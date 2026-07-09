from selenium import webdriver


class BaseTest:

    def __init__(self):
        self.driver = None

    def setup(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

    def teardown(self):
        if self.driver:
            self.driver.quit()