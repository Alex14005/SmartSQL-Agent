import os
import sys
import json
import pandas as pd
import uuid
from dotenv import load_dotenv

load_dotenv()

# 1. SOLUCIÓN AL ERROR DE RUTAS: 
# Le decimos a Python que la carpeta raíz de nuestro proyecto también es parte del "Path"
# Esto permite que pueda importar la carpeta 'src' sin problemas.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datasets import Dataset
from ragas import evaluate
from langchain_core.messages import HumanMessage

# 2. SOLUCIÓN A LOS WARNINGS DE RAGAS:
# Actualizamos la ruta de importación según su nueva versión
from ragas.metrics import AnswerCorrectness, AnswerRelevancy

# Importamos el agente y el LLM ahora que Python ya conoce la carpeta 'src'
from src.agent.graph import smartsql_agent
from src.config.llm import llm

# ... (El resto de tu código de run_evaluation() se queda exactamente igual) ...
def run_evaluation():
    print("🚀 Iniciando Evaluación Automática de SmartSQL-Agent...")
    
    # 1. Cargar el dataset de evaluación
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "eval_dataset.csv")
    df = pd.read_csv(csv_path)
    
    # Listas para guardar lo que genere el agente
    generated_answers = []
    contexts = [] # RAGAS pide contextos (usaremos los resultados crudos del SQL)
    
    # 2. Iterar sobre cada pregunta del dataset
    for index, row in df.iterrows():
        question = row["question"]
        print(f"\n🔄 Evaluando pregunta {index + 1}/{len(df)}: {question}")
        
        # Generamos un thread_id único para cada pregunta (memoria limpia)
        config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        inputs = {"messages": [HumanMessage(content=question)]}
        
        # Ejecutamos el agente
        for output in smartsql_agent.stream(inputs, config=config):
            pass # Dejamos que corra
            
        # Revisamos si se detuvo por el Human-in-the-Loop (confianza baja)
        state = smartsql_agent.get_state(config)
        if state.next and "human_review_node" in state.next:
            print("   ⚠️ Confianza baja detectada. Auto-aprobando para la evaluación...")
            # Auto-aprobamos para no bloquear el script
            smartsql_agent.update_state(config, {"human_feedback": None, "requires_approval": False})
            for output in smartsql_agent.stream(None, config=config):
                pass
                
        # Obtenemos la respuesta final del agente
        final_state = smartsql_agent.get_state(config).values
        answer = final_state.get("final_answer", "Error al generar respuesta")
        raw_data = str(final_state.get("query_results", []))
        
        generated_answers.append(answer)
        contexts.append([raw_data]) # RAGAS pide una lista de strings para el contexto
        print(f"   🤖 Respuesta: {answer}")

    # 3. Preparar los datos en el formato que RAGAS necesita (HuggingFace Dataset)
    data_for_ragas = {
        "question": df["question"].tolist(),
        "answer": generated_answers,
        "ground_truth": df["ground_truth"].tolist(),
        "contexts": contexts
    }
    dataset = Dataset.from_dict(data_for_ragas)
    
    # 4. Configurar LLM y Embeddings dinámicamente según las API Keys
    print("\n📊 Preparando modelos para evaluación...")
    
    # Revisamos si existe la API Key de OpenAI en el entorno
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if has_openai:
        print("🌐 API Key detectada: Usando OpenAI Embeddings.")
        from langchain_openai import OpenAIEmbeddings
        eval_embeddings = OpenAIEmbeddings()
    else:
        print("🦙 No se detectó API Key: Usando Ollama local para Embeddings.")
        from langchain_ollama import OllamaEmbeddings
        # Usamos Llama 3.2 también para los vectores (puedes cambiarlo a "nomic-embed-text" si lo descargas en Ollama)
        eval_embeddings = OllamaEmbeddings(model="llama3.2")

    # Ejecutar las métricas de RAGAS
    print("⏳ Calculando métricas de RAGAS (esto puede tomar un momento, tu PC hará el esfuerzo local)...")
    
    result = evaluate(
        dataset=dataset,
        metrics=[AnswerCorrectness(), AnswerRelevancy()],
        llm=llm,                   # El LLM Juez (Ollama)
        embeddings=eval_embeddings # Los Embeddings dinámicos
    )
    
    # 5. Guardar el reporte de resultados
    # ... (el resto del código sigue igual) ...
    
    # 5. Guardar el reporte de resultados
    report_path = os.path.join(os.path.dirname(__file__), "metrics_report.json")
    
    # RAGAS devuelve un diccionario con los promedios
    metrics_dict = result.copy()
    
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics_dict, f, indent=4)
        
    print(f"\n✅ Evaluación completada. Reporte guardado en: {report_path}")
    print("\nResultados Globales:")
    for metric_name, score in metrics_dict.items():
        print(f" - {metric_name}: {score:.2f}/1.00")

if __name__ == "__main__":
    run_evaluation()