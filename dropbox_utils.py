import os
import pathlib
import pandas as pd
import keyring
import dropbox
from dropbox.exceptions import AuthError

# Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dropbox_home = "https://www.dropbox.com/home/"
dropbox_app = "MAD_WahooToGarmin"
dropbox_app_dir = "/Apps/WahooFitness/"
DROPBOX_ACCESS_TOKEN = keyring.get_password("dropbox", dropbox_app)

# https://practicaldatascience.co.uk/data-science/how-to-use-the-dropbox-api-with-python


def dropbox_connect():
    """Create a connection to Dropbox."""

    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    except AuthError as e:
        print("Error connecting to Dropbox with access token: " + str(e))
    return dbx


def dropbox_list_files(path):
    """Return a Pandas dataframe of files in a given Dropbox folder path in the Apps directory.
    """

    dbx = dropbox_connect()

    try:
        files = dbx.files_list_folder(path).entries
        files_list = []
        for file in files:
            if isinstance(file, dropbox.files.FileMetadata):
                metadata = {
                    "filename": file.name,
                    "path_display": file.path_display,
                    "client_modified": pd.Timestamp(file.client_modified).isoformat(),
                    "server_modified": pd.Timestamp(file.server_modified).isoformat(),
                }
                files_list.append(metadata)

        df = pd.DataFrame.from_records(files_list)
        return df.sort_values(by="server_modified", ascending=False)

    except Exception as e:
        print("Error getting list of files from Dropbox: " + str(e))


def dropbox_download_file(dropbox_file_path, local_file_path):
    """Download a file from Dropbox to the local machine."""

    try:
        dbx = dropbox_connect()

        with open(local_file_path, "wb") as f:
            metadata, result = dbx.files_download(path=dropbox_file_path)
            f.write(result.content)
    except Exception as e:
        print("Error downloading file from Dropbox: " + str(e))


def dropbox_upload_file(local_path, local_file, dropbox_file_path):
    """Upload a file from the local machine to a path in the Dropbox app directory.

    Args:
        local_path (str): The path to the local file.
        local_file (str): The name of the local file.
        dropbox_file_path (str): The path to the file in the Dropbox app directory.

    Example:
        dropbox_upload_file('.', 'test.csv', '/stuff/test.csv')

    Returns:
        meta: The Dropbox file metadata.
    """

    try:
        dbx = dropbox_connect()

        local_file_path = pathlib.Path(local_path) / local_file

        with local_file_path.open("rb") as f:
            meta = dbx.files_upload(
                f.read(), dropbox_file_path, mode=dropbox.files.WriteMode("overwrite")
            )

            return meta
    except Exception as e:
        print("Error uploading file to Dropbox: " + str(e))


if __name__ == "__main__":
    print("here")
