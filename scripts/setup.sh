#!/usr/bin/env bash
# One-command idempotent environment setup script for Linux / macOS.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Setting up Fractional Approval Agent (Linux/macOS) ==="

# 1. Verify Python availability (Hyperon 0.2.10 requires Python 3.10 - 3.12)
PYTHON_BIN=""
for candidate in python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" &>/dev/null; then
        minor=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "99")
        if [ "$minor" -le 12 ] && [ "$minor" -ge 10 ]; then
            PYTHON_BIN="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python 3.10 - 3.12 is required for Hyperon 0.2.10. Please install Python 3.12." >&2
    exit 1
fi

# 2. Create virtual environment if missing
VENV_DIR="${ROOT_DIR}/.venv"
VENV_PYTHON="${VENV_DIR}/bin/python"

if [ ! -f "${VENV_PYTHON}" ]; then
    echo "[1/4] Creating virtual environment (.venv) using ${PYTHON_BIN}..."
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
    echo "[1/4] Virtual environment already exists (.venv)."
fi

# 3. Install pinned dependencies
echo "[2/4] Installing pinned dependencies from requirements.txt..."
"${VENV_DIR}/bin/pip" install -r "${ROOT_DIR}/requirements.txt"

# 4. Copy .env.example to .env if missing
if [ ! -f "${ROOT_DIR}/.env" ]; then
    echo "Copying .env.example to .env (offline mode default)..."
    cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
fi

# 5. Run test suite
echo "[3/4] Running pytest suite to verify installation..."
"${VENV_DIR}/bin/pytest"

# 6. Print next steps
echo ""
echo "[4/4] Setup complete! All systems operational."
echo ""
echo "--- Next Steps ---"
echo "1. Activate virtual environment:"
echo "   source .venv/bin/activate"
echo "2. Run test suite:"
echo "   pytest -v"
echo "3. Launch Streamlit Proof Viewer:"
echo "   streamlit run app/streamlit_app.py"
echo "------------------"
