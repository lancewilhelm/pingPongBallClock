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
# systemd unit values and ExecStart have their own escaping rules. Restrict
# checkout paths so the generated unit cannot be parsed as multiple arguments
# or contain specifier expansions.
if [[ ! "$PROJECT_DIR" =~ ^/[a-zA-Z0-9_./-]+$ ]]; then
    echo "Checkout path must contain only ASCII letters, digits, /, ., _, and -: $PROJECT_DIR" >&2
    exit 1
fi

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

echo "Preparing local credentials..."
AUTH_CREDENTIALS="$(python3 - "$CODE_DIR/.local/auth.json" <<'PY'
import json
import os
from pathlib import Path
import secrets
import sys
import tempfile

path = Path(sys.argv[1])
path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
os.chmod(path.parent, 0o700)
credentials = {"username": "admin", "password": secrets.token_urlsafe(32)}
fd, temp_name = tempfile.mkstemp(prefix=".auth-", dir=path.parent)
try:
    with os.fdopen(fd, "w") as file:
        json.dump(credentials, file)
        file.write("\n")
    try:
        os.link(temp_name, path)
    except FileExistsError:
        os.chmod(path, 0o600)
    else:
        print("Username: " + credentials["username"])
        print("Password: " + credentials["password"])
finally:
    os.unlink(temp_name)
PY
)"

echo "Installing and starting $SERVICE_NAME..."
sed \
    -e "s|__WORKING_DIRECTORY__|$(escape_sed "$CODE_DIR")|g" \
    -e "s|__PYTHON_EXECUTABLE__|$(escape_sed "$VENV_DIR/bin/python")|g" \
    "$UNIT_FILE" > "$GENERATED_UNIT"
sudo install -m 0644 "$GENERATED_UNIT" "/etc/systemd/system/$SERVICE_NAME"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo
if [[ -n "$AUTH_CREDENTIALS" ]]; then
    echo "Browser login credentials:"
    printf '%s\n' "$AUTH_CREDENTIALS"
    echo "Credentials are also stored in $CODE_DIR/.local/auth.json."
    echo
fi
echo "Check the service status and logs with:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  journalctl -u $SERVICE_NAME -f"
