from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.base_test import BaseTest


class LoginTest(BaseTest):

    def run_test(self):

        self.setup()

        try:
            wait = WebDriverWait(self.driver, 10)

            self.driver.get("https://the-internet.herokuapp.com/login")

            wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys("tomsmith")

            self.driver.find_element(
                By.ID,
                "password"
            ).send_keys("SuperSecretPassword!" + Keys.RETURN)

            flash = wait.until(
                EC.presence_of_element_located((By.ID, "flash"))
            )

            if "You logged into a secure area!" in flash.text:
                print("✅ Login Test Passed")
                return True

            print("❌ Login Test Failed")
            return False

        except Exception as e:
            print("Error:", e)
            return False

        finally:
            self.teardown()


if __name__ == "__main__":
    LoginTest().run_test()