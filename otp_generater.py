"""
otp_generator.py — One-Time Password (OTP) Generator
Generates a random 6-digit code for Level 3 authentication.
In a real app, this would be sent via SMS or email — here we simulate it.
"""
import random
import string
import time


# How long (in seconds) the OTP is valid
OTP_EXPIRY_SECONDS = 60

# Store the current active OTP for each session
_active_otps: dict[str, tuple[str, float]] = {}


def generate_otp(session_key: str = "default") -> str:
    """
    Generate a new 6-digit OTP and store it with a timestamp.

    Args:
        session_key: A key to identify this session (e.g. username)

    Returns:
        The 6-digit OTP string
    """
    otp = "".join(random.choices(string.digits, k=6))
    _active_otps[session_key] = (otp, time.time())
    return otp


def verify_otp(session_key: str, user_input: str) -> tuple[bool, str]:
    """
    Verify a user's OTP against the generated one.

    Args:
        session_key: The session key used when generating the OTP
        user_input: What the user typed as their OTP

    Returns:
        (is_valid: bool, message: str)
    """
    if session_key not in _active_otps:
        return False, "No OTP generated. Please request a new one."

    stored_otp, generated_at = _active_otps[session_key]
    elapsed = time.time() - generated_at

    if elapsed > OTP_EXPIRY_SECONDS:
        del _active_otps[session_key]
        return False, f"OTP expired! (Valid for {OTP_EXPIRY_SECONDS} seconds only)"

    if user_input.strip() == stored_otp:
        del _active_otps[session_key]
        return True, "OTP verified successfully!"
    else:
        return False, "Incorrect OTP. Please try again."


def get_otp_time_remaining(session_key: str = "default") -> int:
    """Returns how many seconds remain for a valid OTP (0 if expired/none)."""
    if session_key not in _active_otps:
        return 0
    _, generated_at = _active_otps[session_key]
    remaining = OTP_EXPIRY_SECONDS - (time.time() - generated_at)
    return max(0, int(remaining))
