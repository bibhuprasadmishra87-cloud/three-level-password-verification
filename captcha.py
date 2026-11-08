"""
captcha.py — Simple Text-Based CAPTCHA Generator
Generates a random 6-character alphanumeric CAPTCHA string.
For Level 3 authentication — proves the user is human!

CAPTCHA = Completely Automated Public Turing test to tell Computers and Humans Apart
"""
import random
import string
import tkinter as tk
from tkinter import font as tkfont


def generate_captcha_text(length: int = 6) -> str:
    """
    Generate a random CAPTCHA string using letters and digits.
    We deliberately avoid easily confused characters like 0/O, 1/l/I.

    Args:
        length: Number of characters in the CAPTCHA (default 6)

    Returns:
        Random CAPTCHA string
    """
    # Avoid confusing characters for better UX
    safe_chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789"
    return "".join(random.choices(safe_chars, k=length))


def verify_captcha(user_input: str, correct_captcha: str) -> bool:
    """
    Verify if the user's CAPTCHA input matches the generated one.
    Case-sensitive comparison!
    """
    return user_input.strip() == correct_captcha


def draw_captcha_on_canvas(canvas: tk.Canvas, captcha_text: str,
                            width: int = 220, height: int = 60) -> None:
    """
    Draw a styled CAPTCHA onto a Tkinter Canvas widget.
    Adds visual noise (lines, dots) to make it harder for bots.

    Args:
        canvas: The tkinter Canvas to draw on
        captcha_text: The CAPTCHA string to display
        width, height: Canvas dimensions
    """
    canvas.delete("all")

    # Background gradient simulation with rectangles
    bg_colors = ["#1a1a2e", "#16213e", "#0f3460"]
    for i, color in enumerate(bg_colors):
        canvas.create_rectangle(
            i * (width // 3), 0,
            (i + 1) * (width // 3), height,
            fill=color, outline=""
        )

    # Add random noise lines (makes it harder for bots to read)
    for _ in range(6):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        noise_color = random.choice(["#334155", "#475569", "#64748b"])
        canvas.create_line(x1, y1, x2, y2, fill=noise_color, width=1)

    # Add random noise dots
    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        dot_color = random.choice(["#4f46e5", "#7c3aed", "#2563eb", "#0891b2"])
        canvas.create_oval(x-2, y-2, x+2, y+2, fill=dot_color, outline="")

    # Draw each character with slight rotation simulation (offset + tilt)
    colors = ["#60a5fa", "#a78bfa", "#f472b6", "#34d399", "#fbbf24", "#fb923c"]
    char_width = width // (len(captcha_text) + 1)

    for i, char in enumerate(captcha_text):
        x = char_width * (i + 0.8) + random.randint(-3, 3)
        y = height // 2 + random.randint(-8, 8)
        color = colors[i % len(colors)]
        size = random.randint(18, 24)

        canvas.create_text(
            x, y,
            text=char,
            fill=color,
            font=("Courier New", size, "bold"),
            angle=random.randint(-20, 20)
        )
