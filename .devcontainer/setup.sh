#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "  Deep Research From Scratch — Setup"
echo "=========================================="
echo ""

WORKDIR=/workspaces/deep-research-from-scratch
VENV="$WORKDIR/.venv"

# ── 1. Install uv ──────────────────────────────────────────────────────────────
echo "📦 Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
uv --version

# ── 2. Create virtual environment ─────────────────────────────────────────────
echo ""
echo "🐍 Creating virtual environment..."
cd "$WORKDIR"
uv venv "$VENV" --python 3.11 --clear
echo "✅ venv created at $VENV"

# ── 3. Install project dependencies into the venv ─────────────────────────────
echo ""
echo "📚 Installing project dependencies..."
uv pip install --python "$VENV/bin/python" -e ".[dev]"
uv pip install --python "$VENV/bin/python" ipykernel
echo "✅ Packages installed."

# ── 4. Register Jupyter kernel ─────────────────────────────────────────────────
echo ""
echo "🔧 Registering Jupyter kernel..."
"$VENV/bin/python" -m ipykernel install --user \
    --name deep-research \
    --display-name "Python (deep-research)"
echo "✅ Kernel registered."

# ── 5. Write the shared .env ───────────────────────────────────────────────────
echo ""
echo "🔑 Writing .env file..."
cat > "$WORKDIR/.env" << EOF
# Shared keys (instructor-provided via GitHub Codespace Secrets)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}

# Student keys — filled in by each student in the first notebook cell
LANGSMITH_API_KEY=
TAVILY_API_KEY=

# LangChain tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=deep-research-course
EOF
echo "✅ .env written."

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "  Open notebooks/1_scoping.ipynb to start."
echo "=========================================="
echo ""
