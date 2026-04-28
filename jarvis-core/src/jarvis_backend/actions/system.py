from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from jarvis_backend.actions.base import ActionExecutor, ActionResult
from jarvis_backend.config import ActionsConfig
from jarvis_backend.state.models import AgentAction


class SystemActionExecutor(ActionExecutor):
    def __init__(self, config: ActionsConfig) -> None:
        self._config = config

    async def execute(self, action: AgentAction) -> ActionResult:
        if action.action == "open_app":
            return await self._open_app(action)
        if action.action == "close_app":
            return await self._close_app(action)
        if action.action == "focus_window":
            return await self._focus_window(action)
        if action.action == "system_command":
            return await self._system_command(action)
        return ActionResult(action_id=action.id, ok=False, message=f"Unsupported system action {action.action}")

    async def _open_app(self, action: AgentAction) -> ActionResult:
        if not action.app_name:
            return ActionResult(action_id=action.id, ok=False, message="Missing app_name")
        command = self._config.linux_app_allowlist.get(action.app_name.lower())
        if not command:
            return ActionResult(action_id=action.id, ok=False, message="App is not allowlisted")
        process = await asyncio.create_subprocess_exec(
            command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.sleep(0.2)
        if process.returncode not in (None, 0):
            _stdout, stderr = await process.communicate()
            return ActionResult(
                action_id=action.id,
                ok=False,
                message=stderr.decode("utf-8", errors="replace"),
            )
        return ActionResult(action_id=action.id, ok=True, message=f"Opened {action.app_name}")

    async def _close_app(self, action: AgentAction) -> ActionResult:
        if not action.app_name:
            return ActionResult(action_id=action.id, ok=False, message="Missing app_name")
        command = self._config.linux_app_allowlist.get(action.app_name.lower())
        if not command:
            return ActionResult(action_id=action.id, ok=False, message="App is not allowlisted")
        return await self._run_allowlisted(action, "pkill", ["-f", command])

    async def _focus_window(self, action: AgentAction) -> ActionResult:
        if not action.window_title:
            return ActionResult(action_id=action.id, ok=False, message="Missing window_title")
        return await self._run_allowlisted(action, "wmctrl", ["-a", action.window_title])

    async def _system_command(self, action: AgentAction) -> ActionResult:
        if not action.command:
            return ActionResult(action_id=action.id, ok=False, message="Missing command")
        command = action.command.strip()
        parsed = urlparse(command)
        executable = parsed.path if parsed.scheme else command.split()[0]
        if executable not in self._config.command_allowlist:
            return ActionResult(action_id=action.id, ok=False, message="Command is not allowlisted")
        return await self._run_allowlisted(action, executable, action.args)

    async def _run_allowlisted(
        self, action: AgentAction, executable: str, args: list[str]
    ) -> ActionResult:
        process = await asyncio.create_subprocess_exec(
            executable,
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        output = stdout.decode("utf-8", errors="replace").strip()
        error = stderr.decode("utf-8", errors="replace").strip()
        if process.returncode != 0:
            return ActionResult(action_id=action.id, ok=False, message=error or "Command failed")
        return ActionResult(action_id=action.id, ok=True, message=output or "Command executed")
