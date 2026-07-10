from selenium.webdriver.common.by import By
from tests.base_test import BaseTest


class SearchTest(BaseTest):

    DEFAULT_URL = "https://www.saucedemo.com/"

    def run_test(self):
        self.setup()

        try:
            target_url = self.url or self.DEFAULT_URL
            self.driver.get(target_url)

            self.driver.find_element(By.ID, "user-name").send_keys("standard_user")
            self.driver.find_element(By.ID, "password").send_keys("secret_sauce")
            self.driver.find_element(By.ID, "login-button").click()

            products = self.driver.find_elements(By.CLASS_NAME, "inventory_item")

            if len(products) > 0:
                print(f"PASS: Search Test Passed ({len(products)} products found)")
                return True

            print("FAIL: Search Test Failed")
            self.capture_screenshot("search_test")
            return False

        except Exception as e:
            print("Error:", e)
            self.capture_screenshot("search_test")
            raise

        finally:
            self.teardown()


if __name__ == "__main__":
    SearchTest().run_test()