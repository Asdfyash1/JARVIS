from __future__ import annotations

import asyncio
import json
import re
from collections.abc import Sequence
from urllib.error import URLError
from urllib.parse import quote, quote_plus
from urllib.request import Request, urlopen

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from jarvis_backend.actions.base import ActionExecutor, ActionResult
from jarvis_backend.config import ActionsConfig
from jarvis_backend.state.models import AgentAction


class BrowserActionExecutor(ActionExecutor):
    def __init__(self, config: ActionsConfig) -> None:
        self._config = config

    @property
    def _debugger_addresses(self) -> list[str]:
        addresses = [
            *self._config.browser_debugger_addresses,
            self._config.browser_debugger_address,
            self._config.edge_debugger_address,
        ]
        return list(dict.fromkeys(address for address in addresses if address))

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
            last_error: Exception | None = None
            for address in self._debugger_addresses:
                options = Options()
                options.add_experimental_option("debuggerAddress", address)
                try:
                    return webdriver.Chrome(options=options)
                except WebDriverException as exc:
                    last_error = exc
            if last_error:
                raise last_error
            raise RuntimeError("No browser debugger address configured")

        return await asyncio.to_thread(connect)

    async def _open_url(self, url: str) -> None:
        try:
            await asyncio.to_thread(self._open_url_with_cdp, url)
            return
        except RuntimeError:
            driver = await self._with_driver()
            await asyncio.to_thread(driver.get, url)

    def _open_url_with_cdp(self, url: str) -> None:
        last_error: Exception | None = None
        for address in self._debugger_addresses:
            base_url = f"http://{address}"
            request = Request(f"{base_url}/json/new?{quote(url, safe=':/?=&%')}", method="PUT")
            try:
                with urlopen(request, timeout=10) as response:
                    json.load(response)
                return
            except (OSError, URLError) as exc:
                last_error = exc
        if last_error:
            raise RuntimeError(f"No Chrome/Edge debugger accepted {url}: {last_error}") from last_error
        raise RuntimeError("No browser debugger address configured")

    async def _open_website(self, action: AgentAction) -> ActionResult:
        if not action.url:
            return ActionResult(action_id=action.id, ok=False, message="Missing url")
        await self._open_url(str(action.url))
        return ActionResult(action_id=action.id, ok=True, message=f"Opened {action.url}")

    async def _google_search(self, action: AgentAction) -> ActionResult:
        if not action.query:
            return ActionResult(action_id=action.id, ok=False, message="Missing query")
        url = f"https://www.google.com/search?q={quote_plus(action.query)}"
        await self._open_url(url)
        return ActionResult(action_id=action.id, ok=True, message=f"Searched Google for {action.query}")

    async def _youtube_control(self, action: AgentAction) -> ActionResult:
        if action.youtube_command == "search" and action.query:
            await self._open_url(f"https://www.youtube.com/results?search_query={quote_plus(action.query)}")
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
        if not action.message:
            return ActionResult(action_id=action.id, ok=False, message="Missing message")
        if action.phone_number:
            return await self._whatsapp_phone_message(action)
        driver = await self._with_driver()
        if not action.contact:
            return await self._whatsapp_current_chat_message(action, driver)
        await asyncio.to_thread(driver.get, "https://web.whatsapp.com")
        await asyncio.sleep(2)
        matches = await self._search_whatsapp_contact(driver, action.contact)
        if self._ambiguous_whatsapp_matches(matches):
            options = ", ".join(matches[:5])
            return ActionResult(
                action_id=action.id,
                ok=False,
                message=f"I found multiple WhatsApp matches for {action.contact}: {options}. Which one should I message?",
                data={"matches": matches[:5], "needs_clarification": True},
            )
        await asyncio.sleep(1)
        boxes = await self._whatsapp_text_boxes(driver)
        if not boxes:
            return ActionResult(action_id=action.id, ok=False, message="WhatsApp message box not available")
        await asyncio.to_thread(boxes[-1].send_keys, action.message)
        await asyncio.to_thread(boxes[-1].send_keys, Keys.ENTER)
        return ActionResult(
            action_id=action.id,
            ok=True,
            message="Sent WhatsApp message after explicit confirmation",
        )

    async def _search_whatsapp_contact(self, driver: webdriver.Chrome, contact: str) -> list[str]:
        search_boxes = await asyncio.to_thread(
            driver.find_elements,
            By.CSS_SELECTOR,
            "div[contenteditable='true'][role='textbox'], input[aria-label='Search or start a new chat']",
        )
        if search_boxes:
            await asyncio.to_thread(search_boxes[0].send_keys, Keys.CONTROL + "a")
            await asyncio.to_thread(search_boxes[0].send_keys, contact)
        else:
            await asyncio.to_thread(driver.switch_to.active_element.send_keys, Keys.CONTROL + "a")
            await asyncio.to_thread(driver.switch_to.active_element.send_keys, contact)
        await asyncio.sleep(2)
        matches = await asyncio.to_thread(self._whatsapp_visible_matches, driver, contact)
        if len(matches) > 1:
            return matches
        target = search_boxes[0] if search_boxes else driver.switch_to.active_element
        await asyncio.to_thread(target.send_keys, Keys.ENTER)
        return matches

    async def _whatsapp_current_chat_message(self, action: AgentAction, driver: webdriver.Chrome) -> ActionResult:
        if "web.whatsapp.com" not in driver.current_url:
            await asyncio.to_thread(driver.get, "https://web.whatsapp.com")
            return ActionResult(
                action_id=action.id,
                ok=False,
                message="Open the WhatsApp chat first, then ask Jarvis to send the message",
            )
        boxes = await self._whatsapp_text_boxes(driver)
        if not boxes:
            return ActionResult(action_id=action.id, ok=False, message="WhatsApp message box not available")
        await asyncio.to_thread(boxes[-1].send_keys, action.message)
        await asyncio.to_thread(boxes[-1].send_keys, Keys.ENTER)
        return ActionResult(
            action_id=action.id,
            ok=True,
            message="Sent WhatsApp message in the currently open chat after explicit confirmation",
        )

    async def _whatsapp_text_boxes(self, driver: webdriver.Chrome):
        return await asyncio.to_thread(
            driver.find_elements,
            By.CSS_SELECTOR,
            "div[contenteditable='true'][role='textbox'], div[contenteditable='true'], [contenteditable='true']",
        )

    @staticmethod
    def _ambiguous_whatsapp_matches(matches: Sequence[str]) -> bool:
        return len(list(dict.fromkeys(match.strip() for match in matches if match.strip()))) > 1

    @staticmethod
    def _whatsapp_visible_matches(driver: webdriver.Chrome, contact: str) -> list[str]:
        contact_words = [word.casefold() for word in contact.split() if word]
        candidates: list[str] = []
        rows = driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'], [data-testid='cell-frame-container']")
        for row in rows:
            text = row.text.strip()
            if not text:
                continue
            first_line = text.splitlines()[0].strip()
            if first_line and all(word in text.casefold() for word in contact_words):
                candidates.append(first_line)
        return list(dict.fromkeys(candidates))

    async def _whatsapp_phone_message(self, action: AgentAction) -> ActionResult:
        assert action.phone_number is not None
        digits = re.sub(r"\D", "", action.phone_number)
        if len(digits) < 8:
            return ActionResult(action_id=action.id, ok=False, message="Invalid phone_number")
        url = f"https://wa.me/{digits}?text={quote_plus(action.message or '')}"
        await self._open_url(url)
        return ActionResult(
            action_id=action.id,
            ok=True,
            message=f"Prepared WhatsApp message to +{digits}; press send in WhatsApp if prompted",
        )
