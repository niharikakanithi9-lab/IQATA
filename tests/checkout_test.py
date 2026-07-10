from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.base_test import BaseTest


class CheckoutTest(BaseTest):

    DEFAULT_URL = "https://www.saucedemo.com/"

    def run_test(self):
        self.setup()

        try:
            wait = WebDriverWait(self.driver, 10)

            target_url = self.url or self.DEFAULT_URL
            self.driver.get(target_url)

            wait.until(
                EC.presence_of_element_located((By.ID, "user-name"))
            ).send_keys("standard_user")

            self.driver.find_element(By.ID, "password").send_keys("secret_sauce")
            self.driver.find_element(By.ID, "login-button").click()

            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "inventory_item"))
            )

            self.driver.find_element(
                By.ID, "add-to-cart-sauce-labs-backpack"
            ).click()

            self.driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()

            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "cart_item"))
            )

            print("PASS: Checkout Test Passed")
            return True

        except Exception as e:
            print("Error:", e)
            self.capture_screenshot("checkout_test")
            raise

        finally:
            self.teardown()


if __name__ == "__main__":
    CheckoutTest().run_test()