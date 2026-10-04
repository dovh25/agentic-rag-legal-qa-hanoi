from src.agent.graph import create_agent_graph


def test_agent_graph_execution():
    graph = create_agent_graph()
    initial_state = {
        "query": "Quy định về thu hồi đất và bồi thường tái định cư tại Long Biên",
        "as_of_date": "2024-08-01",
        "district": "Long Biên",
        "reasoning_steps": [],
    }

    result = graph.invoke(initial_state)

    assert "answer" in result
    assert "citations" in result
    assert "status" in result
    assert len(result["reasoning_steps"]) > 0


def test_agent_clarification_flow():
    graph = create_agent_graph()
    initial_state = {
        "query": "đất",  # ambiguous
        "reasoning_steps": [],
    }

    result = graph.invoke(initial_state)
    assert result["status"] == "clarification_needed"
