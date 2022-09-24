import dropbox_utils
import garmin_utils
import os
import pandas as pd
import tempfile
import csv

# Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
temp_dir = tempfile.TemporaryDirectory(dir=BASE_DIR)

# upload_history_file
garmin_history_filename = "garmin_upload_history.csv"
history_file = {
    "dropbox_path": dropbox_utils.dropbox_app_dir + garmin_history_filename,
    "local_path": os.path.join(temp_dir.name, garmin_history_filename),
}

# Workout on Wahoo
# Wahoo will automatically upload the .FIT file to DropBox per its built-in sync

# When this app runs, it will
# Get all the files from dropbox in the Wahoo folder
# Loop through them and try to upload them to Garmin
# Garmin will deny them if the .FIT already exists
# Garmin changes the name of the .FIT file so I can't do a comparison beforehand

# Would be nice to not try to push all the Wahoo files each time -s
# Ideas
# Set a trigger on new file in DropBox, hope it runs in the one time
# Run every 5 minutes, pushing any files in past 10? (would dupe once)
# Run constantly, marking each file done in a CSV on dropbox


def subset_to_unloaded():

    # Download history file
    dropbox_utils.dropbox_download_file(
        history_file["dropbox_path"], history_file["local_path"]
    )
    # Open the history file
    history_df = pd.read_csv(history_file["local_path"])

    # List all files from Wahoo, remove history file from list
    dropbox_files_df = dropbox_utils.dropbox_list_files(dropbox_utils.dropbox_app_dir)
    history_file_index = dropbox_files_df[
        dropbox_files_df["filename"] == garmin_history_filename
    ].index
    dropbox_files_df.drop(history_file_index, inplace=True)

    # Compare those files to the history file
    # Keep only those non uploaded
    merge_df = pd.merge(
        dropbox_files_df,
        history_df,
        on=["filename", "path_display", "client_modified", "server_modified"],
        how="left",
    )
    non_uploaded_df = merge_df[merge_df["uploaded_to_garmin"].isna()].copy()
    return non_uploaded_df


if __name__ == "__main__":

    non_uploaded_df = subset_to_unloaded()
    print(non_uploaded_df)

    # Add them to Garmin if there's any non-uploaded
    if non_uploaded_df.shape[0] == 0:
        print("No remaining files")
    else:

        # Log in to Garmin
        driver, wait = garmin_utils.garmin_login()

        # Loop through each file
        for index, row in non_uploaded_df.iterrows():
            # Download the file
            local_file_loc = os.path.join(temp_dir.name, row["filename"])
            dropbox_utils.dropbox_download_file(row["path_display"], local_file_loc)

            # Nav to the upload page
            driver.get(garmin_utils.import_page)

            # Submit the file to garmin
            submit_response = garmin_utils.submit_fit_file(wait, local_file_loc)

            # Add the data to the csv
            if submit_response:
                row["uploaded_to_garmin"] = pd.Timestamp.now().isoformat()
                a = row.to_dict()
                # Append to the CSV
                with open(
                    history_file["local_path"], "a", newline="", encoding="utf-8"
                ) as f_object:
                    csv_writer = csv.DictWriter(f_object, fieldnames=list(a.keys()))
                    csv_writer.writerow(a)

        # Close selenium
        driver.quit()

        # if any succesful imports, upload csv back to dropbox
        dropbox_utils.dropbox_upload_file(
            temp_dir.name, garmin_history_filename, history_file["dropbox_path"]
        )

    # Clean up folder
    temp_dir.cleanup()
