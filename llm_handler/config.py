import os
from pathlib import Path
from dotenv import load_dotenv

# Charger toutes les variables du fichier .env
load_dotenv()

class EmbeddingConfig:
    def __init__(self):
        self.model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.dimension = 384
        self.max_seq_length = 128

class LLMConfig:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        # Utilisation de 'gemini-1.5-flash' sans prÃ©fixe,
        # c'est le plus compatible avec le SDK 'google-genai'
        self.model_name = "gemini-1.5-flash"
        self.temperature = 0.7

class PathConfig:
    def __init__(self):
        self.base_path = Path(__file__).resolve().parent.parent
        self.cache = self.base_path / "cache"
        self.data = self.base_path / "data"
        self.cache.mkdir(parents=True, exist_ok=True)

class Config:
    def __init__(self):
        self.embedding = EmbeddingConfig()
        self.llm = LLMConfig()
        self.paths = PathConfig()

        class CacheSettings:
            def __init__(self):
                self.enabled = True
                self.expiry_days = 7

        self.cache = CacheSettings()

config = Config()
