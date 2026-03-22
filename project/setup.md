# Setup Guide

This project runs fully offline with a local Ollama server and a Python script that calls the local REST API.

## 1. Install Ollama

Choose the method for your operating system:

- Windows: download and run the official installer from `https://ollama.com/download` or the Windows docs page `https://docs.ollama.com/windows`
- macOS: install from `https://ollama.com/download` or see `https://docs.ollama.com/macos`
- Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

After installation, Ollama serves its local API on `http://localhost:11434` by default.

## 2. Pull the Llama 3.2 3B model

Use the required model for this project:

```bash
ollama pull llama3.2:3b
```

If your Ollama install only exposes the default 3B tag as `llama3.2`, you can pull that instead and update `MODEL_NAME` inside `chatbot.py`.

## 3. Start Ollama

In most desktop installs, Ollama runs in the background after launch. If you are using the standalone CLI or Linux service flow, start the local server with:

```bash
ollama serve
```

Optional check:

```bash
ollama run llama3.2:3b
```

That confirms the model is available locally before running the Python script.

## 4. Create a Python virtual environment

From the `project/` directory:

```bash
python -m venv .venv
```

Activate it:

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
source .venv/bin/activate
```

## 5. Install the Python dependency

```bash
pip install requests
```

## 6. Run the chatbot evaluation

```bash
python chatbot.py
```

The script will:

- load the zero-shot and one-shot prompt templates
- send prompts to the local Ollama endpoint
- evaluate 20 customer support queries
- save the outputs to `eval/results.md`

## 7. Optional custom query file

You can provide your own text file with one query per line:

```bash
python chatbot.py --queries-file custom_queries.txt
```

## 8. Troubleshooting

- If you get a connection error, make sure Ollama is running and reachable at `http://localhost:11434`
- If you get a model error, make sure `llama3.2:3b` has been pulled successfully
- If PowerShell blocks virtual environment activation, allow local scripts for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
