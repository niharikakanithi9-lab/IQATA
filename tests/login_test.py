from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.base_test import BaseTest


class LoginTest(BaseTest):

    DEFAULT_URL = "https://www.saucedemo.com/"

    def run_test(self):
        self.setup()

        try:
            wait = WebDriverWait(self.driver, 15)

            self.driver.get(self.DEFAULT_URL)

            # Enter username
            username = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "user-name")
                )
            )

            username.send_keys("standard_user")


            # Enter password
            password = self.driver.find_element(
                By.ID,
                "password"
            )

            password.send_keys("secret_sauce")


            # Click login
            self.driver.find_element(
                By.ID,
                "login-button"
            ).click()


            # Verify successful login
            wait.until(
                EC.url_contains("inventory")
            )


            if "inventory" in self.driver.current_url:
                print("PASS: Login Test Passed")
                return True


            print("FAIL: Login Test Failed")
            self.capture_screenshot("login_test")
            return False


        except Exception as e:
            print("Error:", e)
            self.capture_screenshot("login_test")
            raise


        finally:
            self.teardown()


if __name__ == "__main__":
    LoginTest().run_test()