# Medical LLM (LangChain + Streamlit)

A professional medical Q&A assistant built with:
- `Streamlit` for the web UI
- `LangChain` for orchestration
- `Chroma` for document retrieval (RAG)
- `Neo4j` for medical knowledge graph queries
- `DeepSeek-V3.2` (via SiliconFlow) as the default LLM

## Features

- Streamlit chat interface with:
  - conversation memory
  - latency display
  - dynamic follow-up question suggestions (updated after each turn)
- Multi-tool agent routing:
  - generic QA
  - vector retrieval QA
  - knowledge graph QA
  - fallback web search
- Retrieval-augmented answers from local files (`data/inputs`)
- Graph-augmented answers from Neo4j

## Architecture

1. **UI Layer**: `app.py`  
   Handles chat rendering, session state, dynamic follow-up suggestions, and user interaction.

2. **Service Layer**: `service.py`  
   Rewrites follow-up user messages into standalone questions using recent chat history.

3. **Agent Layer**: `agent.py`  
   Uses a ReAct-style agent with four tools:
   - `generic_func`
   - `retrival_func`
   - `graph_func`
   - `search_func`

4. **Prompt Layer**: `prompt.py`  
   Defines all prompt templates (generic, retrieval, graph, search, summary).

5. **Knowledge Sources**
   - Vector DB: `data/db` (built from `data/inputs`)
   - Graph DB: external Neo4j instance queried via templates in `config.py`

## Requirements

- Python `3.10+` (tested with 3.11)
- Neo4j (optional, but required for graph-based answers)
- Internet access to SiliconFlow API endpoint

## Installation

```bash
pip install -r requirements.txt
```

## Environment Variables

Set values in `.env`:

```env
SILICONFLOW_API_KEY=<your_api_key>
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1

SILICONFLOW_EMBEDDINGS_MODEL=BAAI/bge-large-zh-v1.5
SILICONFLOW_LLM_MODEL=deepseek-ai/DeepSeek-V3.2

TEMPERATURE=0
MAX_TOKENS=1000
VERBOSE=False

NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your_password>
```

Security note:
- Never commit real API keys or database credentials.
- If a key was exposed, rotate it immediately.

## Build / Refresh Vector Knowledge Base

Put your source files into `data/inputs/` (`.txt`, `.csv`, `.pdf`), then run:

```bash
python data_process.py
```

This will chunk documents, embed them, and persist them to `data/db`.

## Run the App

```bash
python -m streamlit run app.py
```

Open the local URL printed in the terminal.

## How to Update Knowledge

### 1) Document Knowledge (RAG)
- Add or edit files in `data/inputs/`
- Re-run `python data_process.py`

### 2) Graph Knowledge (Neo4j)
- Update your Neo4j nodes/relations/properties
- Edit query templates in `config.py` if you add new query patterns

### 3) Prompt / Behavior Rules
- Modify templates in `prompt.py`
- Modify agent tool routing logic in `agent.py` if needed

## Project Structure

```text
.
├── app.py             # Streamlit UI
├── service.py         # Message rewrite / service logic
├── agent.py           # ReAct agent and tools
├── prompt.py          # Prompt templates
├── config.py          # Knowledge graph template mappings
├── utils.py           # Model, embedding, and Neo4j helpers
├── data_process.py    # Build vector DB from local files
├── requirements.txt
└── data/
    ├── inputs/        # Source documents
    └── db/            # Chroma persisted vector store
```

## Troubleshooting

### `ModuleNotFoundError`
Install dependencies in the same Python environment used to run Streamlit:

```bash
which python
which streamlit
pip install -r requirements.txt
```

### No graph answers
- Verify Neo4j is running
- Check `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- Confirm graph data contains expected entities and relationships

### Retrieval quality is weak
- Add better source documents to `data/inputs`
- Rebuild vector DB with `python data_process.py`
- Tune chunking parameters in `data_process.py`

