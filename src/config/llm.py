import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

# Cargar variables de entorno (API Keys) desde el archivo .env
load_dotenv()

def get_llm(provider: str = "ollama", temperature: float = 0.1):
    """
    Fábrica (Factory) para inicializar el LLM deseado.
    La temperatura en 0.0 es crucial para Text-to-SQL (queremos precisión, no creatividad).
    """
    if provider == "openai":
        # Requiere api en el archivo .env "OPENAI_API_KEY"
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature
        )
    
    elif provider == "cloude":
        # Requiere ANTHROPIC_API_KEY en tu .env
        return ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            temperature=temperature
        )
    
    elif provider == "ollama":
        # Ollama debe de estar corriendo al momenot
        return ChatOllama(
            model="qwen2.5:7b",
            temperature=temperature
        )
    
    else:
        raise ValueError(f"Proveedor LLM no soportado: {provider}")
    
# Instancia por defecto que usa
llm = get_llm(provider="ollama")