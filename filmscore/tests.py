from django.test import LiveServerTestCase, TestCase
from django.conf import settings
from django.test.utils import override_settings
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from .models import Account, Review, Film, SavedFilm
import time

class SaveFilmToListTestCase(LiveServerTestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        Account.objects.create_user(username=self.username, password=self.password)

    def test_save_film_to_list(self):
        browser = webdriver.Chrome(executable_path="chromedriver.exe")
        browser.get(self.live_server_url)

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Log In')]")
        button.click()

        time.sleep(1)

        username = browser.find_element_by_id("id_username")
        username.send_keys(self.username)

        time.sleep(1)

        password = browser.find_element_by_id("id_password")
        password.send_keys(self.password)

        time.sleep(1)

        password.send_keys(Keys.ENTER)

        time.sleep(5)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Films')]")
        button.click()

        time.sleep(1)

        textbox = browser.find_element_by_id("film")
        textbox.send_keys("The Matrix")

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Search')]")
        button.click()

        time.sleep(20)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Add to saved films')]")
        button.click()

        time.sleep(1)

        assert "Remove from saved films" in browser.page_source



class SearchFilmTestCase(LiveServerTestCase):       

    def test_search_for_film(self):
        
        browser = webdriver.Chrome(executable_path="chromedriver.exe")
        browser.get(self.live_server_url)

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Films')]")
        button.click()

        time.sleep(1)

        textbox = browser.find_element_by_id("film")
        textbox.send_keys("The Matrix")

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Search')]")
        button.click()

        time.sleep(20)

        assert "The Matrix" in browser.page_source

        browser.close()

class SaveFilmToListTestCase(LiveServerTestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        Account.objects.create_user(username=self.username, password=self.password)

    def test_save_film_to_list(self):
        browser = webdriver.Chrome(executable_path="chromedriver.exe")
        browser.get(self.live_server_url)

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Log In')]")
        button.click()

        time.sleep(1)

        username = browser.find_element_by_id("id_username")
        username.send_keys(self.username)

        time.sleep(1)

        password = browser.find_element_by_id("id_password")
        password.send_keys(self.password)

        time.sleep(1)

        password.send_keys(Keys.ENTER)

        time.sleep(5)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Films')]")
        button.click()

        time.sleep(1)

        textbox = browser.find_element_by_id("film")
        textbox.send_keys("The Matrix")

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Search')]")
        button.click()

        time.sleep(20)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Add to saved films')]")
        button.click()

        time.sleep(5)

        assert "Remove from saved films" in browser.page_source



class SearchFilmTestCase(LiveServerTestCase):       

    def test_search_for_film(self):
        
        browser = webdriver.Chrome(executable_path="chromedriver.exe")
        browser.get(self.live_server_url)

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Films')]")
        button.click()

        time.sleep(1)

        textbox = browser.find_element_by_id("film")
        textbox.send_keys("The Matrix")

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Search')]")
        button.click()

        time.sleep(20)

        assert "The Matrix" in browser.page_source

        browser.close()

class LoginTestCase(LiveServerTestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        Account.objects.create_user(username=self.username, password=self.password)

    def test_log_in(self):
        browser = webdriver.Chrome(executable_path="chromedriver.exe")
        browser.get(self.live_server_url)

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Log In')]")
        button.click()

        time.sleep(1)

        username = browser.find_element_by_id("id_username")
        username.send_keys(self.username)

        time.sleep(1)

        password = browser.find_element_by_id("id_password")
        password.send_keys(self.password)

        time.sleep(1)

        password.send_keys(Keys.ENTER)

        time.sleep(5)

        assert "View Profile" in browser.page_source

class CreateAccountTestCase(LiveServerTestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        self.email = "test@test.com"
        self.firstname = "test"
        self.lastname = "user"

    def test_create_account(self):   
        browser = webdriver.Chrome(executable_path="chromedriver.exe")
        browser.get(self.live_server_url)

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Log In')]")
        button.click()

        time.sleep(1)

        button = browser.find_element_by_xpath("//*[contains(text(), 'Sign Up')]")
        button.click()

        time.sleep(1)

        username = browser.find_element_by_id("id_username")
        username.send_keys(self.username)

        time.sleep(1)

        email = browser.find_element_by_id("id_email")
        email.send_keys(self.email)

        time.sleep(1)

        firstname = browser.find_element_by_id("id_firstName")
        firstname.send_keys(self.firstname)

        time.sleep(1)

        lastname = browser.find_element_by_id("id_lastName")
        lastname.send_keys(self.lastname)

        time.sleep(1)

        password = browser.find_element_by_id("id_password1")
        password.send_keys(self.password)

        time.sleep(1)

        password = browser.find_element_by_id("id_password2")
        password.send_keys(self.password)

        time.sleep(1)

        password.send_keys(Keys.ENTER)

        time.sleep(5)

        assert "View Profile" in browser.page_source