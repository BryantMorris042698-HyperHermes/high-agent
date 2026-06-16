# Deployment Guide

## Clone and Run

### Linux / Mac / Windows WSL
```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/python
pip install -e .           # Editable install
pip install -e ".[all]"    # With all extras (dev, ollama)

# Run
python high-agent-repl.py
python -m high_agent_engine sweep
python -m high_agent_engine crawl ./src --recursive
```

### Termux (Android)
```bash
pkg install python git
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/python
pip install -e .

# Optional: install Ollama for local LLM
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b

# Run
python high-agent-repl.py
```

### Rust (Desktop with TUI)
```bash
git clone https://github.com/BryantMorris042698-HyperHermes/high-agent.git
cd high-agent/rust
cargo build --features tui
cargo run --bin high-agent-tui --features tui   # Full TUI dashboard
cargo run --example basic --features tui         # CLI example
```

---

## Python Package Installation

### Editable install (recommended for development)
```bash
cd python
pip install -e .
```

### From source tarball
```bash
pip install high-agent-*.tar.gz
```

### Via PyPI (after v0.3.0 release)
```bash
pip install high-agent
```

### With LLM extras
```bash
pip install high-agent[ollama]    # Ollama support
pip install high-agent[all]       # All extras
```

---

## LLM Setup

### Ollama (local, free — recommended for Termux)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b            # Small model, fast on mobile
ollama pull codellama:7b           # Code-focused model

# Verify
ollama list
curl http://localhost:11411/api/tags  # Should return model list
```

### OpenAI
```bash
export OPENAI_API_KEY=sk-proj-...
python high-agent-repl.py --model gpt-4o --api-key $OPENAI_API_KEY
```

### OpenRouter (best for cost/quality)
```bash
export OPENROUTER_API_KEY=sk-or-...
python high-agent-repl.py --provider openrouter --model anthropic/claude-3.5-haiku
```

### Groq (fast inference)
```bash
export GROQ_API_KEY=gsk_...
python high-agent-repl.py --provider groq --model llama-3.3-70b-versatile
```

---

## Running as a Daemon

Start the background daemon for continuous monitoring:
```bash
python -m high_agent_engine daemon --port 8765
```

The daemon writes state to `~/.high-agent/state.json` every 5 seconds. The TUI reads it when you press [r] to refresh.

---

## CI/CD

### GitHub Actions
- **CI**: Runs on every push — Rust tests, Python tests, format checks
- **Release**: Publishes to PyPI on version tags (`v*.*.*`)

### Local Release Build
```bash
./scripts/build-release.sh
# Creates: dist/high-agent-*.tar.gz and dist/high_agent_engine-*.whl
```

### Manual PyPI Publish
```bash
pip install twine
cd dist
twine upload --repository pypi dist/*
```

---

## Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY python/ .
RUN pip install -e .
CMD ["python", "high-agent-repl.py"]
```
```bash
docker build -t graph-x-0x0 .
docker run -it graph-x-0x0
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `OPENROUTER_API_KEY` | OpenRouter API key | None |
| `GROQ_API_KEY` | Groq API key | None |
| `DEEPSEEK_API_KEY` | DeepSeek API key | None |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11411` |
| `HIGH_AGENT_STATE_FILE` | Path to state JSON | `~/.high-agent/state.json` |
| `HIGH_AGENT_HISTORY_MAX` | Max history entries | 1000 |

---

## Troubleshooting

### `pip install -e .` fails with "setup.py not found"
Make sure you're in the `python/` directory:
```bash
cd high-agent/python
pip install -e .
```

### Ollama connection refused
```bash
# Check if Ollama is running
curl http://localhost:11411/api/tags

# Start Ollama
ollama serve

# Or pull a model
ollama pull llama3.2:3b
```

### TUI won't compile on Termux
Rust TUI requires `cargo` and ncurses — not available on Termux. Use the Python engine instead:
```bash
python high-agent-repl.py
```

### GitHub PAT not working for git push
Use the REST API push method instead (the Python `urllib` blob→tree→commit→PATCH approach works even when git intercepts credentials).