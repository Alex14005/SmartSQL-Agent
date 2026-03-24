import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, AIMessage

# Importamos nuestro agente compilado
from src.agent.graph import smartsql_agent

# Configuración de la página
st.set_page_config(page_title="SmartSQL Agent", page_icon="🤖", layout="wide")
st.title("🤖 SmartSQL Agent")
st.markdown("Agente Text-to-SQL con Memoria y Human-in-the-Loop")

# ==========================================
# 1. INICIALIZACIÓN DE ESTADOS (SESSION_STATE)
# ==========================================
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4()) # ID único para la memoria de LangGraph

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] # Para mostrar los mensajes en la UI

if "awaiting_review" not in st.session_state:
    st.session_state.awaiting_review = False # Bandera para saber si el grafo se pausó

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# ==========================================
# 2. MOSTRAR HISTORIAL DE CHAT
# ==========================================
for msg in st.session_state.chat_history:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(msg.content)

# ==========================================
# 3. INTERFAZ DE HUMAN-IN-THE-LOOP (HITL)
# ==========================================
# Si el agente está pausado, mostramos el panel de revisión en lugar del chat normal
if st.session_state.awaiting_review:
    st.warning("⚠️ **Revisión Humana Requerida**: La confianza del LLM es menor al 80%.")
    
    # Obtenemos el estado actual congelado en LangGraph
    current_state = smartsql_agent.get_state(config).values
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🔍 **Consulta SQL Generada:**")
        st.code(current_state.get('generated_sql', ''), language="sql")
    with col2:
        st.metric(label="Puntaje de Confianza", value=f"{current_state.get('confidence_score', 0)}%")
        
    st.markdown("### ¿Qué deseas hacer?")
    feedback = st.text_input("Escribe una corrección (o deja en blanco para aprobar):", key="feedback_input")
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("✅ Aprobar / Enviar"):
            if feedback.strip() == "":
                # El usuario aprobó sin cambios
                smartsql_agent.update_state(config, {"human_feedback": None, "requires_approval": False})
            else:
                # El usuario dio feedback
                smartsql_agent.update_state(config, {"human_feedback": feedback})
            
            # Reanudamos el grafo pasando None
            with st.spinner("Ejecutando y reanudando..."):
                for output in smartsql_agent.stream(None, config=config):
                    pass # Dejamos que termine de correr
                
                # Obtenemos la respuesta final y el costo
                final_state = smartsql_agent.get_state(config).values
                final_answer = final_state.get("final_answer", "Error al generar respuesta.")
                
                # Actualizamos historial visual y quitamos la pausa
                st.session_state.chat_history.append(AIMessage(content=final_answer))
                st.session_state.total_cost = final_state.get("total_cost", 0.0)
                st.session_state.awaiting_review = False
                st.rerun()

# ==========================================
# 4. ENTRADA DE USUARIO NORMAL (CHAT)
# ==========================================
# Solo mostramos el input de chat si no estamos esperando revisión
elif prompt := st.chat_input("Hazme una pregunta sobre tu base de datos (Ej: ¿Cuántos clientes hay?)"):
    
    # 1. Mostrar mensaje del usuario en la UI
    st.session_state.chat_history.append(HumanMessage(content=prompt))
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Correr el grafo de LangGraph
    with st.chat_message("assistant"):
        with st.spinner("Pensando y generando SQL..."):
            inputs = {"messages": [HumanMessage(content=prompt)]}
            
            # Corremos el grafo hasta que termine o se detenga en el Breakpoint
            for output in smartsql_agent.stream(inputs, config=config):
                pass
            
            # 3. Verificar si el grafo se detuvo por el Human-in-the-Loop
            state = smartsql_agent.get_state(config)
            
            if state.next and "human_review_node" in state.next:
                # Se pausó. Cambiamos la bandera y recargamos la página
                st.session_state.awaiting_review = True
                st.rerun()
            else:
                # Terminó exitosamente sin necesidad de humanos
                final_state = state.values
                final_answer = final_state.get("final_answer", "No pude encontrar la respuesta.")
                
                st.markdown(final_answer)
                st.session_state.chat_history.append(AIMessage(content=final_answer))
                st.session_state.total_cost = final_state.get("total_cost", 0.0)

# ==========================================
# SIDEBAR: MÉTRICAS Y COSTOS
# ==========================================
with st.sidebar:
    st.header("📊 Métricas de Sesión")
    st.metric(label="Costo Total Estimado", value=f"${st.session_state.total_cost:.4f}")
    if st.button("🗑️ Limpiar Memoria (Nueva Sesión)"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.awaiting_review = False
        st.session_state.total_cost = 0.0
        st.rerun()