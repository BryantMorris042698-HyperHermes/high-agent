"""Ollama API client — generate, chat, pull models."""

from __future__ import annotations
import json
import os
import requests
from typing import List, Optional, Dict, Any

DEFAULT_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
TIMEOUT = 120

class OllamaClient:
    def __init__(self, base_url: str = DEFAULT_HOST, default_model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.default_model = default_model

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return r.status_code == 200
        except:
            return False

    def list_models(self) -> List[Dict[str, Any]]:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=TIMEOUT)
            data = r.json()
            return data.get("models", [])
        except:
            return []

    def pull_model(self, model: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{self.base_url}/api/pull",
            json={"name": model},
            stream=True,
            timeout=3600,
        )
        status = {}
        for line in resp.iter_lines():
            if line:
                try:
                    status = json.loads(line)
                    if "error" in status:
                        raise Exception(status["error"])
                except: pass
        return status

    def generate(self, prompt: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
        model = model or self.default_model
        req = {
            "model": model, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.7, "num_predict": 512},
        }
        if system:
            req["system"] = system
        r = requests.post(f"{self.base_url}/api/generate", json=req, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json().get("response", "")

    def chat(self, messages: List[tuple], model: Optional[str] = None) -> str:
        model = model or self.default_model
        ollama_msgs = [{"role": role, "content": content} for role, content in messages]
        req = {
            "model": model, "messages": ollama_msgs, "stream": False,
            "options": {"temperature": 0.7, "num_predict": 512},
        }
        r = requests.post(f"{self.base_url}/api/chat", json=req, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")

    def show_model(self, model: str) -> Dict[str, Any]:
        r = requests.post(f"{self.base_url}/api/show", json={"name": model}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()

    def copy_model(self, src: str, dst: str) -> None:
        r = requests.post(f"{self.base_url}/api/copy", json={"source": src, "destination": dst}, timeout=TIMEOUT)
        r.raise_for_status()

    def delete_model(self, model: str) -> None:
        r = requests.delete(f"{self.base_url}/api/delete", json={"name": model}, timeout=TIMEOUT)
        r.raise_for_status()


if __name__ == "__main__":
    client = OllamaClient()
    print(f"Ollama available: {client.is_available()}")
    if client.is_available():
        models = client.list_models()
        print(f"Models: {[m['name'] for m in models]}")
        print(client.generate("Explain Φ(G) in one sentence."))
    else:
        print("Ollama not running. Install: curl -fsSL https://ollama.com/install.sh | sh")