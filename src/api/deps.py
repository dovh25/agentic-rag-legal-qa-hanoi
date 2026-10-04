from functools import lru_cache

from src.agent.graph import create_agent_graph
from src.core.config import Settings, get_settings


def get_app_settings() -> Settings:
    """Dependency provider for application settings."""
    return get_settings()


@lru_cache
def get_agent_graph():
    """Dependency provider for compiled LangGraph agent graph."""
    return create_agent_graph()
