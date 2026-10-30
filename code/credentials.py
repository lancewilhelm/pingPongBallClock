#!/usr/bin/env python3
"""Change the local web login from the Raspberry Pi terminal."""
import getpass
import json
import sys

import storage


def main():
    path = storage.STATE_DIR / "auth.json"
    try:
        existing = storage.read_json(path)
        if not isinstance(existing, dict) or not isinstance(existing.get("username"), str):
            raise ValueError("Invalid credentials file")
        current_username = existing["username"]
    except FileNotFoundError:
        current_username = "admin"
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Cannot read credentials: {error}", file=sys.stderr)
        return 1

    try:
        username = input(f"Username [{current_username}]: ").strip() or current_username
        if not username or ":" in username or any(ord(char) < 32 or ord(char) == 127 for char in username):
            print("Username must be nonempty and cannot contain a colon or control characters.", file=sys.stderr)
            return 1
        password = getpass.getpass("New password: ")
        confirmation = getpass.getpass("Confirm password: ")
    except (EOFError, KeyboardInterrupt):
        print("\nCredentials were not changed.", file=sys.stderr)
        return 1

    if not password:
        print("Password cannot be empty.", file=sys.stderr)
        return 1
    if password != confirmation:
        print("Passwords do not match. Credentials were not changed.", file=sys.stderr)
        return 1

    try:
        storage.atomic_json(path, {"username": username, "password": password})
    except OSError as error:
        print(f"Cannot save credentials: {error}", file=sys.stderr)
        return 1
    print("Credentials updated. Sign in again in your browser.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
