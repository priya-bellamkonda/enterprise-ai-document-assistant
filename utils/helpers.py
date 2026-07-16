import json
import os
import re
import bcrypt


USERS_FILE = "data/users.json"


def load_users():
    """Loads the users database (username -> hashed password)."""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    """Saves the users database."""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    """Turns a plain password into a secure hash for storage."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed):
    """Checks if a plain password matches the stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))



def register_user(username, password):
    """
    Creates a new user account.
    Returns (success: bool, message: str)
    """
    users = load_users()

    username = username.strip()   # keep original capitalization
    password = password.strip()

    if not username or not password:
        return False, "Username and password cannot be empty."

    # Block usernames that only differ by capitalization (avoids folder conflicts)
    for existing_username in users:
        if existing_username.lower() == username.lower():
            return False, "That username is already taken (usernames are not case-sensitive for uniqueness, even though login requires exact capitalization)."

    if len(password) < 6:
        return False, "Password must be at least 6 characters long (e.g. 'Blue@2026')."

    if password.lower() == username.lower():
        return False, "Password cannot be the same as your username."

    if password.isdigit():
        return False, "Password cannot be only numbers (e.g. use 'Sunny#123' instead of '123456')."

    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter (e.g. 'Tiger$99')."

    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter (e.g. 'Ocean#42')."

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character, like ! @ # $ % & * (e.g. 'Winter@25')."

    users[username] = hash_password(password)
    save_users(users)
    return True, "Account created successfully!"


def authenticate_user(username, password):
    """
    Checks login credentials. Username must match exact capitalization.
    Returns (success: bool, message: str)
    """
    users = load_users()

    username = username.strip()   # no lowercasing — exact match required

    if username not in users:
        return False, "Username not found."

    if not verify_password(password, users[username]):
        return False, "Incorrect password."

    return True, "Login successful!"