import asyncio
import os
import traceback
import unittest
import nest_asyncio

from amazoncaptcha import AmazonCaptcha
from langchain_community.tools.playwright.utils import (
    create_async_playwright_browser,
)
from playwright_stealth import stealth_async

from utils.env_util import EnvLoader

nest_asyncio.apply()

async def async_solve_captcha(page):
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


class TestAmazonWebPageLogin(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """
        This method is called before each test method.
        """
        print("setUp: Preparing the test environment.")
        EnvLoader()
        self.amazon_email = os.getenv("AMAZON_EMAIL")
        self.amazon_password = os.getenv("AMAZON_PASSWORD")

    async def test_login(self):
        try:
            # Launch the browser
            browser = create_async_playwright_browser(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Apply stealth to avoid detection
            await stealth_async(page)

            # Open Amazon web page
            await page.goto("https://www.amazon.com")

            # Check if captcha is present
            if await page.is_visible('img[src*="captcha"]'):
                print("Solving the captcha...")
                await async_solve_captcha(page)
                print("Done")

            # Open the login page
            await page.click("a#nav-link-accountList")

            # Continue with the login process
            await page.fill("input[name='email']", self.amazon_email)
            await page.click("input[id='continue']")
            await page.fill("input[name='password']", self.amazon_password)
            await page.click("input[id='signInSubmit']")

            await asyncio.sleep(10)

            # Close the browser
            await browser.close()

            print("Success!")
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())


if __name__ == "__main__":
    unittest.main()