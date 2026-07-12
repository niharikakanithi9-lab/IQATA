from tests.base_test import BaseTest, get_site_credentials


class CheckoutTest(BaseTest):

    DEFAULT_URL = "https://www.saucedemo.com/"

    def run_test(self):
        self.setup()

        try:
            target_url = self.url or self.DEFAULT_URL
            self.driver.get(target_url)

            username, password = get_site_credentials(target_url)

            if not self.profile_login(username, password):
                print("FAIL: Checkout Test Failed (login rejected — check credentials for this site)")
                self.capture_screenshot("checkout_test")
                return False

            if not self.profile_add_first_product_to_cart():
                print("FAIL: Checkout Test Failed (could not add product to cart)")
                self.capture_screenshot("checkout_test")
                return False

            if not self.profile_go_to_cart_and_verify():
                print("FAIL: Checkout Test Failed (cart did not show item)")
                self.capture_screenshot("checkout_test")
                return False

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