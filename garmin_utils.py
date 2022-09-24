from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os
import keyring

user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36"

chrome_options = Options()
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(f"user-agent={user_agent}")

# Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

activity_page = "https://connect.garmin.com/modern/activities"
import_page = "https://connect.garmin.com/modern/import-data"
garmin_username = "mike10@stny.rr.com"
garmin_password = keyring.get_password("garmin", garmin_username)

##### Dropping files in
# https://gist.github.com/florentbr/349b1ab024ca9f3de56e6bf8af2ac69e

JS_DROP_FILE = """
    var target = arguments[0],
        offsetX = arguments[1],
        offsetY = arguments[2],
        document = target.ownerDocument || document,
        window = document.defaultView || window;

    var input = document.createElement('INPUT');
    input.type = 'file';
    input.onchange = function () {
      var rect = target.getBoundingClientRect(),
          x = rect.left + (offsetX || (rect.width >> 1)),
          y = rect.top + (offsetY || (rect.height >> 1)),
          dataTransfer = { files: this.files };

      ['dragenter', 'dragover', 'drop'].forEach(function (name) {
        var evt = document.createEvent('MouseEvent');
        evt.initMouseEvent(name, !0, !0, window, 0, 0, 0, x, y, !1, !1, !1, !1, 0, null);
        evt.dataTransfer = dataTransfer;
        target.dispatchEvent(evt);
      });

      setTimeout(function () { document.body.removeChild(input); }, 25);
    };
    document.body.appendChild(input);
    return input;
"""


def drag_and_drop_file(drop_target, path):
    driver = drop_target.parent
    file_input = driver.execute_script(JS_DROP_FILE, drop_target, 0, 0)
    file_input.send_keys(path)


def garmin_login(garmin_username=garmin_username, garmin_password=garmin_password):

    print("----- starting login -----")

    # Start new chromedriver
    driver = webdriver.Chrome(
        os.path.join(BASE_DIR, "chromedriver"), options=chrome_options
    )

    # Nav to garmin page
    driver.get(activity_page)

    # Login
    wait = WebDriverWait(driver, 20)
    wait.until(
        EC.frame_to_be_available_and_switch_to_it(
            (By.XPATH, "//iframe[@id='gauth-widget-frame-gauth-widget']")
        )
    )  # switching frame
    wait.until(EC.visibility_of_element_located((By.ID, "username"))).send_keys(
        garmin_username
    )  # userame/email
    wait.until(EC.visibility_of_element_located((By.ID, "password"))).send_keys(
        garmin_password
    )  # password
    wait.until(EC.element_to_be_clickable((By.ID, "login-btn-signin"))).click()

    print("----- logged in -----")

    return driver, wait


def submit_fit_file(wait, file):

    try:

        print("----- starting file upload -----")

        # Find the submission area
        form_box = wait.until(
            EC.visibility_of_element_located((By.XPATH, "//*[@id='import-data']/h2"))
        )
        # find the target for the drop
        file_input = form_box.parent.execute_script(JS_DROP_FILE, form_box, 0, 0)
        # Drop the file
        file_input.send_keys(file)
        # Click submit button
        wait.until(EC.element_to_be_clickable((By.ID, "import-data-start"))).click()
        # Get the submission message
        # It's so wonky I give up
        print("----- file uploaded -----")
        submit_response = True

    except Exception as e:
        print(e)
        submit_response = False

    return submit_response


if __name__ == "__main__":
    print("here")

