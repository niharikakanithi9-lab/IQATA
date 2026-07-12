from selenium.webdriver.common.by import By
from tests.base_test import BaseTest, get_site_credentials, get_site_profile


class SearchTest(BaseTest):

    DEFAULT_URL = "https://www.saucedemo.com/"

    def run_test(self):
        self.setup()

        try:
            target_url = self.url or self.DEFAULT_URL
            self.driver.get(target_url)

            username, password = get_site_credentials(target_url)
            logged_in = self.profile_login(username, password)

            if not logged_in:
                print("FAIL: Search Test Failed (login rejected — check credentials for this site)")
                self.capture_screenshot("search_test")
                return False

            profile = get_site_profile(self.driver.current_url)
            product_selector = profile["product_card"] if profile else "inventory_item"
            by = By.CSS_SELECTOR if profile else By.CLASS_NAME
            products = self.driver.find_elements(by, product_selector)

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