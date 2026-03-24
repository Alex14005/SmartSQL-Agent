import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_community.callbacks import get_openai_callback

# Importamos lo que construimos en los pasos anteriores
from src.agent.state import SmartSQLState
from src.config.llm import llm
from src.config.prompts import (
    SQL_GENERATION_SYSTEM_PROMPT,
    CONFIDENCE_EVALUATION_PROMPT,
    FINAL_ANSWER_PROMPT
)
from src.tools.db_tools import get_database_schema, execute_sql_query

def _get_last_user_question(messages: list) -> str:
    """Función de ayuda para extraer la última pregunta del usuario del historial."""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            return msg.content
    return ""

def generate_sql_node(state: SmartSQLState):
    """Nodo 1: Genera la consulta SQL basada en la pregunta y el esquema."""
    print("--- 🧠 GENERANDO SQL ---")
    
    schema = get_database_schema()
    
    # Preparamos el System Prompt inyectando el esquema de la DB
    system_message = SystemMessage(
        content=SQL_GENERATION_SYSTEM_PROMPT.format(schema=schema)
    )
    
    # Construimos el historial de mensajes: System Prompt + Historial de la conversación
    messages_to_llm = [system_message] + state["messages"]
    
    # Si viene del Human-in-the-loop con correcciones, se lo añadimos como contexto
    if state.get("human_feedback"):
        messages_to_llm.append(
            HumanMessage(content=f"Corrección del humano sobre la query anterior: {state['human_feedback']}")
        )

    # Llamamos al LLM y trackeamos el costo
    with get_openai_callback() as cb:
        response = llm.invoke(messages_to_llm)
        cost = cb.total_cost

    # Limpiar el output (por si el LLM devuelve ```sql ... ``` a pesar de las instrucciones)
    raw_sql = response.content
    cleaned_sql = re.sub(r"```sql|```", "", raw_sql).strip()

    # Retornamos SOLO lo que queremos actualizar en el estado
    return {
        "generated_sql": cleaned_sql,
        "total_cost": cost,
        "execution_error": None # Reseteamos el error por si es un re-intento
    }

def evaluate_sql_node(state: SmartSQLState):
    """Nodo 2: Evalúa la confianza del SQL generado para decidir si requiere humano."""
    print("--- ⚖️ EVALUANDO CONFIANZA ---")
    
    question = _get_last_user_question(state["messages"])
    sql_query = state["generated_sql"]
    schema = get_database_schema()
    
    prompt = CONFIDENCE_EVALUATION_PROMPT.format(
        question=question, 
        sql_query=sql_query, 
        schema=schema
    )
    
    with get_openai_callback() as cb:
        response = llm.invoke([HumanMessage(content=prompt)])
        cost = cb.total_cost
        
    try:
        # Extraer solo los números de la respuesta
        score_str = re.search(r'\d+', response.content).group()
        score = float(score_str)
    except:
        score = 0.0 # Si el LLM no responde con un número, forzamos revisión humana
        
    requires_approval = score < 80.0
    print(f"Confianza: {score}% | Requiere aprobación: {requires_approval}")

    return {
        "confidence_score": score,
        "requires_approval": requires_approval,
        "total_cost": cost
    }

def execute_sql_node(state: SmartSQLState):
    """Nodo 3: Ejecuta la consulta en la base de datos."""
    print("--- ⚙️ EJECUTANDO SQL ---")
    
    sql_query = state["generated_sql"]
    result = execute_sql_query(sql_query)
    
    if result["success"]:
        print("✅ Ejecución exitosa")
        return {
            "query_results": result["data"],
            "execution_error": None
        }
    else:
        print(f"❌ Error SQL: {result['error']}")
        return {
            "query_results": None,
            "execution_error": result["error"]
        }

def generate_answer_node(state: SmartSQLState):
    """Nodo 4: Transforma los resultados crudos en una respuesta natural."""
    print("--- 💬 GENERANDO RESPUESTA FINAL ---")
    
    question = _get_last_user_question(state["messages"])
    sql_query = state["generated_sql"]
    results = state.get("query_results", [])
    
    prompt = FINAL_ANSWER_PROMPT.format(
        question=question,
        sql_query=sql_query,
        results=results
    )
    
    with get_openai_callback() as cb:
        response = llm.invoke([HumanMessage(content=prompt)])
        cost = cb.total_cost
        
    final_text = response.content
    
    # Retornamos la respuesta final y LA AÑADIMOS al historial de mensajes
    return {
        "final_answer": final_text,
        "messages": [AIMessage(content=final_text)],
        "total_cost": cost
    }