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
            self.driver = webdriver.Edge()
        else:
            self.driver = webdriver.Chrome()

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