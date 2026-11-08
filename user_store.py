"""
user_store.py — User Database (JSON-based)
Handles saving and loading user data from a local JSON file.
Think of this as our simple "database" for the project!
"""
import json
import os

# Path to where we store user data
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "users.json")


def _load_all_users() -> dict:
    """Load all users from the JSON file."""
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save_all_users(users: dict) -> None:
    """Save all users back to the JSON file."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)


def register_user(username: str, hashed_password: str, salt: str,
                  security_question: str, security_answer_hash: str,
                  security_answer_salt: str, level: int) -> tuple[bool, str]:
    """
    Register a new user and save their data.

    Args:
        username: Chosen username
        hashed_password: SHA-256 hashed password
        salt: Password salt
        security_question: The security question text
        security_answer_hash: Hashed answer to the security question
        security_answer_salt: Salt for the security answer
        level: Which security level (1, 2, or 3)

    Returns:
        (success: bool, message: str)
    """
    users = _load_all_users()

    if username.lower() in users:
        return False, f"Username '{username}' already exists. Please choose another."

    users[username.lower()] = {
        "username": username,
        "password_hash": hashed_password,
        "password_salt": salt,
        "security_question": security_question,
        "security_answer_hash": security_answer_hash,
        "security_answer_salt": security_answer_salt,
        "level": level,
        "failed_attempts": 0,
        "locked_until": None
    }

    _save_all_users(users)
    return True, f"User '{username}' registered successfully!"


def get_user(username: str) -> dict | None:
    """
    Retrieve a user's data by username.

    Returns:
        The user dictionary if found, None otherwise.
    """
    users = _load_all_users()
    return users.get(username.lower(), None)


def update_failed_attempts(username: str, count: int, locked_until=None) -> None:
    """Update the failed login attempt count for a user."""
    users = _load_all_users()
    if username.lower() in users:
        users[username.lower()]["failed_attempts"] = count
        users[username.lower()]["locked_until"] = locked_until
        _save_all_users(users)


def reset_failed_attempts(username: str) -> None:
    """Reset failed attempts after a successful login."""
    users = _load_all_users()
    if username.lower() in users:
        users[username.lower()]["failed_attempts"] = 0
        users[username.lower()]["locked_until"] = None
        _save_all_users(users)


def username_exists(username: str) -> bool:
    """Check if a username already exists."""
    users = _load_all_users()
    return username.lower() in users
