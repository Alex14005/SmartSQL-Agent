from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Importamos nuestro Estado y nuestros Nodos
from src.agent.state import SmartSQLState
from src.agent.nodes import (
    generate_sql_node,
    evaluate_sql_node,
    execute_sql_node,
    generate_answer_node
)

def human_review_node(state: SmartSQLState):
    """
    Nodo 'Dummy' (pasivo). 
    Su único propósito es servir como un punto de anclaje para pausar el grafo.
    Cuando el grafo se reanuda, este nodo se ejecuta y no modifica nada por sí solo,
    ya que las modificaciones (feedback o aprobación) las hará el humano desde la interfaz.
    """
    print("--- 👤 REVISIÓN HUMANA COMPLETADA / OMITIDA ---")
    return {}

# ==========================================
# FUNCIONES DE ENRUTAMIENTO (CONDICIONALES)
# ==========================================

def route_after_evaluation(state: SmartSQLState) -> str:
    """Decide si vamos a ejecución directa o pedimos revisión humana."""
    if state.get("requires_approval"):
        print("🔀 Ruta: Confianza baja -> Pausar para revisión humana")
        return "human_review_node"
    
    print("🔀 Ruta: Confianza alta -> Ejecutar SQL directamente")
    return "execute_sql_node"

def route_after_human(state: SmartSQLState) -> str:
    """Decide qué hacer después de que el humano intervino."""
    # Si el humano escribió algún feedback (ej. "Te faltó filtrar por país")
    if state.get("human_feedback"):
        print("🔀 Ruta: Humano dio feedback -> Regenerar SQL")
        return "generate_sql_node"
    
    # Si el humano solo aprobó (human_feedback es None o vacío)
    print("🔀 Ruta: Humano aprobó la query -> Ejecutar SQL")
    return "execute_sql_node"

def route_after_execution(state: SmartSQLState) -> str:
    """Decide si hubo un error en la DB y hay que reintentar."""
    if state.get("execution_error"):
        print(f"🔀 Ruta: Error SQL detectado -> Auto-corregir")
        return "generate_sql_node"
    
    print("🔀 Ruta: Ejecución exitosa -> Generar respuesta final")
    return "generate_answer_node"

# ==========================================
# CONSTRUCCIÓN DEL GRAFO
# ==========================================

# 1. Inicializamos el grafo con nuestra estructura de Estado
workflow = StateGraph(SmartSQLState)

# 2. Añadimos todos los nodos
workflow.add_node("generate_sql_node", generate_sql_node)
workflow.add_node("evaluate_sql_node", evaluate_sql_node)
workflow.add_node("human_review_node", human_review_node)
workflow.add_node("execute_sql_node", execute_sql_node)
workflow.add_node("generate_answer_node", generate_answer_node)

# 3. Conectamos el flujo principal (Edges simples)
workflow.add_edge(START, "generate_sql_node")
workflow.add_edge("generate_sql_node", "evaluate_sql_node")

# 4. Añadimos las rutas condicionales (Conditional Edges)
workflow.add_conditional_edges(
    "evaluate_sql_node",
    route_after_evaluation,
    {
        "human_review_node": "human_review_node",
        "execute_sql_node": "execute_sql_node"
    }
)

workflow.add_conditional_edges(
    "human_review_node",
    route_after_human,
    {
        "generate_sql_node": "generate_sql_node",
        "execute_sql_node": "execute_sql_node"
    }
)

workflow.add_conditional_edges(
    "execute_sql_node",
    route_after_execution,
    {
        "generate_sql_node": "generate_sql_node", # Bucle de corrección
        "generate_answer_node": "generate_answer_node"
    }
)

workflow.add_edge("generate_answer_node", END)

# ==========================================
# COMPILACIÓN Y MEMORIA
# ==========================================

# El MemorySaver es vital para guardar el historial de la conversación (Memoria)
# y para mantener el estado congelado mientras esperamos al humano.
memory = MemorySaver()

# Compilamos el grafo. Le decimos que se PAUSE EXACTAMENTE ANTES de entrar al nodo humano.
smartsql_agent = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review_node"]
)