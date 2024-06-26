import os
import time
import traceback
import unittest

from amazoncaptcha import AmazonCaptcha
from langchain_community.tools.playwright.utils import create_sync_playwright_browser, create_async_playwright_browser
from playwright_stealth import stealth_sync

from utils.env_util import EnvLoader


def solve_captcha(page):
    """
    Solve the captcha by extracting the captcha image URL,
    using AmazonCaptcha library to solve it, and submitting the solution.
    """
    # Get the captcha image URL
    captcha_url = page.get_attribute('img[src*="captcha"]', "src")
    print(f"Captcha URL: {captcha_url}")

    # Solve the captcha using AmazonCaptcha library
    captcha = AmazonCaptcha.fromlink(captcha_url)
    solution = captcha.solve()
    print(f"Captcha Solution: {solution}")

    # Fill the captcha solution and submit the form
    page.fill('input[name="field-keywords"]', solution)
    page.click('span.a-button-inner > button[type="submit"]')


async def asolve_captcha(page):
    """
    Solve the captcha by extracting the captcha image URL,
    using AmazonCaptcha library to solve it, and submitting the solution.
    """
    # Get the captcha image URL
    captcha_url = await page.get_attribute('img[src*="captcha"]', "src")
    print(f"Captcha URL: {captcha_url}")

    # Solve the captcha using AmazonCaptcha library
    captcha = AmazonCaptcha.fromlink(captcha_url)
    solution = captcha.solve()
    print(f"Captcha Solution: {solution}")

    # Fill the captcha solution and submit the form
    await page.fill('input[name="field-keywords"]', solution)
    await page.click('span.a-button-inner > button[type="submit"]')

class TestAmazonWebPageLogin(unittest.TestCase):

    def setUp(self):
        """
        This method is called before each test method.
        """
        print("setUp: Preparing the test environment.")
        EnvLoader()
        self.amazon_email = os.getenv("AMAZON_EMAIL")
        self.amazon_password = os.getenv("AMAZON_PASSWORD")

    def test_login(self):
        try:
            # Launch the browser
            browser = create_sync_playwright_browser(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Apply stealth to avoid detection
            stealth_sync(page)

            # Open Amazon web page
            page.goto(
                "https://www.amazon.com"
            )

            # Check if captcha is present
            if page.is_visible('img[src*="captcha"]'):
                print("Solving the captcha...")
                solve_captcha(page)
                print("Done")

            # Open the login page
            page.click('a#nav-link-accountList')

            # Continue with the login process
            page.fill("input[name='email']", self.amazon_email)
            page.click("input[id='continue']")
            page.fill("input[name='password']", self.amazon_password)
            page.click("input[id='signInSubmit']")

            time.sleep(10)

            # Close the browser
            browser.close()

            print("Success!")
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())



if __name__ == "__main__":
    unittest.main()
