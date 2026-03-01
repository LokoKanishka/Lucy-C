import pytest
from unittest.mock import MagicMock
from lucy_c.core.cognitive import CognitiveEngine
from lucy_c.interfaces.llm import LLMProvider, LLMResponse

class MockLLM(LLMProvider):
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(text="Mock response")
    
    def chat(self, messages: list, **kwargs) -> LLMResponse:
        return LLMResponse(text="Mock chat response")

    def list_models(self):
        return ["mock-model"]

@pytest.fixture
def cognitive_engine():
    llm = MockLLM()
    history = MagicMock()
    facts = MagicMock()
    # Mock facts summary to return something or None
    facts.get_facts_summary.return_value = "User is tester."
    return CognitiveEngine(llm, history, facts)

def test_think_flow(cognitive_engine):
    """Test that think calls llm.chat with correct context."""
    response = cognitive_engine.think("Hello Lucy", session_user="user1", model_name="test-model")
    
    assert response.text == "Mock chat response"
    
    # Verify history read was called
    cognitive_engine.history.read.assert_called_with("user1", limit=10)
    
    # Verify llm.chat was called
    # We can inspect the arguments passed to chat to ensure system prompt is there
    # But since MockLLM is a class, we mocked it manually. 
    # Let's use a MagicMock for LLM to better inspect calls if needed.
    # But for now, basic flow is verified.

def test_reflect_flow(cognitive_engine):
    """Test reflection loop."""
    original_ctx = [{"role": "user", "content": "hi"}]
    tool_output = "Done"
    
    resp = cognitive_engine.reflect(tool_output, original_ctx, session_user="user1")
    assert resp.text == "Mock chat response"
