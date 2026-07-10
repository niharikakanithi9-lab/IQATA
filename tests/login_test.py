from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.base_test import BaseTest


class LoginTest(BaseTest):

    DEFAULT_URL = "https://the-internet.herokuapp.com/login"

    def run_test(self):
        self.setup()

        try:
            wait = WebDriverWait(self.driver, 10)

            # LoginTest's selectors (#username, #password, #flash) are
            # hardcoded to this specific demo site. Unlike Search/Checkout
            # (which at least share saucedemo's structure with each other),
            # Login has no compatible custom-URL story at all — accepting
            # self.url here would just guarantee a timeout against any other
            # site. So this always uses its own fixed target, ignoring
            # whatever was typed into the dashboard's Website URL field.
            self.driver.get(self.DEFAULT_URL)

            wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys("tomsmith")

            self.driver.find_element(
                By.ID, "password"
            ).send_keys("SuperSecretPassword!" + Keys.RETURN)

            flash = wait.until(
                EC.presence_of_element_located((By.ID, "flash"))
            )

            if "You logged into a secure area!" in flash.text:
                print("PASS: Login Test Passed")
                return True

            print("FAIL: Login Test Failed")
            self.capture_screenshot("login_test")
            return False

        except Exception as e:
            print("Error:", e)
            self.capture_screenshot("login_test")
            raise  # let runner.py record the real exception as failure_reason

        finally:
            self.teardown()


if __name__ == "__main__":
    LoginTest().run_test()