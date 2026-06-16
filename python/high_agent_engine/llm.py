"""Unified LLM client — Ollama, OpenAI, OpenRouter, Groq, DeepSeek.

Auto-detects provider from URL or model name. Pass a model like:
  - "llama3.2:3b"             → Ollama (http://localhost:11434)
  - "gpt-4o"                  → OpenAI (needs OPENAI_API_KEY)
  - "anthropic/claude-sonnet-4" → OpenRouter
  - "groq/llama-3.3-70b"      → Groq
  - "deepseek-chat"           → DeepSeek
  - "http://localhost:11434/qwen2.5:1.5b" → custom Ollama URL
"""

from __future__ import annotations
import json
import os
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path

# Config file — persists provider/model choice across runs
_CONFIG_PATH = Path.home() / ".high-agent" / "llm-config.json"


def _save_config(provider: str, model: str, api_key: str = "") -> None:
    """Save LLM choice to ~/.high-agent/llm-config.json."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {"provider": provider, "model": model}
    if api_key:
        data["api_key"] = api_key
    _CONFIG_PATH.write_text(json.dumps(data, indent=2))


def _load_config() -> Optional[Dict]:
    """Load saved LLM config, return None if not found."""
    try:
        if _CONFIG_PATH.exists():
            return json.loads(_CONFIG_PATH.read_text())
    except Exception:
        pass
    return None
import json

# ── Provider defaults ─────────────────────────────────────────────────────────

PROVIDER_MODELS = {
    "openai": {
        "default": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
        "env_key": "OPENAI_API_KEY",
    },
    "openrouter": {
        "default": "anthropic/claude-sonnet-4",
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
    },
    "groq": {
        "default": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
    },
    "deepseek": {
        "default": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "ollama": {
        "default": "llama3.2:3b",
        "base_url": "http://localhost:11434",
        "env_key": "OLLAMA_HOST",
    },
}

OLLAMA_MODELS = {
    "llama3.2:3b", "llama3.2:1b", "llama3.1:8b", "llama3.1:70b",
    "llama3:8b", "llama3:70b",
    "mistral:7b", "mistral-nemo:12b",
    "codellama:7b", "codellama:13b", "codellama:34b",
    "qwen2.5:0.5b", "qwen2.5:1.5b", "qwen2.5:3b", "qwen2.5:7b", "qwen2.5:14b", "qwen2.5:32b",
    "phi3:3.8b", "phi3:14b",
    "nomic-embed-text", "mxbai-embed-large",
    "gemma2:2b", "gemma2:9b", "gemma2:27b",
    "llava:7b", "llava:13b", "llava:34b",
    "dolphin-mixtral:8x22b",
    "wizardlm2:8x22b",
    "aya:8b", "aya:35b",
    "phi4:14b",
    "qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "qwen2.5-coder:7b", "qwen2.5-coder:14b",
}


def _detect_provider(model: str, base_url: Optional[str]) -> tuple[str, str, str]:
    """Returns (provider, final_base_url, env_key)."""
    if base_url:
        if "localhost" in base_url or "127.0.0.1" in base_url:
            return "ollama", base_url, "OLLAMA_HOST"
        if "openrouter" in base_url:
            return "openrouter", base_url, "OPENROUTER_API_KEY"
        if "groq" in base_url:
            return "groq", base_url, "GROQ_API_KEY"
        if "deepseek" in base_url:
            return "deepseek", base_url, "DEEPSEEK_API_KEY"
        return "openai", base_url, "OPENAI_API_KEY"

    # Auto-detect from model name
    if ":" in model or model.lower() in {m.lower() for m in OLLAMA_MODELS}:
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return "ollama", host, "OLLAMA_HOST"
    if "/" in model:
        # openrouter format: provider/model
        return "openrouter", PROVIDER_MODELS["openrouter"]["base_url"], "OPENROUTER_API_KEY"
    if model.startswith("gpt-") or model.startswith("o1-") or model.startswith("o3-"):
        return "openai", PROVIDER_MODELS["openai"]["base_url"], "OPENAI_API_KEY"
    if model.startswith("deepseek"):
        return "deepseek", PROVIDER_MODELS["deepseek"]["base_url"], "DEEPSEEK_API_KEY"
    if model.startswith("groq/"):
        return "groq", PROVIDER_MODELS["groq"]["base_url"], "GROQ_API_KEY"

    # Default: try ollama first, fall back to openai
    return "ollama", PROVIDER_MODELS["ollama"]["base_url"], "OLLAMA_HOST"


class LLMClient:
    """Unified LLM client for Ollama + OpenAI-compatible APIs.

    Usage:
        # Ollama (local)
        client = LLMClient(model="llama3.2:3b")

        # OpenAI
        client = LLMClient(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

        # OpenRouter
        client = LLMClient(model="anthropic/claude-sonnet-4", api_key=os.getenv("OPENROUTER_API_KEY"))

        # Auto-detect
        client = LLMClient(model="llama3.2:3b")  # → Ollama
        client = LLMClient(model="gpt-4o")        # → OpenAI

        # Chat
        resp = client.chat([("user", "Hello")])
        resp = client.chat([("system", "You are helpful."), ("user", "Hi")])

        # Generate
        resp = client.generate("Explain Φ(G) in one sentence.")

        # Streaming
        for chunk in client.generate("Write code", stream=True):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        timeout: int = 120,
    ):
        # Resolve provider
        if provider and provider in PROVIDER_MODELS:
            self.provider = provider
            defaults = PROVIDER_MODELS[provider]
            self.model = model or defaults["default"]
            self.base_url = base_url or defaults["base_url"]
            self._api_key_env = defaults["env_key"]
        else:
            self.model = model or PROVIDER_MODELS["ollama"]["default"]
            self.provider, self.base_url, self._api_key_env = _detect_provider(
                self.model, base_url
            )

        # API key — from param, then env var
        self._api_key = api_key or os.getenv(self._api_key_env, "")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Session reuse
        self._session = None

    def _session_get(self) -> requests.Session:
        if self._session is None:
            self._session = requests.Session()
            if self._api_key and self.provider != "ollama":
                self._session.headers["Authorization"] = f"Bearer {self._api_key}"
        return self._session

    @property
    def is_ollama(self) -> bool:
        return self.provider == "ollama"

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    # ── Availability ──────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Check if the LLM endpoint is reachable."""
        try:
            if self.is_ollama:
                r = self._session_get().get(
                    self._url("/api/tags"), timeout=5
                )
                return r.status_code == 200
            else:
                r = self._session_get().get(
                    self._url("/models"),
                    timeout=10,
                    headers={"HTTP-Referer": "https://high-agent.ai"},
                )
                return r.status_code in (200, 403)  # 403 = valid key, no models listed
        except Exception:
            return False

    def status(self) -> Dict[str, Any]:
        """Return full status dict."""
        avail = self.is_available()
        models = []
        if avail and self.is_ollama:
            try:
                r = self._session_get().get(self._url("/api/tags"), timeout=10)
                models = [m["name"] for m in r.json().get("models", [])]
            except Exception:
                pass
        return {
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key_set": bool(self._api_key),
            "available": avail,
            "models": models,
        }

    # ── Generate ────────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        """Single-shot text generation. Returns full response (or generator if stream=True)."""
        if self.is_ollama:
            return self._ollama_generate(prompt, system=system, stream=stream, **kwargs)
        else:
            return self._openai_generate(prompt, system=system, stream=stream, **kwargs)

    def _ollama_generate(
        self, prompt: str, system: Optional[str] = None, stream: bool = False, **_
    ) -> str:
        req = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        if system:
            req["system"] = system
        r = self._session_get().post(
            self._url("/api/generate"), json=req, timeout=self.timeout, stream=stream
        )
        r.raise_for_status()
        if stream:
            def gen():
                for line in r.iter_lines():
                    if line:
                        try:
                            yield json.loads(line)["response"]
                        except (json.JSONDecodeError, KeyError):
                            pass
            return gen()  # type: ignore
        return r.json().get("response", "")

    def _openai_generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
        **kwargs,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        data = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://high-agent.ai",
            "X-Title": "Graph_x_0x0",
        }
        if self.provider == "openrouter":
            headers["HTTP-Referer"] = "https://openrouter.ai"
        r = self._session_get().post(
            self._url("/chat/completions"), json=data, headers=headers,
            timeout=self.timeout, stream=stream
        )
        r.raise_for_status()
        if stream:
            def gen():
                for line in r.iter_lines():
                    if line and line.startswith(b"data: "):
                        if line == b"data: [DONE]":
                            break
                        try:
                            yield json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass
            return gen()  # type: ignore
        return r.json()["choices"][0]["message"]["content"]

    # ── Chat ────────────────────────────────────────────────────────────────

    def chat(
        self,
        messages: List[tuple],
        stream: bool = False,
        **kwargs,
    ) -> str:
        """Chat with messages list of (role, content) tuples.

        Roles: 'system', 'user', 'assistant'
        """
        if self.is_ollama:
            return self._ollama_chat(messages, stream=stream, **kwargs)
        else:
            return self._openai_chat(messages, stream=stream, **kwargs)

    def _ollama_chat(
        self, messages: List[tuple], stream: bool = False, **kwargs
    ) -> str:
        ollama_msgs = [
            {"role": role, "content": content}
            for role, content in messages
            if content
        ]
        data = {
            "model": self.model,
            "messages": ollama_msgs,
            "stream": stream,
            "options": {
                "temperature": kwargs.get("temperature", self.temperature),
                "num_predict": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        r = self._session_get().post(
            self._url("/api/chat"), json=data, timeout=self.timeout, stream=stream
        )
        r.raise_for_status()
        if stream:
            def gen():
                for line in r.iter_lines():
                    if line:
                        try:
                            yield json.loads(line)["message"]["content"]
                        except (json.JSONDecodeError, KeyError):
                            pass
            return gen()  # type: ignore
        return r.json().get("message", {}).get("content", "")

    def _openai_chat(
        self, messages: List[tuple], stream: bool = False, **kwargs
    ) -> str:
        formatted = [
            {"role": role, "content": content}
            for role, content in messages
            if content
        ]
        data = {
            "model": self.model,
            "messages": formatted,
            "stream": stream,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://high-agent.ai",
            "X-Title": "Graph_x_0x0",
        }
        r = self._session_get().post(
            self._url("/chat/completions"), json=data, headers=headers,
            timeout=self.timeout, stream=stream
        )
        r.raise_for_status()
        if stream:
            def gen():
                for line in r.iter_lines():
                    if line and line.startswith(b"data: "):
                        if line == b"data: [DONE]":
                            break
                        try:
                            yield json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass
            return gen()  # type: ignore
        return r.json()["choices"][0]["message"]["content"]

    # ── Embeddings ──────────────────────────────────────────────────────────

    def embed(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        if self.is_ollama:
            r = self._session_get().post(
                self._url("/api/embeddings"),
                json={"model": self.model, "prompt": text},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("embedding", [])
        else:
            r = self._session_get().post(
                self._url("/embeddings"),
                json={"model": self.model, "input": text},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            r.raise_for_status()
            return r.json().get("data", [{}])[0].get("embedding", [])

    # ── Model management ───────────────────────────────────────────────────

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        if self.is_ollama:
            try:
                r = self._session_get().get(self._url("/api/tags"), timeout=10)
                return r.json().get("models", [])
            except Exception:
                return []
        return [{"name": self.model, "provider": self.provider}]

    def pull(self, model: Optional[str] = None) -> None:
        """Pull a model (Ollama only)."""
        if not self.is_ollama:
            raise RuntimeError("pull() only works with Ollama provider")
        name = model or self.model
        r = requests.post(
            self._url("/api/pull"),
            json={"name": name},
            stream=True,
            timeout=3600,
        )
        for line in r.iter_lines():
            if line:
                try:
                    s = json.loads(line)
                    if "error" in s:
                        raise RuntimeError(s["error"])
                    status = s.get("status", "")
                    if "pulling" in status or "verifying" in status or "writing" in status:
                        print(f"\r  [{name}] {status}...", end="", flush=True)
                except Exception:
                    pass
        print()

    def show_model(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Show model info (Ollama only)."""
        if not self.is_ollama:
            return {"name": model or self.model, "provider": self.provider}
        r = self._session_get().post(
            self._url("/api/show"),
            json={"name": model or self.model},
            timeout=30,
        )
        r.raise_for_status()
        return r.json()


# ── Quick setup helpers ────────────────────────────────────────────────────────

def setup_ollama(model: str = "llama3.2:3b") -> LLMClient:
    """Create LLMClient pointing at local Ollama. Auto-detects running status."""
    client = LLMClient(model=model)
    if client.is_available():
        print(f"[Ollama] Connected — {client.model} @ {client.base_url}")
    else:
        print(f"[Ollama] Not running at {client.base_url}")
        print("  Install: curl -fsSL https://ollama.com/install.sh | sh")
        print("  Start:   ollama serve")
        print("  Pull:    ollama pull llama3.2:3b")
    return client


def setup_api_key(
    model: str = "gpt-4o-mini",
    provider: str = "openai",
) -> LLMClient:
    """Create LLMClient using an API key. Validates key before returning."""
    client = LLMClient(model=model, provider=provider)
    if client.is_available():
        print(f"[{client.provider}] Connected — {client.model}")
    else:
        print(f"[{client.provider}] Failed to connect with {client.model}")
        print(f"  Check your {client._api_key_env} environment variable")
    return client


def auto_setup() -> LLMClient:
    """Detect the best available LLM. Priority:
    1. Saved config (from `setup` command)
    2. Ollama (if running locally)
    3. Env vars: DEEPSEEK > OPENAI > OPENROUTER > GROQ
    """
    # 1. Saved config from previous `setup` run
    cfg = _load_config()
    if cfg:
        kwargs: Dict[str, Any] = {"provider": cfg["provider"], "model": cfg["model"]}
        if "api_key" in cfg:
            kwargs["api_key"] = cfg["api_key"]
        client = LLMClient(**kwargs)
        if client.is_available():
            return client

    # 2. Ollama (local, no key needed)
    client = LLMClient(model="llama3.2:3b")
    if client.is_available():
        return client

    # 3. DeepSeek
    if os.getenv("DEEPSEEK_API_KEY"):
        client = LLMClient(provider="deepseek")
        if client.is_available():
            return client

    # 4. OpenAI
    if os.getenv("OPENAI_API_KEY"):
        client = LLMClient(provider="openai")
        if client.is_available():
            return client

    # 5. OpenRouter
    if os.getenv("OPENROUTER_API_KEY"):
        client = LLMClient(provider="openrouter")
        if client.is_available():
            return client

    # 6. Groq
    if os.getenv("GROQ_API_KEY"):
        client = LLMClient(provider="groq")
        if client.is_available():
            return client

    # Fallback — not available, but returns something
    return LLMClient(model="llama3.2:3b")


# ── Pretty status ─────────────────────────────────────────────────────────────

def print_status(client: Optional[LLMClient] = None) -> None:
    """Print a pretty status table of all providers."""
    print("\nLLM Provider Status")
    print("─" * 50)
    print(f"  {'Provider':<12} {'Model':<30} {'Status'}")
    print("  " + "-" * 50)
    tried = set()

    # Try each provider
    for prov_name, defaults in PROVIDER_MODELS.items():
        key = os.getenv(defaults["env_key"], "")
        if not key:
            continue
        if prov_name in tried:
            continue
        try:
            c = LLMClient(provider=prov_name)
            avail = c.is_available()
            status = "✓ available" if avail else "✗ auth failed"
            print(f"  {prov_name:<12} {c.model:<30} {status}")
            tried.add(prov_name)
        except Exception as e:
            print(f"  {prov_name:<12} {'':30} ✗ {e}")

    # Try Ollama (no key needed)
    if "ollama" not in tried:
        c = LLMClient(provider="ollama")
        avail = c.is_available()
        status = "✓ available" if avail else "✗ not running"
        print(f"  {'ollama':<12} {c.model:<30} {status}")

    print()


if __name__ == "__main__":
    print_status()
    print("\nTrying auto-setup...")
    client = auto_setup()
    if client.is_available():
        print(f"\nQuick test: {client.generate('What is Φ(G)? Keep it under 20 words.')}")
    else:
        print("\nNo LLM provider available. Set up with:")
        print("  Ollama:    curl -fsSL https://ollama.com/install.sh | sh && ollama pull llama3.2:3b")
        print("  OpenAI:    export OPENAI_API_KEY=sk-...")
        print("  OpenRouter: export OPENROUTER_API_KEY=sk-or-...")
        print("  Groq:      export GROQ_API_KEY=gsk_...")
