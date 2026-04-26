from __future__ import annotations

import asyncio
from urllib.parse import quote_plus

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from jarvis_backend.actions.base import ActionExecutor, ActionResult
from jarvis_backend.config import ActionsConfig
from jarvis_backend.state.models import AgentAction


class BrowserActionExecutor(ActionExecutor):
    def __init__(self, config: ActionsConfig) -> None:
        self._config = config

    async def execute(self, action: AgentAction) -> ActionResult:
        if action.action == "open_website":
            return await self._open_website(action)
        if action.action == "google_search":
            return await self._google_search(action)
        if action.action == "youtube_control":
            return await self._youtube_control(action)
        if action.action == "whatsapp_message":
            return await self._whatsapp_message(action)
        return ActionResult(action_id=action.id, ok=False, message=f"Unsupported browser action {action.action}")

    async def _with_driver(self) -> webdriver.Chrome:
        def connect() -> webdriver.Chrome:
            options = Options()
            options.add_experimental_option("debuggerAddress", self._config.browser_debugger_address)
            return webdriver.Chrome(options=options)

        return await asyncio.to_thread(connect)

    async def _open_website(self, action: AgentAction) -> ActionResult:
        if not action.url:
            return ActionResult(action_id=action.id, ok=False, message="Missing url")
        driver = await self._with_driver()
        await asyncio.to_thread(driver.get, str(action.url))
        return ActionResult(action_id=action.id, ok=True, message=f"Opened {action.url}")

    async def _google_search(self, action: AgentAction) -> ActionResult:
        if not action.query:
            return ActionResult(action_id=action.id, ok=False, message="Missing query")
        driver = await self._with_driver()
        url = f"https://www.google.com/search?q={quote_plus(action.query)}"
        await asyncio.to_thread(driver.get, url)
        return ActionResult(action_id=action.id, ok=True, message=f"Searched Google for {action.query}")

    async def _youtube_control(self, action: AgentAction) -> ActionResult:
        if action.youtube_command == "search" and action.query:
            driver = await self._with_driver()
            await asyncio.to_thread(
                driver.get,
                f"https://www.youtube.com/results?search_query={quote_plus(action.query)}",
            )
            return ActionResult(action_id=action.id, ok=True, message=f"Searched YouTube for {action.query}")
        if not action.youtube_command:
            return ActionResult(action_id=action.id, ok=False, message="Missing youtube_command")
        key = " "
        if action.youtube_command == "next":
            key = Keys.SHIFT + "n"
        if action.youtube_command == "previous":
            key = Keys.SHIFT + "p"
        driver = await self._with_driver()
        body = await asyncio.to_thread(driver.find_element, By.TAG_NAME, "body")
        await asyncio.to_thread(body.send_keys, key)
        return ActionResult(action_id=action.id, ok=True, message=f"YouTube {action.youtube_command}")

    async def _whatsapp_message(self, action: AgentAction) -> ActionResult:
        if not action.contact or not action.message:
            return ActionResult(action_id=action.id, ok=False, message="Missing contact or message")
        driver = await self._with_driver()
        await asyncio.to_thread(driver.get, "https://web.whatsapp.com")
        await asyncio.sleep(2)
        search_boxes = await asyncio.to_thread(
            driver.find_elements,
            By.CSS_SELECTOR,
            "div[contenteditable='true'][role='textbox']",
        )
        if not search_boxes:
            return ActionResult(action_id=action.id, ok=False, message="WhatsApp search box not available")
        await asyncio.to_thread(search_boxes[0].send_keys, action.contact)
        await asyncio.sleep(1)
        await asyncio.to_thread(search_boxes[0].send_keys, Keys.ENTER)
        await asyncio.sleep(1)
        boxes = await asyncio.to_thread(
            driver.find_elements,
            By.CSS_SELECTOR,
            "div[contenteditable='true'][role='textbox']",
        )
        if not boxes:
            return ActionResult(action_id=action.id, ok=False, message="WhatsApp message box not available")
        await asyncio.to_thread(boxes[-1].send_keys, action.message)
        await asyncio.to_thread(boxes[-1].send_keys, Keys.ENTER)
        return ActionResult(
            action_id=action.id,
            ok=True,
            message="Sent WhatsApp message after explicit confirmation",
        )
