from jarvis_backend.llm.action_parser import ActionParser
from jarvis_backend.actions.browser import BrowserActionExecutor
from jarvis_backend.config import ActionsConfig


def test_parses_structured_action() -> None:
    text = """
    ```json
    {
      "spoken_response": "Opening Chrome after confirmation.",
      "actions": [{"action": "open_app", "app_name": "chrome"}]
    }
    ```
    """
    decision = ActionParser().parse(text)
    assert decision.spoken_response == "Opening Chrome after confirmation."
    assert len(decision.actions) == 1
    assert decision.actions[0].action == "open_app"


def test_browser_debugger_addresses_include_chrome_and_edge() -> None:
    executor = BrowserActionExecutor(
        ActionsConfig(
            browser_debugger_address="127.0.0.1:9222",
            edge_debugger_address="127.0.0.1:9223",
            browser_debugger_addresses=["127.0.0.1:9222", "127.0.0.1:9223"],
        )
    )

    assert executor._debugger_addresses == ["127.0.0.1:9222", "127.0.0.1:9223"]
