from testing import *
from page import *

import settings

from django.test import LiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from sys import argv

if settings.SERVER:
    import pyvirtualdisplay

# populate database
# count results =>
# recount results


class Test(SeleniumTest):
    def test_search(self):
        self.goto("")
        welcome = Welcome(self.browser)
        search = welcome.search(songname1)
        search.playResult(songname1)
        assert self.browser.find_element_by_class("playerSpacer")
