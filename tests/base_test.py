import os
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# Real credentials per site. saucedemo's are the official demo login.
# demoblaze/automationexercise need an account that actually exists on
# that site — if you haven't registered kax@gmail.com / kaxkax on those
# sites, login will legitimately fail (wrong password), which is a true
# result, not a bug. Register test accounts there if you want real PASS
# results on login specifically.
SITE_CREDENTIALS = {
    "saucedemo.com": ("standard_user", "secret_sauce"),
    "demoblaze.com": ("kaxkax", "kaxgood"),
    "automationexercise.com": ("kax@gmail.com", "kaxgood"),
}


def get_site_credentials(url, default=("standard_user", "secret_sauce")):
    host = urlparse(url).netloc.replace("www.", "")
    for domain, creds in SITE_CREDENTIALS.items():
        if domain in host:
            return creds
    return default


SITE_PROFILES = {
    "saucedemo.com": {
        "login_link": None,  # form is already on landing page
        "username": "#user-name",
        "password": "#password",
        "login_btn": "#login-button",
        "product_card": ".inventory_item",
        "add_to_cart_in_card": "button[data-test^='add-to-cart']",
        "cart_link": ".shopping_cart_link",
        "cart_item": ".cart_item",
    },
    "demoblaze.com": {
        "login_link": "#login2",  # opens a modal — must click first
        "username": "#loginusername",
        "password": "#loginpassword",
        "login_btn": "button[onclick='logIn()']",
        "product_card": ".card",
        "product_link_in_card": "a.hrefch",  # card itself has no add-to-cart button;
                                              # must click into the product page first
        "add_to_cart_in_card": "a[onclick^='addToCart']",
        "cart_link": "a#cartur, a[onclick^='showcart' i], a[onclick^='showCart' i]",
        "cart_item": "#tbodyid tr",
    },
    "automationexercise.com": {
        "login_link": "a[href='/login']",
        "username": "input[data-qa='login-email']",
        "password": "input[data-qa='login-password']",
        "login_btn": "button[data-qa='login-button']",
        "product_card": ".single-products",
        "add_to_cart_in_card": "a.add-to-cart",
        "cart_link": "a[href='/view_cart']",
        "cart_item": "#cart_info_table tbody tr",
    },
}


def get_site_profile(url):
    """
    Module-level helper (NOT a method — lives outside the class,
    same as SITE_PROFILES above it). Matches the current page's
    hostname against SITE_PROFILES and returns the matching dict,
    or None if the site has no profile.
    """
    host = urlparse(url).netloc.replace("www.", "")
    for domain, profile in SITE_PROFILES.items():
        if domain in host:
            return profile
    return None


