from __future__ import annotations

import json
import os
from datetime import datetime
from enum import Enum
from typing import Optional, Type

from bs4 import BeautifulSoup
from langchain_community.tools.playwright.base import BaseBrowserTool
from langchain_community.tools.playwright.utils import (
    get_current_page,
)
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.pydantic_v1 import BaseModel, Field


class AmazonExtractInfo(str, Enum):
    ORDER_DETAILS_INFO = "ORDER_DETAILS_INFO"
    SHOPPING_CART_INFO = "SHOPPING_CART_INFO"


async def extract_shopping_cart_content(page):
    # Get the HTML content of the cart page
    html_content = await page.content()

    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract all item information
    items = soup.select("#activeCartViewForm .sc-list-item")
    cart_items = []

    for item in items:
        title_element = item.select_one(".sc-grid-item-product-title .a-truncate-full")
        title = title_element.get_text(strip=True) if title_element else "N/A"

        price_element = item.select_one(".sc-product-price")
        price = price_element.get_text(strip=True) if price_element else "N/A"

        quantity_element = item.select_one(".sc-action-quantity input")
        quantity = quantity_element.get("value") if quantity_element else "N/A"

        cart_items.append({"title": title, "price": price, "quantity": quantity})

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Construct the file path
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    data_dir = os.path.join(project_root, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    file_path = os.path.join(data_dir, f"cart_items_{timestamp}.json")

    # Save cart information to a JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(cart_items, f, ensure_ascii=False, indent=4)

    return f"Cart information saved to {file_path}"


class ExtractContentToolInput(BaseModel):
    """Input for ExtractContentTool."""

    info: AmazonExtractInfo = Field(
        ...,
        description="Choose which information to extract from",
    )


class ExtractContentTool(BaseBrowserTool):
    """Tool for extracting content from a given web page and storing them in JSON format."""

    name: str = "extract_content"
    description: str = (
        "Extract content from the HTML file and store them in a structured format."
    )
    args_schema: Type[BaseModel] = ExtractContentToolInput

    def _run(
        self,
        info: AmazonExtractInfo,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        raise NotImplementedError("Not implemented")

    async def _arun(
        self,
        info: AmazonExtractInfo,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""
        if self.async_browser is None:
            raise ValueError(f"Asynchronous browser not provided to {self.name}")

        page = get_current_page(self.async_browser)

        if info == AmazonExtractInfo.SHOPPING_CART_INFO:
            return await extract_shopping_cart_content(page)
        else:
            return "Sorry, extracting content is not supported yet."
