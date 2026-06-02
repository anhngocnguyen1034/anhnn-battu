# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> FOR-BAZI (玄冥 / Cyber-Bazi) is a professional Chinese Bazi (八字) fortune-telling system:
> a Python calculation engine + FastAPI backend + ReAct AI agent, a React/Tauri frontend, and
> an MCP server. UI text and most code comments are in Chinese.

## Commands

All Python commands run **from the project root** — packages (`engine`, `tools`, `agent`,
`backend`, etc.) are imported as top-level modules, and the root is injected onto `sys.path`
by `tests/conftest.py` and `backend/main.py`. Running from a subdirectory breaks imports.

```bash
# Install
pip install -r requirements.txt          # engine + streamlit + mcp
pip install -r backend/requirements.txt   # fastapi + anthropic + chromadb + sentence-transformers
cd frontend && npm install

# Backend (port 8000; serves frontend/dist/ in prod, /docs for OpenAPI)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend dev (port 5173, proxies /api → :8000)
cd frontend && npm run dev
cd frontend && npm run build      # tsc -b && vite build → frontend/dist/
cd frontend && npm run lint       # eslint

# Tests (pytest.ini sets asyncio_mode=auto — async tests need no decorator)
pytest -q                                              # full suite
pytest tests/test_agent_service.py -q                  # single file
pytest tests/test_engine.py::test_name -q              # single test

# MCP server (Chinese-calendar / Bazi tools for Claude Desktop etc.)
python -m mcp_server.server

# Legacy Streamlit UI (port 8501) — superseded by the React frontend
streamlit run streamlit_app.py

# Desktop EXE
cd frontend && npx tauri build    # Tauri v2 + WebView2; bundles a backend exe via launcher.py / backend.spec
```

## Architecture

Request flow: **React frontend → FastAPI routes (`backend/api/`) → services (`backend/services/`)
→ Python core (`engine/`, `tools/`, `agent/`) → LLM + ChromaDB**. See `docs/ARCHITECTURE.md`
for full Mermaid diagrams; the points below are the ones that bite if you don't know them.

### Two chart-data formats and the adapters between them — the central gotcha

The engine and the frontend speak **different shapes for the same chart**, and there are two
adapters that must stay in sync:

- **Engine / "flat" format** — parallel arrays + flat keys: `pillars: ["壬午",...]`,
  `tg_gan`, `tg_zhi`, `nayin`, `day_master`, `minggong`, `taiyuan`, `wuxing: {...}`, `dayun: [...]`.
  This is what `engine/bazi_engine.py` emits and what every tool in `tools/bazi_tools.py`
  expects as its `bazi_data` argument.
- **Frontend `BaziReading`** — nested objects + camelCase-ish keys: `chart.year_pillar.{stem,branch}`,
  `element_balance`, `ten_gods`, `ming_gong`, `pillar_annotations`, etc. (`frontend/src/types/bazi.ts`).

Conversions:
- **Forward (flat → nested)**: `frontend/src/lib/response-adapter.ts` → `adaptChartResponse()`,
  called after `POST /api/v1/chart`.
- **Backward (nested → flat)**: `backend/services/agent_service.py` → `_normalize_chart_data()`,
  called at the top of `/api/v1/chat/stream` before anything touches the agent or tools.

If you add a chart field, you almost always have to touch **both** adapters or the agent will
silently see missing data.

### AI agent (ReAct + provider abstraction)

- `agent/react_agent.py` runs a ReAct loop (**max 8 steps**): call LLM → if `tool_calls`,
  `dispatch_tool()` and append results → repeat → final answer (+ a ganzhi fact-check pass).
- `agent/api_adapter.py` hides the OpenAI-vs-Anthropic SDK split. Routing is decided **purely
  by provider name** via the `ANTHROPIC_PROVIDERS` set (`{"MiMo", "GLM", "Zhipu", "智谱 GLM",
  "Anthropic (兼容)"}`). To onboard a new Anthropic-Messages-compatible provider, add its name
  to that set — nothing else. Everything not in the set goes through the OpenAI SDK path.
- API keys / base_url / model come **per-request** from the chat payload (user-supplied in
  Settings), falling back to `backend/config.py` defaults.

### Tools (14, in `tools/bazi_tools.py`)

`TOOL_SCHEMAS` (OpenAI function-calling schemas), `TOOL_REGISTRY` (name → fn), and
`dispatch_tool(name, args, bazi_data)` are the public surface. Tools split into: calculation
(`calculate_wuxing_power`, `analyze_geju`, `get_annual_fortune`, `get_dayun_stage`, ...),
classical-text lookup (穷通宝鉴 / 滴天髓 / 子平真诠 / 三命通会, plus generic `query_classical_text`),
and RAG/aux (`rag_retrieve`, `query_xing_chong_he_hai`, `explain_shensha`, `fact_check_ganzhi`).

**Why so many tools exist:** LLMs reliably miscompute ganzhi/calendar facts, so all
calendar-derived values come from `lunar-python` (the single source of truth for pillars,
nayin, dayun, etc.), and `fact_check_ganzhi` exists to catch the model hallucinating them.
Prefer extending a tool over having the model "do the math."

### Classical texts & RAG

5 classical texts live as JSON in `data/classical_texts/` (exact lookup via
`data/text_service.py`) and are also indexed into **ChromaDB** for semantic search
(`data/rag_service.py`, used by `scholar_agent.py` / the `rag_retrieve` tool). ChromaDB +
`sentence-transformers` are heavy deps; RAG-dependent code/tests won't run without them.

## Configuration

`backend/config.py` uses pydantic-settings. **All env vars are prefixed `BAZI_`** and read
from a root `.env` (see `.env.example`). Defaults point at **MiniMax** (`BAZI_OPENAI_BASE_URL=
https://api.minimaxi.com/v1`, model `MiniMax-M2.7`), not OpenAI proper — the README's GPT-4o
example is illustrative, not the default. `BAZI_ANTHROPIC_*` defaults to a GLM/MiniMax
Anthropic-compatible endpoint.

## CI

`.github/workflows/ci.yml` has two jobs. **`lint-compile` is the real gate**: `compileall`
over all source + `ruff check --select E9,F63,F7,F82` (hard errors only — syntax / undefined
names, no style rules) + an import smoke test. The full `pytest` job is **best-effort**
(`continue-on-error: true`) because the heavy deps (lunar-python, chromadb, torch, ...) are
slow/flaky to install in CI. Don't rely on CI to run the suite — run `pytest -q` locally.
