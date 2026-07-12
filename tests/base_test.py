import os
import os
import time

from selenium import webdriver


class BaseTest:

    def __init__(self, url=None, browser="Chrome", environment="Development"):

        self.url = url
        self.browser = browser
        self.environment = environment
        self.driver = None
        self.screenshot_path = None


    def setup(self):

        browser_name = (self.browser or "Chrome").lower()


        if browser_name == "firefox":

            self.driver = webdriver.Firefox()


        elif browser_name == "edge":

            self.driver = webdriver.Edge()


        else:

            # Azure Linux App Service does not have GUI Chrome.
            # Run Chromium in headless mode.

            from selenium.webdriver.chrome.options import Options

            options = Options()

            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")


            self.driver = webdriver.Chrome(
                options=options
            )


        self.driver.maximize_window()



    def capture_screenshot(self, name):

        if self.driver is None:
            return None


        os.makedirs("screenshots", exist_ok=True)

        safe_name = name.lower().replace(" ", "_")

        path = (
            f"screenshots/"
            f"{safe_name}_{int(time.time())}.png"
        )


        try:

            self.driver.save_screenshot(path)

            self.screenshot_path = path

            return path


        except Exception:

            return None



    def teardown(self):

        if self.driver:

            self.driver.quit()
