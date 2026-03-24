import pytest
from src.agent.state import SmartSQLState
from src.agent.graph import route_after_evaluation, route_after_human
from src.config.llm import get_llm

# TEST 1: Probar la fábrica de LLMs (Configuración)
def test_get_llm_factory():
    """Verifica que el sistema cargue el modelo correcto según el proveedor."""
    llm_openai = get_llm(provider="openai")
    assert llm_openai.__class__.__name__ == "ChatOpenAI"
    
    llm_ollama = get_llm(provider="ollama")
    assert llm_ollama.__class__.__name__ == "ChatOllama"

# TEST 2: Probar el enrutador de Evaluación (Human-in-the-Loop)
def test_route_after_evaluation():
    """Verifica que si la confianza es baja, se active la revisión humana."""
    # Simular estado con confianza baja (<80)
    state_low_confidence = {"requires_approval": True}
    assert route_after_evaluation(state_low_confidence) == "human_review_node"
    
    # Simular estado con confianza alta (>=80)
    state_high_confidence = {"requires_approval": False}
    assert route_after_evaluation(state_high_confidence) == "execute_sql_node"

# TEST 3: Probar el enrutador post-Humano (Feedback)
def test_route_after_human():
    """Verifica qué hace el agente después de que el humano interviene."""
    # Si el humano escribe algo para corregir
    state_with_feedback = {"human_feedback": "Olvida los clientes de Japón, busca en México"}
    assert route_after_human(state_with_feedback) == "generate_sql_node"
    
    # Si el humano solo presiona "Aprobar" (feedback vacío/None)
    state_approved = {"human_feedback": None}
    assert route_after_human(state_approved) == "execute_sql_node"