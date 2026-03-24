import uuid
from langchain_core.messages import HumanMessage
from src.agent.graph import smartsql_agent

def main():
    # 1. Configurar la Memoria (Checkpointer)
    # Generamos un ID de sesión único. Todo lo que ocurra bajo este ID 
    # compartirá el mismo historial de mensajes.
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("="*50)
    print("🤖 BIENVENIDO A SMARTSQL-AGENT (TEST DE TERMINAL)")
    print("="*50)
    print("Escribe tu pregunta sobre la base de datos.")
    print("Ejemplo 1: '¿Cuántos clientes hay?'")
    print("Ejemplo 2: '¿Y de esos, cuántos son de México?' (Para probar memoria)")
    print("Escribe 'salir' para terminar.\n")
    
    while True:
        user_input = input("\n👤 Tú: ")
        if user_input.lower() in ['salir', 'exit', 'quit']:
            print("¡Hasta luego!")
            break
            
        # 2. Iniciar la ejecución del grafo
        # Le pasamos el mensaje del humano inicial
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        # Usamos .stream() para ver cómo avanza nodo por nodo
        for output in smartsql_agent.stream(inputs, config=config):
            # output es un diccionario con el nombre del nodo y los cambios en el estado
            for node_name, state_changes in output.items():
                print(f"📍 [Grafo avanzó por]: {node_name}")
        
        # 3. Revisar si el grafo se pausó (Human-in-the-Loop)
        # LangGraph pausa la ejecución y pone el siguiente nodo en state.next
        state = smartsql_agent.get_state(config)
        
        if state.next and "human_review_node" in state.next:
            current_state = state.values
            print("\n" + "⚠️ "*20)
            print("PAUSA: SE REQUIERE REVISIÓN HUMANA (Confianza < 80%)")
            print(f"SQL Generado : {current_state.get('generated_sql')}")
            print(f"Confianza    : {current_state.get('confidence_score')}%")
            print("⚠️ "*20)
            
            action = input("\n¿Qué deseas hacer?\n[a] Aprobar query\n[o escribe tu corrección/feedback para el LLM]: ")
            
            if action.lower() == 'a':
                # Aprobamos limpiando el feedback y quitando la alerta
                smartsql_agent.update_state(
                    config, 
                    {"human_feedback": None, "requires_approval": False},
                )
                print("✅ Aprobado por el humano. Continuando...")
            else:
                # El usuario escribió texto, lo tomamos como feedback para corregir
                smartsql_agent.update_state(
                    config, 
                    {"human_feedback": action},
                )
                print("🔄 Feedback recibido. Re-generando SQL...")
            
            # Reanudamos el grafo pasándole None como input
            for output in smartsql_agent.stream(None, config=config):
                for node_name, state_changes in output.items():
                    print(f"📍 [Grafo avanzó por]: {node_name}")
                    
        # 4. Mostrar el resultado final y los costos
        final_state = smartsql_agent.get_state(config).values
        if "final_answer" in final_state:
            print(f"\n🤖 Agente: {final_state['final_answer']}")
            
        # Mostramos el tracking de costos acumulados
        costo = final_state.get('total_cost', 0.0)
        print(f"💰 Costo acumulado de sesión: ${costo:.4f}")

if __name__ == "__main__":
    main()