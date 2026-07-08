from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.base_test import BaseTest


class CheckoutTest(BaseTest):

    def run_test(self):

        self.setup()

        try:
            wait = WebDriverWait(self.driver, 10)

            self.driver.get("https://www.saucedemo.com/")

            # Login
            wait.until(
                EC.presence_of_element_located((By.ID, "user-name"))
            ).send_keys("standard_user")

            self.driver.find_element(By.ID, "password").send_keys("secret_sauce")
            self.driver.find_element(By.ID, "login-button").click()

            # Wait for inventory page
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "inventory_item"))
            )

            # Add first product
            self.driver.find_element(
                By.ID,
                "add-to-cart-sauce-labs-backpack"
            ).click()

            # Open cart
            self.driver.find_element(
                By.CLASS_NAME,
                "shopping_cart_link"
            ).click()

            # Verify cart page
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "cart_item"))
            )

            print("✅ Checkout Test Passed")
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.teardown()


if __name__ == "__main__":
    CheckoutTest().run_test()