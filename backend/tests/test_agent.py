from app.agents.career import CareerAgent
from app.core.config import Settings


def test_adk_agent_is_initialized_with_typed_contract():
    settings = Settings(gemini_api_key="test-key")
    agent = CareerAgent.from_settings(settings).build_adk_agent(settings)
    assert agent.name == "career_intelligence"
    assert agent.input_schema.__name__ == "CareerAnalysisInput"
    assert agent.output_schema.__name__ == "CareerAnalysisOutput"
