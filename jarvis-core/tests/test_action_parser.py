from jarvis_backend.actions.browser import BrowserActionExecutor
from jarvis_backend.config import ActionsConfig
from jarvis_backend.config import TtsConfig
from jarvis_backend.llm.action_parser import ActionParser
from jarvis_backend.tts.voxcpm import VoxCpmTts


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


def test_parses_whatsapp_unknown_phone_number_action() -> None:
    decision = ActionParser().parse(
        """
        {
          "spoken_response": "I can prepare that WhatsApp message. Please confirm first.",
          "actions": [{"action": "whatsapp_message", "phone_number": "+15551234567", "message": "hi"}]
        }
        """
    )

    assert len(decision.actions) == 1
    assert decision.actions[0].action == "whatsapp_message"
    assert decision.actions[0].phone_number == "+15551234567"
    assert decision.actions[0].message == "hi"


def test_parses_whatsapp_current_chat_action() -> None:
    decision = ActionParser().parse(
        """
        {
          "spoken_response": "I can send hi in the current WhatsApp chat. Please confirm first.",
          "actions": [{"action": "whatsapp_message", "message": "hi"}]
        }
        """
    )

    assert len(decision.actions) == 1
    assert decision.actions[0].action == "whatsapp_message"
    assert decision.actions[0].contact is None
    assert decision.actions[0].phone_number is None
    assert decision.actions[0].message == "hi"


def test_browser_debugger_addresses_include_chrome_and_edge() -> None:
    executor = BrowserActionExecutor(
        ActionsConfig(
            browser_debugger_address="127.0.0.1:9222",
            edge_debugger_address="127.0.0.1:9223",
            browser_debugger_addresses=["127.0.0.1:9222", "127.0.0.1:9223"],
        )
    )

    assert executor._debugger_addresses == ["127.0.0.1:9222", "127.0.0.1:9223"]


def test_whatsapp_ambiguous_match_detection() -> None:
    assert BrowserActionExecutor._ambiguous_whatsapp_matches(["U Karthik", "U Karthik in Study Group"])
    assert not BrowserActionExecutor._ambiguous_whatsapp_matches(["U Karthik", "U Karthik"])


def test_voxcpm_voice_profiles_default_to_thick_female_and_allow_male() -> None:
    female = VoxCpmTts(TtsConfig())
    male = VoxCpmTts(TtsConfig(voice_profile="male_thick"))

    assert "woman" in female._voice_prompt()
    assert "thicker" in female._voice_prompt()
    assert "man" in male._voice_prompt()
    assert "baritone" in male._voice_prompt()
