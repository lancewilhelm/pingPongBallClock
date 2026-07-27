#!/usr/bin/env bash

# Install the application without modifying Raspberry Pi OS's system Python.
# Run this as the regular account that owns the checkout, not with sudo.
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
    echo "Run this script as your regular user: ./setup.sh (it will prompt for sudo)." >&2
    exit 1
fi

CODE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$CODE_DIR/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
SERVICE_NAME="pingpongballclock.service"
UNIT_FILE="$CODE_DIR/pingpongballclock.service.in"
GENERATED_UNIT="$(mktemp)"

cleanup() {
    rm -f "$GENERATED_UNIT"
}
trap cleanup EXIT

escape_sed() {
    printf '%s' "$1" | sed -e 's/[\\/&|]/\\&/g'
}

echo "Installing operating-system build prerequisites..."
sudo apt-get update
sudo apt-get install --yes python3-full python3-venv python3-dev build-essential

echo "Creating project virtual environment..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$CODE_DIR/requirements.txt"

echo "Installing and starting $SERVICE_NAME..."
sed \
    -e "s|__WORKING_DIRECTORY__|$(escape_sed "$CODE_DIR")|g" \
    -e "s|__PYTHON_EXECUTABLE__|$(escape_sed "$VENV_DIR/bin/python")|g" \
    "$UNIT_FILE" > "$GENERATED_UNIT"
sudo install -m 0644 "$GENERATED_UNIT" "/etc/systemd/system/$SERVICE_NAME"
sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"

echo
echo "Ping Pong Ball Clock is running. Check it with:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  journalctl -u $SERVICE_NAME -f"
