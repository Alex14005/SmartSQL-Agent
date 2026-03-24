# 🤖 SmartSQL-Agent: Text-to-SQL AI con Human-in-the-Loop

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-State%20of%20the%20Art-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black)
![LLMOps](https://img.shields.io/badge/LLMOps-RAGAS-brightgreen)

**SmartSQL-Agent** es un agente autónomo de Inteligencia Artificial diseñado para interactuar con bases de datos relacionales utilizando lenguaje natural. A diferencia de los chatbots tradicionales, este proyecto implementa una arquitectura avanzada de **LangGraph** que incluye memoria conversacional, auto-corrección de errores, cálculo de costos y un sistema de seguridad de **Human-in-the-Loop (HITL)** para auditoría de consultas críticas.

---

## ✨ Características Principales

*   🗣️ **Text-to-SQL Inteligente:** Convierte preguntas en lenguaje natural en consultas SQL válidas, las ejecuta y devuelve la respuesta en formato conversacional.
*   🧠 **Memoria Contextual:** Recuerda el hilo de la conversación. (Ej. *"¿Cuántos clientes hay?"* -> *"¿Y de esos, cuántos son de México?"*).
*   🛡️ **Human-in-the-Loop (HITL):** Sistema de seguridad empresarial. Si el LLM tiene una confianza menor al 80% en la query generada, el agente se pausa (`breakpoint`) y solicita aprobación o feedback humano antes de tocar la base de datos.
*   🔄 **Auto-Corrección (Self-Healing):** Si la base de datos devuelve un error de sintaxis, el agente lee el error y reescribe la consulta automáticamente.
*   💰 **Cost Tracking:** Monitorea en tiempo real el costo en USD de los tokens consumidos por sesión (Ideal para entornos de producción).
*   🔒 **Soporte 100% Local / Cloud:** Configurable para usar la API de OpenAI (GPT-4), Anthropic (Claude) o modelos 100% locales y privados mediante **Ollama** (Llama 3.2).
*   📊 **LLMOps & Evaluación Automática:** Incluye un pipeline automatizado con **RAGAS** para medir matemáticamente la precisión (Answer Correctness) y relevancia del agente contra un dataset de pruebas.

---

## 🏗️ Arquitectura del Sistema (LangGraph)

El "cerebro" del agente es una máquina de estados finitos (`StateGraph`) que fluye de la siguiente manera:

1. **`generate_sql_node`**: Lee el esquema de la DB y la pregunta, genera la query.
2. **`evaluate_sql_node`**: LLM-as-a-Judge evalúa la query vs la pregunta (0-100%).
3. **`human_review_node`**: *(Condicional)* Si la confianza es < 80%, el grafo se congela esperando *input* humano.
4. **`execute_sql_node`**: Ejecuta la query de forma segura (Solo Lectura) usando Pandas. *(Si hay error, vuelve al nodo 1)*.
5. **`generate_answer_node`**: Traduce el JSON resultante a lenguaje natural.

---

## 📂 Estructura del Proyecto

```text
smartsql-agent/
├── data/                       # Base de datos SQLite y Dataset de evaluación (Ground Truth)
├── src/                        # Código fuente modular
│   ├── agent/                  # Lógica Core (graph.py, nodes.py, state.py)
│   ├── tools/                  # Herramientas de extracción de schemas y ejecución (db_tools.py)
│   └── config/                 # Prompts del sistema y Factory de LLMs (OpenAI, Ollama)
├── evaluation/                 # Pipeline de LLMOps con RAGAS (run_eval.py)
├── scripts/                    # Scripts de utilidad (seed_db.py)
├── app.py                      # Interfaz gráfica de usuario en Streamlit
└── requirements.txt            # Dependencias

## Instalacion y uso
** Clonar el repositorio y preparar el entorno **
git clone https://github.com/TU_USUARIO/SmartSQL-Agent.git
cd SmartSQL-Agent

Recomendado usar uv o venv para el entorno virtual
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

## Configuracion (Variables de entorno)
OPENAI_API_KEY=sk-tu-api-key
ANTHROPIC_API_KEY=sk-ant-tu-api-key

## Iniciar la base de datos de prueba
python scripts/seed_db.py

## Ejecutar la aplicaicon web UI
streamlit run app.py

## Evaluación Automática (LLMOps)
Para medir el rendimiento del agente antes de pasarlo a producción, corre el script de evaluación basado en RAGAS. Este script enviará un set de preguntas predefinidas al agente, recolectará sus respuestas y las evaluará usando IA.
python evaluation/run_eval.py