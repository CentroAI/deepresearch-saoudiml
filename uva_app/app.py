"""
UVa Researcher - Web Interface
University of Valladolid Deep Research Agent
"""

import asyncio
import json
import logging
import os
import queue
import sys
import threading
import uuid

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, send_from_directory, session
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()

PROJECT_ROOT   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH       = os.path.join(PROJECT_ROOT, "src")
NOTEBOOKS_PATH = os.path.join(PROJECT_ROOT, "notebooks")
sys.path.insert(0, SRC_PATH)
sys.path.insert(0, NOTEBOOKS_PATH)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("uva")

# Serve static files AND templates from the same folder
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=TEMPLATES_DIR, static_url_path="/static")
app.secret_key = "uva-researcher-2026"

_agent        = None
_checkpointer = None
_agent_lock   = threading.Lock()

def get_agent():
    global _agent, _checkpointer
    with _agent_lock:
        if _agent is None:
            log.info("Loading agent...")
            from deep_research_from_scratch.research_agent_full import deep_researcher_builder
            _checkpointer = InMemorySaver()
            _agent = deep_researcher_builder.compile(checkpointer=_checkpointer)
            log.info("Agent loaded OK")
    return _agent

@app.route("/")
def index():
    if "thread_id" not in session:
        session["thread_id"] = str(uuid.uuid4())
    return render_template("index.html")

@app.route("/logo")
def logo():
    """Serve the UVa logo from the templates folder."""
    return send_from_directory(TEMPLATES_DIR, "image.png", mimetype="image/png")

@app.route("/new_session", methods=["POST"])
def new_session():
    session["thread_id"] = str(uuid.uuid4())
    return jsonify({"status": "ok"})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data or {}).get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    thread_id = session.get("thread_id") or str(uuid.uuid4())
    session["thread_id"] = thread_id

    q = queue.Queue()
    SENTINEL = object()

    def run_agent():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_stream_agent(message, thread_id, q))
        except Exception as exc:
            log.exception("Agent error")
            q.put(f"data: {json.dumps({'type': 'error', 'text': str(exc)})}\n\n")
        finally:
            q.put(SENTINEL)
            loop.close()

    threading.Thread(target=run_agent, daemon=True).start()

    def generate():
        while True:
            item = q.get()
            if item is SENTINEL:
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                break
            yield item

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── Which LLM nodes belong to which phase ────────────────────────────────────
# Only stream tokens from these specific named nodes; ignore everything else
# (tool calls, internal chains, compression steps, etc.)
STREAMING_NODES = {
    # node-name               → (phase_key,    display_label,              bubble_title)
    "clarify_with_user":      ("clarifying",   "Clarifying your request",  "Scope Check"),
    "write_research_brief":   ("briefing",     "Writing research brief",   "Research Brief"),
    "final_report_generation":("writing",      "Writing final report",     "Final Report"),
    # Supervisor high-level decision messages only (not sub-researcher noise)
    "supervisor":             ("researching",  "Coordinating research",    "Research Coordinator"),
}

async def _stream_agent(message: str, thread_id: str, q: queue.Queue):
    agent  = get_agent()
    config = {"configurable": {"thread_id": thread_id, "recursion_limit": 50}}

    # Track which node is currently streaming so we can open/close bubbles correctly
    current_node = None

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=message)]},
        config=config,
        version="v2",
    ):
        kind = event.get("event", "")
        # The tags list tells us which graph node we're inside
        tags  = event.get("tags", [])
        name  = event.get("name", "")

        # ── Phase start: open a new bubble ───────────────────────────────────
        if kind == "on_chain_start" and name in STREAMING_NODES:
            phase_key, label, title = STREAMING_NODES[name]
            current_node = name
            payload = json.dumps({
                "type":  "phase_start",
                "phase": phase_key,
                "label": label,
                "title": title,
                "node":  name,
            })
            q.put(f"data: {payload}\n\n")

        # ── Phase end: close/finalize the bubble ──────────────────────────────
        elif kind == "on_chain_end" and name in STREAMING_NODES:
            if current_node == name:
                q.put(f"data: {json.dumps({'type': 'phase_end', 'node': name})}\n\n")
                current_node = None

        # ── Token streaming: only for whitelisted nodes ───────────────────────
        elif kind == "on_chat_model_stream":
            # Only emit tokens if we're inside a node we care about
            if current_node not in STREAMING_NODES:
                continue
            # Also skip if this is a sub-researcher (compress / tool nodes)
            # by checking that none of the tags suggest a nested researcher graph
            if any("researcher" in t.lower() for t in tags if "supervisor" not in t.lower()):
                continue

            chunk = event.get("data", {}).get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                text = chunk.content
                if isinstance(text, str) and text:
                    payload = json.dumps({"type": "token", "text": text, "node": current_node})
                    q.put(f"data: {payload}\n\n")

        # ── Supervisor finished → tell UI research phase ended ────────────────
        elif kind == "on_chain_end" and name == "supervisor_subgraph":
            q.put(f"data: {json.dumps({'type': 'research_complete'})}\n\n")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("\n" + "=" * 62)
    print("  UVa Researcher  -  Universidad de Valladolid")
    print("  http://localhost:5000")
    print("=" * 62 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True, use_reloader=False)
