"""
register_screen.py — User Registration Window
Allows new users to sign up with a username, password,
security question, and choose their security level.
"""
import tkinter as tk
from tkinter import messagebox
from ui.styles import COLORS, FONTS, PAD
from ui.widgets import (StyledLabel, StyledEntry, StyledButton,
                        PasswordEntry, StrengthBar, Separator, StatusMessage)
from auth.hasher import hash_password, check_password_strength
from auth.user_store import register_user, username_exists

# Preset list of security questions to choose from
SECURITY_QUESTIONS = [
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What was the name of your first school?",
    "What is your favorite childhood movie?",
    "What was the make of your first car?",
    "What is the name of your best friend from childhood?",
]


class RegisterScreen(tk.Toplevel):
    """
    Registration window — appears as a popup over the main window.
    Uses tk.Toplevel so it's a separate window on top of the main one.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Create New Account")
        self.geometry("520x700")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])
        self.grab_set()   # Makes this modal — blocks the parent window

        self._selected_question = tk.StringVar(value=SECURITY_QUESTIONS[0])
        self._selected_level = tk.IntVar(value=1)

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """Center the window on screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"520x700+{x}+{y}")

    def _build_ui(self):
        # Scrollable area
        canvas = tk.Canvas(self, bg=COLORS["bg_dark"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._scroll_frame = tk.Frame(canvas, bg=COLORS["bg_dark"])

        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Mousewheel scroll
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        self._build_form(self._scroll_frame)

    def _build_form(self, parent):
        pad = PAD["lg"]

        # Header
        header = tk.Frame(parent, bg=COLORS["bg_card"], pady=PAD["lg"])
        header.pack(fill="x")

        tk.Label(header, text="🔐", font=("Segoe UI Emoji", 32),
                 bg=COLORS["bg_card"]).pack()
        tk.Label(header, text="Create Your Account",
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                 font=FONTS["title"]).pack(pady=(4, 0))
        tk.Label(header, text="Fill in the details below to get started",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack()

        body = tk.Frame(parent, bg=COLORS["bg_dark"], padx=pad, pady=pad)
        body.pack(fill="x")

        # ── USERNAME ─────────────────────────────────────────────────────
        self._make_field_label(body, "USERNAME")
        self._username_entry = StyledEntry(body, width=30)
        self._username_entry.pack(fill="x", pady=(0, PAD["md"]))
        self._username_entry._frame.config(padx=2, pady=2)
        # Fix: repack inner entry wider
        self._username_entry.config(width=38)

        # ── PASSWORD ─────────────────────────────────────────────────────
        self._make_field_label(body, "PASSWORD")
        self._password_entry = PasswordEntry(body, width=36)
        self._password_entry.pack(fill="x")
        self._password_entry.bind_key("<KeyRelease>", self._on_password_change)

        # Strength bar
        self._strength_bar = StrengthBar(body)
        self._strength_bar.pack(fill="x", pady=(4, PAD["md"]))

        # ── CONFIRM PASSWORD ─────────────────────────────────────────────
        self._make_field_label(body, "CONFIRM PASSWORD")
        self._confirm_entry = PasswordEntry(body, width=36)
        self._confirm_entry.pack(fill="x", pady=(0, PAD["md"]))

        # ── SECURITY QUESTION ────────────────────────────────────────────
        Separator(body).pack(fill="x", pady=PAD["sm"])
        self._make_field_label(body, "SECURITY QUESTION (for Level 2 & 3)")

        # Dropdown for question selection
        question_frame = tk.Frame(body, bg=COLORS["bg_input"], relief="flat")
        question_frame.pack(fill="x")

        question_menu = tk.OptionMenu(
            question_frame, self._selected_question, *SECURITY_QUESTIONS
        )
        question_menu.config(
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["bg_input_focus"],
            activeforeground=COLORS["text_primary"],
            font=FONTS["small"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            indicatoron=1,
            width=46,
        )
        question_menu["menu"].config(
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            activebackground=COLORS["primary"],
            font=FONTS["small"],
        )
        question_menu.pack(fill="x", padx=4, pady=4)

        # Answer field
        self._make_field_label(body, "ANSWER TO SECURITY QUESTION")
        self._answer_entry = StyledEntry(body)
        self._answer_entry.pack(fill="x", pady=(0, PAD["md"]))
        self._answer_entry.config(width=38)

        # ── SECURITY LEVEL ───────────────────────────────────────────────
        Separator(body).pack(fill="x", pady=PAD["sm"])
        self._make_field_label(body, "CHOOSE SECURITY LEVEL")

        level_frame = tk.Frame(body, bg=COLORS["bg_dark"])
        level_frame.pack(fill="x", pady=(4, PAD["md"]))

        level_info = [
            (1, "🟢 Level 1 — Basic",   "Password only",                        COLORS["level1"]),
            (2, "🟡 Level 2 — Medium",  "Password + Security Question",          COLORS["level2"]),
            (3, "🔴 Level 3 — Expert",  "Password + Security Q + OTP + CAPTCHA", COLORS["level3"]),
        ]

        for lvl, name, desc, color in level_info:
            self._make_level_radio(level_frame, lvl, name, desc, color)

        # ── STATUS & SUBMIT ──────────────────────────────────────────────
        self._status = StatusMessage(body)
        self._status.pack(fill="x", pady=(PAD["sm"], PAD["xs"]))

        btn = StyledButton(
            body, text="✓  CREATE ACCOUNT",
            command=self._on_register,
            bg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            width=30,
        )
        btn.pack(fill="x", ipady=8, pady=PAD["sm"])

        # Back link
        back_btn = tk.Button(
            body,
            text="← Back to Login",
            command=self.destroy,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_accent"],
            activebackground=COLORS["bg_dark"],
            activeforeground=COLORS["primary"],
            relief="flat",
            font=FONTS["small"],
            cursor="hand2",
            bd=0,
        )
        back_btn.pack(pady=PAD["sm"])

    def _make_field_label(self, parent, text: str):
        tk.Label(
            parent, text=text,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(PAD["xs"], 2))

    def _make_level_radio(self, parent, value: int, name: str, desc: str, color: str):
        frame = tk.Frame(parent, bg=COLORS["bg_card"], pady=8, padx=12,
                         relief="flat", bd=1)
        frame.pack(fill="x", pady=3)

        rb = tk.Radiobutton(
            frame,
            text=name,
            variable=self._selected_level,
            value=value,
            bg=COLORS["bg_card"],
            fg=color,
            activebackground=COLORS["bg_card"],
            selectcolor=COLORS["bg_dark"],
            font=FONTS["heading"],
            cursor="hand2",
        )
        rb.pack(side="left")

        tk.Label(
            frame, text=f"  {desc}",
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
            font=FONTS["small"],
        ).pack(side="left", padx=(8, 0))

    def _on_password_change(self, event=None):
        """Update the strength bar as the user types."""
        password = self._password_entry.get()
        if password:
            score, label, color, feedback = check_password_strength(password)
            self._strength_bar.update_strength(score, label, color, feedback)

    def _on_register(self):
        """Validate inputs and register the user."""
        self._status.clear()

        username = self._username_entry.get().strip()
        password = self._password_entry.get()
        confirm = self._confirm_entry.get()
        answer = self._answer_entry.get().strip()
        question = self._selected_question.get()
        level = self._selected_level.get()

        # ── VALIDATION ──────────────────────────────────────────────────
        if not username:
            self._status.show_error("Username cannot be empty.")
            return
        if len(username) < 3:
            self._status.show_error("Username must be at least 3 characters.")
            return
        if username_exists(username):
            self._status.show_error(f"Username '{username}' is already taken!")
            return
        if not password:
            self._status.show_error("Password cannot be empty.")
            return
        if len(password) < 6:
            self._status.show_error("Password must be at least 6 characters.")
            return
        if password != confirm:
            self._status.show_error("Passwords do not match!")
            return
        if not answer:
            self._status.show_error("Please provide an answer to the security question.")
            return

        # ── HASH & STORE ─────────────────────────────────────────────────
        pwd_hash, pwd_salt = hash_password(password)
        ans_hash, ans_salt = hash_password(answer.lower())  # Store answer lowercase

        success, message = register_user(
            username=username,
            hashed_password=pwd_hash,
            salt=pwd_salt,
            security_question=question,
            security_answer_hash=ans_hash,
            security_answer_salt=ans_salt,
            level=level,
        )

        if success:
            messagebox.showinfo(
                "Account Created!",
                f"✓ Welcome, {username}!\n\n"
                f"Your account has been created with Level {level} security.\n"
                f"You can now log in.",
                parent=self
            )
            self.destroy()
        else:
            self._status.show_error(message)