class BaseTest:

    def __init__(self, url=None, browser="Chrome", environment="Development"):
        # These now actually get used by setup() and run_test() in subclasses,
        # instead of being accepted and ignored.
        self.url = url
        self.browser = browser
        self.environment = environment
        self.driver = None
        self.screenshot_path = None  # runner.py reads this instead of touching
                                      # self.driver after teardown has quit it

    def setup(self):
        browser_name = (self.browser or "Chrome").lower()

        if browser_name == "firefox":
            self.driver = webdriver.Firefox()
        elif browser_name == "edge":
            from selenium.webdriver.edge.options import Options as EdgeOptions
            options = EdgeOptions()
            options.add_experimental_option("prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            })
            options.add_argument("--disable-features=PasswordLeakDetection,PasswordChangeDetection")
            self.driver = webdriver.Edge(options=options)
        else:
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            options = ChromeOptions()
            options.add_experimental_option("prefs", {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.password_manager_leak_detection": False,
            })
            options.add_argument("--disable-features=PasswordLeakDetection,PasswordChangeDetection")
            self.driver = webdriver.Chrome(options=options)

        self.driver.maximize_window()

    def generic_login(self, username, password, wait_seconds=10):
        """
        Fallback for sites with no SITE_PROFILES entry. Uses semantic
        selectors instead of site-specific IDs. Only works if a login
        form is already visible on the current page (no navigation).
        """
        wait = WebDriverWait(self.driver, wait_seconds)

        try:
            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[type='email'], input[type='text'][name*='user' i], "
                    "input[autocomplete='username'], #user-name"))
            )
            username_field.send_keys(username)

            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.send_keys(password)

            submit_btn = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], input[type='submit'], #login-button")
            submit_btn.click()

            return True
        except Exception as e:
            print(f"generic_login failed: {e}")
            return False

    def profile_login(self, username, password, wait_seconds=10):
        """
        Uses SITE_PROFILES for the current domain if one exists.
        Falls back to generic_login if the site has no profile.
        """
        profile = get_site_profile(self.driver.current_url)
        if not profile:
            return self.generic_login(username, password, wait_seconds)

        wait = WebDriverWait(self.driver, wait_seconds)
        try:
            if profile["login_link"]:
                self.driver.find_element(By.CSS_SELECTOR, profile["login_link"]).click()

            user_field = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, profile["username"]))
            )
            user_field.send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, profile["password"]).send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, profile["login_btn"]).click()

            # Some sites (demoblaze) fire a native JS alert() on bad
            # credentials instead of an inline error message. If we don't
            # handle it, every subsequent find_element() call throws
            # UnexpectedAlertPresentException and the whole test dies
            # with a confusing stacktrace instead of a clean FAIL.
            try:
                WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                alert = self.driver.switch_to.alert
                alert_text = alert.text
                alert.accept()
                print(f"profile_login: site rejected credentials — alert said: {alert_text}")
                return False
            except TimeoutException:
                pass  # no alert appeared, login click went through normally

            return True
        except Exception as e:
            print(f"profile_login failed: {e}")
            return False

    def profile_add_first_product_to_cart(self, wait_seconds=10):
        profile = get_site_profile(self.driver.current_url)
        if not profile:
            return False
        try:
            card = WebDriverWait(self.driver, wait_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, profile["product_card"]))
            )

            if profile.get("product_link_in_card"):
                # This site's card is just a link to a separate product
                # page — the real add-to-cart button lives there, not
                # on the card itself. Navigate in first.
                link = card.find_element(By.CSS_SELECTOR, profile["product_link_in_card"])
                self.driver.execute_script("arguments[0].click();", link)
                btn = WebDriverWait(self.driver, wait_seconds).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, profile["add_to_cart_in_card"]))
                )
            else:
                btn = card.find_element(By.CSS_SELECTOR, profile["add_to_cart_in_card"])

            self.driver.execute_script("arguments[0].click();", btn)

            # Some sites (demoblaze) confirm the add with a native
            # alert() instead of an inline message. Same issue as
            # login — an unhandled alert breaks every call after it.
            try:
                WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                alert = self.driver.switch_to.alert
                alert.accept()
            except TimeoutException:
                pass  # no alert on this site, that's fine

            return True
        except Exception as e:
            print(f"profile_add_first_product_to_cart failed: {e}")
            return False

    def profile_go_to_cart_and_verify(self, wait_seconds=10):
        profile = get_site_profile(self.driver.current_url)
        if not profile:
            return False
        try:
            cart_link = WebDriverWait(self.driver, wait_seconds).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, profile["cart_link"]))
            )
            self.driver.execute_script("arguments[0].click();", cart_link)
            WebDriverWait(self.driver, wait_seconds).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, profile["cart_item"]))
            )
            return True
        except Exception as e:
            print(f"profile_go_to_cart_and_verify failed: {e}")
            return False

    def capture_screenshot(self, name):
        """
        Call this from inside run_test(), BEFORE teardown() quits the driver.
        Sets self.screenshot_path so runner.py can read it after the fact
        without touching a dead driver session.
        """
        if self.driver is None:
            return None
        os.makedirs("screenshots", exist_ok=True)
        safe_name = name.lower().replace(" ", "_")
        path = f"screenshots/{safe_name}_{int(time.time())}.png"
        try:
            self.driver.save_screenshot(path)
            self.screenshot_path = path
            return path
        except Exception:
            return None

    def teardown(self):
        if self.driver:
            self.driver.quit()