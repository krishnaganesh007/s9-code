import os
import json
import yaml
import requests
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
MODELS_JSON = ROOT / "config" / "models.json"
PROFILE_YAML = ROOT / "config" / "profiles.yaml"

# Objective is simple:
# # 1. Load model configurations from models.json
# 2. Load profile from profiles.yaml to determine which model to use
# 3. Initialize the appropriate model client (Gemini or Ollama)
# 4. Provide a unified method to generate text based on the selected model
# Where are the generate embeddings methods? -> They can be added similarly to generate_text if needed in the future.
# But without that, we cannot use the memory module fully, right? -> Correct, without embedding generation, certain memory functionalities may be limited.

class ModelManager:
    def __init__(self):
        self.config = json.loads(MODELS_JSON.read_text())
        self.profile = yaml.safe_load(PROFILE_YAML.read_text())

        self.text_model_key = self.profile["llm"]["text_generation"]
        self.model_info = self.config["models"][self.text_model_key]
        self.model_type = self.model_info["type"]

        # ✅ Gemini initialization (your style)
        if self.model_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            self.client = genai.Client(api_key=api_key)

    async def generate_text(self, prompt: str) -> str:
        if self.model_type == "gemini":
            return self._gemini_generate(prompt)

        elif self.model_type == "ollama":
            return self._ollama_generate(prompt)
        
        elif self.model_type == "qwen":
            return self._qwen_generate(prompt)

        raise NotImplementedError(f"Unsupported model type: {self.model_type}")

    def _gemini_generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_info["model"],
            contents=prompt
        )

        # ✅ Safely extract response text
        try:
            return response.text.strip()
        except AttributeError:
            try:
                return response.candidates[0].content.parts[0].text.strip()
            except Exception:
                return str(response)

    def _ollama_generate(self, prompt: str) -> str:
        response = requests.post(
            self.model_info["url"]["generate"],
            json={"model": self.model_info["model"], "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    
    def _qwen_generate(self, prompt: str) -> str:
        payload = {
            "model": self.model_info["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 20,
                "min_p": 0,
                "num_predict": 32768
            }
        }

        response = requests.post(
            self.model_info["url"]["generate"],
            json=payload
        )
        response.raise_for_status()
        return response.json()["response"].strip()

