from typing import TypedDict, Annotated, List, Dict, Any, Optional, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator

class SmartSQLState(TypedDict, total=False):
    # Memoria Conversacional y entradas
    messages: Annotated[List[BaseMessage], add_messages]

    # 2 Generacion SQL y Validacion
    generated_sql: Optional[str]
    confidence_score: Optional[float]

    # 3 Human in the loop
    requires_approval: Optional[str]
    human_feedback: Optional[str]

    # Ejecucion de Base de datos
    query_results: Optional[List[Dict[str, Any]]]
    execution_error: Optional[str]

    # Respuesta Final
    final_answer: Optional[str]

    # Tracking de costos opcional
    # Se acumula el costo sumando el valor nuevo
    total_cost: Annotated[float, operator.add]
