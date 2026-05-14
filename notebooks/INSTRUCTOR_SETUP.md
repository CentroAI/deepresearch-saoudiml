# Instructor Setup Guide — GitHub Codespaces

This guide explains how to configure GitHub Codespaces so that:
- **Shared keys** (Anthropic, OpenAI, Tavily) are pre-loaded invisibly for all students
- **Students only paste** their personal `LANGSMITH_API_KEY` once per notebook session

---

## 1. Push the `.devcontainer/` folder to your repo

Copy the `.devcontainer/` folder from this zip into the **root** of your repository:

```
deep_research_from_scratch/
├── .devcontainer/
│   ├── devcontainer.json
│   └── setup.sh
├── notebooks/
│   └── session_setup.py   ← drop this into the notebooks/ folder
...
```

Commit and push to `main`.

---

## 2. Set Organization Codespace Secrets (you do this once)

These are the shared model keys students will **never see**.

1. Go to your **GitHub Organization** → `Settings` → `Secrets and variables` → `Codespaces`
2. Click **New organization secret** for each key below:

| Secret name | Value | Repository access |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | your repo only |
| `OPENAI_API_KEY` | `sk-...` | your repo only |

> If you're using a **personal repo** (not an org), go to:
> `Repo Settings` → `Secrets and variables` → `Codespaces` → `New repository secret`

---

## 3. Add the setup cell to each notebook

Open each notebook and **insert a new cell at the very top** (before all other cells).
Paste this code:

```python
# Run this cell first — sets up all API keys for the session
%run session_setup.py
```

Or copy the full contents of `notebooks/session_setup.py` directly into the cell.

---

## 4. Share this link with students (before the session)

Send students this URL (replace `ORG` and `REPO`):

```
https://codespaces.new/ORG/REPO?quickstart=1
```

Or tell them:
1. Go to the repo on GitHub
2. Click the green **Code** button → **Codespaces** tab → **Create codespace on main**

> ⏱️ First launch takes ~3 minutes while the container builds and dependencies install.
> Tell students to launch it **before** the session starts.

---

## 5. What students see when they open a notebook

1. Codespace opens with VS Code in the browser
2. They open `notebooks/1_scoping.ipynb`
3. They run the first cell — two prompts appear in sequence:

```
🔑 [1/2] Paste your LANGSMITH_API_KEY and press Enter
         (get yours free at https://smith.langchain.com → Settings → API Keys)
         >

🔑 [2/2] Paste your TAVILY_API_KEY and press Enter
         (get yours free at https://app.tavily.com → API Keys)
         >
```

4. They paste their key (one time per notebook session)
5. All shared keys are verified and shown as ✅

That's it — they're ready to run the rest of the notebook.

---

## Rate limit strategy

With 30-40 students, split them into groups and assign one key per group.
Create 4 sets of org secrets with a group suffix, then set the right one
in `devcontainer.json` per group branch (or just use 4 separate repos forked
from the main one):

| Group | Branch / Repo fork | Keys used |
|---|---|---|
| A (students 1–10) | `group-a` | `ANTHROPIC_API_KEY_A`, `OPENAI_API_KEY_A` |
| B (students 11–20) | `group-b` | `ANTHROPIC_API_KEY_B`, `OPENAI_API_KEY_B` |
| C (students 21–30) | `group-c` | `ANTHROPIC_API_KEY_C`, `OPENAI_API_KEY_C` |
| D (students 31–40) | `group-d` | `ANTHROPIC_API_KEY_D`, `OPENAI_API_KEY_D` |

Each group's key has its own rate limit bucket — effectively 4× your TPM.

---

## Monitoring during the session

- Open **LangSmith** → your project → filter by `LANGSMITH_API_KEY`
- Each student's traces are tagged with their personal key so you can see who's running what in real time
- If you see 429 errors, the `max_retries=5` in LangChain will handle most of them silently

---

## Cost estimate (40 students, full session)

| Model | Est. tokens/student | Total | Approx cost |
|---|---|---|---|
| `claude-sonnet-4` | ~50K | 2M | ~$15 |
| `gpt-4.1` | ~80K | 3.2M | ~$13 |
| `gpt-4.1-mini` | ~100K | 4M | ~$0.60 |
| **Total** | | | **~$29** |

Actual cost depends on how many heavy research runs students trigger.
