from jarvis_backend.llm.action_parser import ActionParser


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
