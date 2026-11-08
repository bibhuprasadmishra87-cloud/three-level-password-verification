"""
hasher.py — Password Hashing Utilities
Uses SHA-256 from Python's built-in hashlib module.
No external libraries needed!
"""
import hashlib
import os


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """
    Hash a password using SHA-256 with a random salt.

    What is a salt?
    A salt is a random string added to the password before hashing.
    This makes sure even if two users have the same password,
    their stored hashes will be different — extra security!

    Args:
        password: The plain-text password from the user
        salt: Optional existing salt (used when verifying login)

    Returns:
        A tuple of (hashed_password, salt)
    """
    if salt is None:
        # Generate a random 16-byte salt and convert to hex string
        salt = os.urandom(16).hex()

    # Combine password + salt, then hash with SHA-256
    salted = password + salt
    hashed = hashlib.sha256(salted.encode("utf-8")).hexdigest()

    return hashed, salt


def verify_password(input_password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify if the entered password matches the stored hash.

    Args:
        input_password: Password typed by the user
        stored_hash: The hash stored in our JSON database
        salt: The salt stored alongside the hash

    Returns:
        True if password is correct, False otherwise
    """
    # Hash the input password with the SAME salt used during registration
    computed_hash, _ = hash_password(input_password, salt)
    # Compare — this is a secure comparison
    return computed_hash == stored_hash


def check_password_strength(password: str) -> tuple[int, str, str]:
    """
    Check the strength of a password and return a score + feedback.

    Scoring:
        0-1: Weak
        2-3: Medium
        4-5: Strong

    Returns:
        (score, label, color)
    """
    score = 0
    tips = []

    if len(password) >= 8:
        score += 1
    else:
        tips.append("at least 8 characters")

    if any(c.isupper() for c in password):
        score += 1
    else:
        tips.append("an uppercase letter")

    if any(c.islower() for c in password):
        score += 1
    else:
        tips.append("a lowercase letter")

    if any(c.isdigit() for c in password):
        score += 1
    else:
        tips.append("a number")

    if any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        score += 1
    else:
        tips.append("a special character (!@#$...)")

    if score <= 1:
        label = "Weak"
        color = "#FF4757"       # Red
    elif score <= 3:
        label = "Medium"
        color = "#FFA502"       # Orange/Yellow
    else:
        label = "Strong"
        color = "#2ED573"       # Green

    feedback = "Add: " + ", ".join(tips) if tips else "Great password! ✓"
    return score, label, color, feedback
