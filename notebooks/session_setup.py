"""Session setup — run this cell first in every notebook."""

# ruff: noqa: T201
import os
from pathlib import Path

from dotenv import load_dotenv, set_key

# ── Load .env (won't overwrite vars already in the environment) ────────────────
load_dotenv(dotenv_path=Path("../.env"), override=False)
load_dotenv(dotenv_path=Path(".env"), override=False)

# ── Find .env file location ────────────────────────────────────────────────────
_env_file = None
for _candidate in [Path("../.env"), Path(".env")]:
    if _candidate.exists():
        _env_file = _candidate
        break

# ── Persist shared keys from container env into .env ──────────────────────────
# GitHub Codespace Secrets are injected as env vars at container start.
# Writing them to .env ensures load_dotenv() in notebook cells also picks them up.
for _shared_key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
    _val = os.environ.get(_shared_key, "")
    if _val and _env_file:
        set_key(str(_env_file), _shared_key, _val)


def _set_student_key(env_var: str, prompt: str) -> None:
    """Prompt the student for a key, set it in the environment, and persist to .env."""
    if os.getenv(env_var):
        print(f"✅ {env_var} already set — skipping.")
        return
    value = input(prompt).strip()
    if value:
        os.environ[env_var] = value
        if _env_file:
            set_key(str(_env_file), env_var, value)
        print(f"✅ {env_var} set for this session.")
    else:
        print(f"⚠️  {env_var} left blank.")


print()
_set_student_key(
    "LANGSMITH_API_KEY",
    "🔑 [1/2] Paste your LANGSMITH_API_KEY and press Enter\n"
    "        (get yours free at https://smith.langchain.com → Settings → API Keys)\n"
    "        > ",
)
print()
_set_student_key(
    "TAVILY_API_KEY",
    "🔑 [2/2] Paste your TAVILY_API_KEY and press Enter\n"
    "        (get yours free at https://app.tavily.com → API Keys)\n"
    "        > ",
)

# ── Verify all keys ────────────────────────────────────────────────────────────
_all_keys = {
    "ANTHROPIC_API_KEY": "Claude models        (instructor)",
    "OPENAI_API_KEY":    "GPT-4.1 models       (instructor)",
    "LANGSMITH_API_KEY": "LangSmith tracing    (yours)",
    "TAVILY_API_KEY":    "Tavily web search    (yours)",
}

print("\n── Key status ────────────────────────────────────────────────────────")
_all_ok = True
for _key, _label in _all_keys.items():
    _val = os.getenv(_key, "")
    if _val:
        print(f"  ✅  {_key:<22}  {_label}")
    else:
        _all_ok = False
        _hint = "← contact the instructor" if "instructor" in _label else "← paste above"
        print(f"  ❌  {_key:<22}  {_label}  {_hint}")

print()
if _all_ok:
    print("🚀 All keys present — you're ready to go!\n")
else:
    print("⚠️  Some keys are missing. See hints above.\n")
