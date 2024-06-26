import asyncio
import json
import os
import traceback
import unittest
from datetime import datetime

import nest_asyncio

from amazoncaptcha import AmazonCaptcha
from bs4 import BeautifulSoup
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

            # Open cart page
            await page.click("a#nav-cart")

            # Wait for the cart page to load
            await page.wait_for_selector("#activeCartViewForm")

            # Get the HTML content of the cart page
            html_content = await page.content()

            # Parse HTML using BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract all item information
            items = soup.select("#activeCartViewForm .sc-list-item")
            cart_items = []

            for item in items:
                title_element = item.select_one(".sc-grid-item-product-title .a-truncate-full")
                title = title_element.get_text(strip=True) if title_element else "N/A"

                price_element = item.select_one(".sc-product-price")
                price = price_element.get_text(strip=True) if price_element else "N/A"

                quantity_element = item.select_one(".sc-action-quantity input")
                quantity = quantity_element.get('value') if quantity_element else "N/A"

                cart_items.append({
                    "title": title,
                    "price": price,
                    "quantity": quantity
                })

            # Get the current timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            # Construct the file path
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            data_dir = os.path.join(project_root, 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            file_path = os.path.join(data_dir, f"cart_items_{timestamp}.json")

            # Save cart information to a JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cart_items, f, ensure_ascii=False, indent=4)

            print(f"Cart information saved to {file_path}")

            await browser.close()

            print("Success!")
        except Exception as e:
            print(f"An error occurred: {e}")
            print(traceback.format_exc())


if __name__ == "__main__":
    unittest.main()