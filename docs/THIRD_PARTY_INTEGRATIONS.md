# Third-Party Integrations

Per the surgical integration brief, this table records what was reviewed, what (if anything) was adapted, and under what license.

| Source | Reference | Used? | What was adapted | License | Notes |
|---|---|---:|---|---|---|
| TauricResearch/TradingAgents | `tradingagents/agents/utils/structured.py` @ `8e94132c912858eef1ee5f8478de5afa5410a230` | Yes | Concept only: a typed-schema call → validate → fallback boundary for LLM output. No source code copied — reimplemented natively using `google-genai`'s `response_schema`/`response_mime_type` and Groq's `response_format={"type":"json_object"}`, both already available in this repo's installed SDK versions. | Verify current TradingAgents repo LICENSE before any future direct code reuse; none of their code was copied here, so no attribution obligation was triggered. | The LangGraph multi-agent graph, analyst/researcher/trader/risk hierarchy, and full memory system were explicitly not touched. |
| HKUDS/Vibe-Trading | `agent/src/core/state.py` @ `305a6705dc318234a8d097623366d0e560e4f069`, `agent/src/tools/backtest_tool.py` @ `59681937af6cde767062654d875ed157048a8290` | Yes | Concept only: run-lifecycle states (created/running/succeeded/failed/cancelled), evidence-gated point-in-time correctness, safe run-directory path resolution, atomic state writes. Independently reimplemented for BreakoutScan's own scan/pattern DSL rather than ported. | MIT (per Vibe-Trading's own repo at the reviewed SHA). | The 74-tool MCP server, swarm system, Alpha Zoo, broker connectors, market-data adapters, and full backtest (P&L/equity-curve) engine were explicitly not touched. |

**Note on this repository's own license**: `README.md` states "License: MIT — see LICENSE for details," but no `LICENSE` file actually exists in the repository root as of this integration. This is a pre-existing discrepancy, unrelated to this work, flagged here rather than silently fixed.

No runtime dependency on either external repository was added — both are reference implementations only, verified via the dependency audit in `docs/INTEGRATION_REPORT.md`.
