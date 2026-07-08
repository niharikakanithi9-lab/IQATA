from selenium.webdriver.common.by import By
from tests.base_test import BaseTest


class SearchTest(BaseTest):

    def run_test(self):

        self.setup()

        try:
            self.driver.get("https://www.saucedemo.com/")

            # Login
            self.driver.find_element(By.ID, "user-name").send_keys("standard_user")
            self.driver.find_element(By.ID, "password").send_keys("secret_sauce")
            self.driver.find_element(By.ID, "login-button").click()

            # Check whether product page loaded
            products = self.driver.find_elements(By.CLASS_NAME, "inventory_item")

            if len(products) > 0:
                print(f"✅ Search Test Passed ({len(products)} products found)")
                return True

            print("❌ Search Test Failed")
            return False

        except Exception as e:
            print("Error:", e)
            return False

        finally:
            self.teardown()


if __name__ == "__main__":
    SearchTest().run_test()