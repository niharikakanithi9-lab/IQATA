# base_test.py
import os
import time

from selenium import webdriver


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