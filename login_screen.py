"""
login_screen.py — Main Login Window
The first screen users see. They enter username and are shown
the appropriate security level login screen.

This is the HOME screen / starting point of the app.
"""
import tkinter as tk
from tkinter import messagebox
import time
import datetime

from ui.styles import COLORS, FONTS, PAD
from ui.widgets import (StyledLabel, StyledEntry, StyledButton,
                        PasswordEntry, Separator, StatusMessage, LevelBadge)
from auth.hasher import verify_password
from auth.user_store import get_user, update_failed_attempts, reset_failed_attempts
from auth.otp_generator import generate_otp, verify_otp, get_otp_time_remaining
from auth.captcha import generate_captcha_text, verify_captcha, draw_captcha_on_canvas

MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 30


class LoginScreen(tk.Tk):
    """
    The main application window.
    Manages which login "phase" is currently active.
    """

    def __init__(self):
        super().__init__()
        self.title("🔐 Three Level Password Verification System")
        self.geometry("480x600")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])
        self._center_window(480, 600)

        # State variables
        self._current_user = None      # Loaded user dict
        self._login_phase = "initial"  # initial / level2 / level3_otp / level3_captcha
        self._attempts = 0
        self._otp_code = None
        self._captcha_text = None
        self._lockout_until = None

        self._build_ui()

    def _center_window(self, w, h):
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ─────────────────────────────────────────────────────────────────────
    #  UI BUILD
    # ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the full UI layout."""
        # Clear everything first
        for widget in self.winfo_children():
            widget.destroy()

        self._build_header()
        self._build_phase_frame()

    def _build_header(self):
        """Top header with logo and title."""
        header = tk.Frame(self, bg=COLORS["bg_card"], pady=PAD["lg"])
        header.pack(fill="x")

        # Animated logo
        logo_frame = tk.Frame(header, bg=COLORS["bg_card"])
        logo_frame.pack()

        tk.Label(logo_frame, text="🔐",
                 font=("Segoe UI Emoji", 40),
                 bg=COLORS["bg_card"]).pack()

        tk.Label(header, text="SecureAuth Pro",
                 bg=COLORS["bg_card"],
                 fg=COLORS["text_primary"],
                 font=FONTS["logo"]).pack()

        tk.Label(header, text="Three Level Password Verification System",
                 bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack(pady=(2, 0))

        # Phase indicator strip
        self._phase_strip = tk.Frame(header, bg=COLORS["bg_card"])
        self._phase_strip.pack(pady=(PAD["sm"], 0))
        self._update_phase_strip("initial")

    def _build_phase_frame(self):
        """The main content frame that changes with each phase."""
        self._main_frame = tk.Frame(self, bg=COLORS["bg_dark"],
                                    padx=PAD["xl"], pady=PAD["lg"])
        self._main_frame.pack(fill="both", expand=True)

        self._show_initial_login()

    # ─────────────────────────────────────────────────────────────────────
    #  PHASE 1 — INITIAL LOGIN (Username + Password)
    # ─────────────────────────────────────────────────────────────────────

    def _show_initial_login(self):
        """Display the username + password login form."""
        self._clear_main()
        self._login_phase = "initial"
        self._update_phase_strip("initial")

        frame = self._main_frame

        # Level badges row (shows what levels are available)
        badge_frame = tk.Frame(frame, bg=COLORS["bg_dark"])
        badge_frame.pack(pady=(0, PAD["md"]))
        for lvl in [1, 2, 3]:
            LevelBadge(badge_frame, lvl).pack(side="left", padx=3)

        Separator(frame).pack(fill="x", pady=PAD["sm"])

        # Username field
        self._make_field_label(frame, "USERNAME")
        self._username_var = tk.StringVar()
        usr_frame = tk.Frame(frame, bg=COLORS["border"], padx=1, pady=1)
        usr_frame.pack(fill="x")
        self._username_entry = tk.Entry(
            usr_frame,
            textvariable=self._username_var,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat",
            font=FONTS["body"],
            bd=4,
        )
        self._username_entry.pack(fill="x")
        self._username_entry.bind("<FocusIn>",
            lambda e: usr_frame.config(bg=COLORS["border_focus"]))
        self._username_entry.bind("<FocusOut>",
            lambda e: usr_frame.config(bg=COLORS["border"]))

        # Password field
        self._make_field_label(frame, "PASSWORD")
        self._password_entry = PasswordEntry(frame)
        self._password_entry.pack(fill="x")
        self._password_entry.bind_key("<Return>", lambda e: self._on_level1_submit())

        # Status message
        self._status = StatusMessage(frame)
        self._status.pack(fill="x", pady=(PAD["sm"], PAD["xs"]))

        # Attempt indicator
        self._attempt_label = tk.Label(
            frame, text="",
            bg=COLORS["bg_dark"],
            fg=COLORS["warning"],
            font=FONTS["small"]
        )
        self._attempt_label.pack()

        # Login button
        StyledButton(
            frame, text="🔓  LOGIN",
            command=self._on_level1_submit,
            bg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            width=24,
        ).pack(fill="x", ipady=10, pady=PAD["md"])

        Separator(frame).pack(fill="x")

        # Register link
        reg_frame = tk.Frame(frame, bg=COLORS["bg_dark"])
        reg_frame.pack(pady=PAD["sm"])
        tk.Label(reg_frame, text="New here?  ",
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack(side="left")
        reg_btn = tk.Button(
            reg_frame, text="Create an Account →",
            command=self._open_register,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_accent"],
            activebackground=COLORS["bg_dark"],
            activeforeground=COLORS["primary"],
            relief="flat",
            font=("Segoe UI", 9, "underline"),
            cursor="hand2",
            bd=0,
        )
        reg_btn.pack(side="left")

        self._username_entry.focus_set()

    def _on_level1_submit(self):
        """Handle username + password submission (Level 1 auth)."""
        self._status.clear()

        username = self._username_var.get().strip()
        password = self._password_entry.get()

        if not username or not password:
            self._status.show_error("Please enter both username and password.")
            return

        # Check lockout
        if self._lockout_until and time.time() < self._lockout_until:
            remaining = int(self._lockout_until - time.time())
            self._status.show_error(
                f"Account locked! Too many failed attempts.\n"
                f"Try again in {remaining} seconds. 🔒"
            )
            self._start_lockout_countdown()
            return

        # Fetch user from database
        user = get_user(username)
        if not user:
            self._attempts += 1
            self._handle_failed_attempt(None, "Invalid username or password.")
            return

        # Verify password
        is_valid = verify_password(password, user["password_hash"], user["password_salt"])
        if not is_valid:
            self._attempts += 1
            self._handle_failed_attempt(username, "Invalid username or password.")
            return

        # Password correct! Store user and proceed based on level
        self._current_user = user
        self._attempts = 0

        level = user.get("level", 1)

        if level == 1:
            # Level 1: Done! Login successful
            self._login_success()
        elif level == 2:
            # Level 2: Go to security question
            self._show_level2_question()
        else:
            # Level 3: Go to OTP first
            self._show_level3_otp()

    def _handle_failed_attempt(self, username, message):
        """Handle a failed login attempt — track count and lock if needed."""
        remaining = MAX_ATTEMPTS - self._attempts

        if self._attempts >= MAX_ATTEMPTS:
            self._lockout_until = time.time() + LOCKOUT_SECONDS
            if username:
                update_failed_attempts(username, self._attempts, self._lockout_until)
            self._status.show_error(
                f"⛔ Account locked for {LOCKOUT_SECONDS} seconds!\n"
                f"Too many failed attempts."
            )
            self._start_lockout_countdown()
        else:
            self._status.show_error(f"{message}\n({remaining} attempt(s) remaining)")
            self._attempt_label.config(
                text=f"⚠ Attempt {self._attempts}/{MAX_ATTEMPTS}"
            )

    def _start_lockout_countdown(self):
        """Update the UI every second during lockout."""
        if self._lockout_until and time.time() < self._lockout_until:
            remaining = int(self._lockout_until - time.time())
            self._status.config(
                text=f"⛔ Locked. Try again in {remaining}s...",
                fg=COLORS["error"]
            )
            self.after(1000, self._start_lockout_countdown)
        else:
            self._lockout_until = None
            self._attempts = 0
            self._status.show_info("Account unlocked. You may try again.")
            self._attempt_label.config(text="")

    # ─────────────────────────────────────────────────────────────────────
    #  PHASE 2 — LEVEL 2 SECURITY QUESTION
    # ─────────────────────────────────────────────────────────────────────

    def _show_level2_question(self):
        """Display the security question screen (Level 2)."""
        self._clear_main()
        self._login_phase = "level2"
        self._update_phase_strip("level2")

        frame = self._main_frame
        user = self._current_user

        tk.Label(frame, text="🔒 Level 2 Verification",
                 bg=COLORS["bg_dark"], fg=COLORS["level2"],
                 font=FONTS["subtitle"]).pack(pady=(0, PAD["xs"]))
        tk.Label(frame,
                 text="Correct password ✓  Please answer your security question.",
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack()

        Separator(frame).pack(fill="x", pady=PAD["md"])

        # Question display
        question_box = tk.Frame(frame, bg=COLORS["bg_card"], padx=16, pady=12)
        question_box.pack(fill="x", pady=(0, PAD["md"]))

        tk.Label(question_box, text="Security Question:",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack(anchor="w")
        tk.Label(question_box, text=user["security_question"],
                 bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                 font=FONTS["heading"], wraplength=360, justify="left").pack(anchor="w")

        # Answer field
        self._make_field_label(frame, "YOUR ANSWER")
        ans_frame = tk.Frame(frame, bg=COLORS["border"], padx=1, pady=1)
        ans_frame.pack(fill="x")
        self._answer_entry = tk.Entry(
            ans_frame,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat",
            font=FONTS["body"],
            bd=4,
        )
        self._answer_entry.pack(fill="x")
        self._answer_entry.bind("<Return>", lambda e: self._on_level2_submit())
        self._answer_entry.bind("<FocusIn>",
            lambda e: ans_frame.config(bg=COLORS["border_focus"]))
        self._answer_entry.bind("<FocusOut>",
            lambda e: ans_frame.config(bg=COLORS["border"]))

        self._status = StatusMessage(frame)
        self._status.pack(fill="x", pady=PAD["sm"])

        StyledButton(
            frame, text="✓  VERIFY ANSWER",
            command=self._on_level2_submit,
            bg_color=COLORS["level2"],
            hover_color=COLORS["level2_dark"],
            width=24,
        ).pack(fill="x", ipady=10, pady=PAD["xs"])

        tk.Button(frame, text="← Go Back",
                  command=self._show_initial_login,
                  bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                  relief="flat", font=FONTS["small"], cursor="hand2", bd=0
                  ).pack(pady=PAD["sm"])

        self._answer_entry.focus_set()

    def _on_level2_submit(self):
        """Verify the security answer."""
        self._status.clear()
        answer = self._answer_entry.get().strip()

        if not answer:
            self._status.show_error("Please enter your answer.")
            return

        user = self._current_user
        is_valid = verify_password(
            answer.lower(),
            user["security_answer_hash"],
            user["security_answer_salt"]
        )

        if is_valid:
            self._login_success()
        else:
            self._attempts += 1
            remaining = MAX_ATTEMPTS - self._attempts
            if self._attempts >= MAX_ATTEMPTS:
                self._status.show_error(
                    "Too many wrong answers! Returning to login."
                )
                self.after(2000, self._reset_and_go_home)
            else:
                self._status.show_error(
                    f"Wrong answer! ({remaining} attempt(s) remaining)"
                )

    # ─────────────────────────────────────────────────────────────────────
    #  PHASE 3 — LEVEL 3 OTP
    # ─────────────────────────────────────────────────────────────────────

    def _show_level3_otp(self):
        """Display the OTP verification screen (first step of Level 3)."""
        self._clear_main()
        self._login_phase = "level3_otp"
        self._update_phase_strip("level3_otp")

        # Generate OTP
        username = self._current_user["username"]
        self._otp_code = generate_otp(session_key=username)

        frame = self._main_frame

        tk.Label(frame, text="🔴 Level 3 — Step 1: OTP",
                 bg=COLORS["bg_dark"], fg=COLORS["level3"],
                 font=FONTS["subtitle"]).pack(pady=(0, PAD["xs"]))
        tk.Label(frame, text="Correct password ✓  Please verify your One-Time Password.",
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack()

        Separator(frame).pack(fill="x", pady=PAD["md"])

        # OTP display box (simulates an SMS / email)
        otp_box = tk.Frame(frame, bg=COLORS["bg_card"], padx=16, pady=16)
        otp_box.pack(fill="x", pady=(0, PAD["md"]))

        tk.Label(otp_box, text="📱 Your OTP Code (simulated SMS):",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack()
        tk.Label(otp_box, text=self._otp_code,
                 bg=COLORS["bg_card"], fg=COLORS["level3"],
                 font=FONTS["otp"]).pack(pady=PAD["sm"])

        # Countdown timer
        self._otp_timer_label = tk.Label(
            otp_box, text="",
            bg=COLORS["bg_card"],
            fg=COLORS["warning"],
            font=FONTS["small"]
        )
        self._otp_timer_label.pack()
        self._update_otp_countdown(username)

        # Entry
        self._make_field_label(frame, "ENTER OTP CODE")
        otp_frame = tk.Frame(frame, bg=COLORS["border"], padx=1, pady=1)
        otp_frame.pack(fill="x")
        self._otp_entry = tk.Entry(
            otp_frame,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat",
            font=FONTS["otp"],
            bd=4,
            justify="center",
            width=10,
        )
        self._otp_entry.pack(fill="x", pady=4)
        self._otp_entry.bind("<Return>", lambda e: self._on_otp_submit())

        self._status = StatusMessage(frame)
        self._status.pack(fill="x", pady=PAD["sm"])

        btn_row = tk.Frame(frame, bg=COLORS["bg_dark"])
        btn_row.pack(fill="x")

        StyledButton(
            btn_row, text="✓  VERIFY OTP",
            command=self._on_otp_submit,
            bg_color=COLORS["level3"],
            hover_color=COLORS["level3_dark"],
            width=18,
        ).pack(side="left", ipady=10, expand=True, fill="x", padx=(0, 4))

        StyledButton(
            btn_row, text="🔄 Resend",
            command=lambda: self._show_level3_otp(),
            bg_color=COLORS["bg_card"],
            hover_color=COLORS["border"],
            width=10,
        ).pack(side="left", ipady=10)

        tk.Button(frame, text="← Go Back",
                  command=self._show_initial_login,
                  bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                  relief="flat", font=FONTS["small"], cursor="hand2", bd=0
                  ).pack(pady=PAD["sm"])

        self._otp_entry.focus_set()

    def _update_otp_countdown(self, username: str):
        """Live countdown showing OTP expiry time."""
        remaining = get_otp_time_remaining(username)
        if remaining > 0:
            self._otp_timer_label.config(
                text=f"⏱ Expires in {remaining}s",
                fg=COLORS["warning"] if remaining > 10 else COLORS["error"]
            )
            self.after(1000, lambda: self._update_otp_countdown(username))
        else:
            self._otp_timer_label.config(text="⚠ OTP Expired!", fg=COLORS["error"])

    def _on_otp_submit(self):
        """Verify the OTP."""
        self._status.clear()
        otp_input = self._otp_entry.get().strip()
        username = self._current_user["username"]

        if not otp_input:
            self._status.show_error("Please enter the OTP code.")
            return

        is_valid, message = verify_otp(username, otp_input)
        if is_valid:
            # OTP correct → go to CAPTCHA step
            self._show_level3_captcha()
        else:
            self._status.show_error(message)

    # ─────────────────────────────────────────────────────────────────────
    #  PHASE 3 — LEVEL 3 CAPTCHA
    # ─────────────────────────────────────────────────────────────────────

    def _show_level3_captcha(self):
        """Display the CAPTCHA verification screen (second step of Level 3)."""
        self._clear_main()
        self._login_phase = "level3_captcha"
        self._update_phase_strip("level3_captcha")

        self._captcha_text = generate_captcha_text()

        frame = self._main_frame

        tk.Label(frame, text="🔴 Level 3 — Step 2: CAPTCHA",
                 bg=COLORS["bg_dark"], fg=COLORS["level3"],
                 font=FONTS["subtitle"]).pack(pady=(0, PAD["xs"]))
        tk.Label(frame, text="OTP verified ✓  Prove you're human with the CAPTCHA below.",
                 bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack()

        Separator(frame).pack(fill="x", pady=PAD["md"])

        # CAPTCHA Canvas
        captcha_frame = tk.Frame(frame, bg=COLORS["bg_card"], pady=16)
        captcha_frame.pack(fill="x", pady=(0, PAD["sm"]))

        tk.Label(captcha_frame, text="Type the characters shown below:",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=FONTS["small"]).pack()

        self._captcha_canvas = tk.Canvas(
            captcha_frame,
            width=240, height=65,
            bg=COLORS["bg_dark"],
            highlightthickness=2,
            highlightbackground=COLORS["border"],
        )
        self._captcha_canvas.pack(pady=(8, 0))
        draw_captcha_on_canvas(self._captcha_canvas, self._captcha_text, 240, 65)

        tk.Label(captcha_frame, text="CAPTCHA is case-sensitive",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=("Segoe UI", 8)).pack(pady=(4, 0))

        # Reload button
        tk.Button(
            captcha_frame, text="🔄 New CAPTCHA",
            command=self._refresh_captcha,
            bg=COLORS["bg_card"],
            fg=COLORS["text_accent"],
            activebackground=COLORS["bg_card"],
            relief="flat", font=FONTS["small"], cursor="hand2", bd=0
        ).pack()

        # Input
        self._make_field_label(frame, "ENTER CAPTCHA TEXT")
        cap_frame = tk.Frame(frame, bg=COLORS["border"], padx=1, pady=1)
        cap_frame.pack(fill="x")
        self._captcha_entry = tk.Entry(
            cap_frame,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief="flat",
            font=FONTS["code"],
            bd=4,
            justify="center",
        )
        self._captcha_entry.pack(fill="x")
        self._captcha_entry.bind("<Return>", lambda e: self._on_captcha_submit())
        self._captcha_entry.bind("<FocusIn>",
            lambda e: cap_frame.config(bg=COLORS["border_focus"]))
        self._captcha_entry.bind("<FocusOut>",
            lambda e: cap_frame.config(bg=COLORS["border"]))

        self._status = StatusMessage(frame)
        self._status.pack(fill="x", pady=PAD["sm"])

        StyledButton(
            frame, text="✓  VERIFY & LOGIN",
            command=self._on_captcha_submit,
            bg_color=COLORS["level3"],
            hover_color=COLORS["level3_dark"],
            width=24,
        ).pack(fill="x", ipady=10, pady=PAD["xs"])

        tk.Button(frame, text="← Go Back",
                  command=self._show_initial_login,
                  bg=COLORS["bg_dark"], fg=COLORS["text_secondary"],
                  relief="flat", font=FONTS["small"], cursor="hand2", bd=0
                  ).pack(pady=PAD["sm"])

        self._captcha_entry.focus_set()

    def _refresh_captcha(self):
        """Generate a new CAPTCHA image."""
        self._captcha_text = generate_captcha_text()
        draw_captcha_on_canvas(self._captcha_canvas, self._captcha_text, 240, 65)
        self._captcha_entry.delete(0, tk.END)
        self._status.clear()

    def _on_captcha_submit(self):
        """Verify CAPTCHA input."""
        self._status.clear()
        user_input = self._captcha_entry.get()

        if not user_input:
            self._status.show_error("Please enter the CAPTCHA text.")
            return

        if verify_captcha(user_input, self._captcha_text):
            self._login_success()
        else:
            self._status.show_error("Wrong CAPTCHA! Please try again.")
            self._refresh_captcha()

    # ─────────────────────────────────────────────────────────────────────
    #  SUCCESS & HELPER METHODS
    # ─────────────────────────────────────────────────────────────────────

    def _login_success(self):
        """Handle successful login — open the dashboard."""
        reset_failed_attempts(self._current_user["username"])
        # Import here to avoid circular imports
        from ui.dashboard_screen import DashboardScreen
        DashboardScreen(self, self._current_user)

    def _reset_and_go_home(self):
        """Reset state and go back to initial login."""
        self._current_user = None
        self._attempts = 0
        self._show_initial_login()

    def _clear_main(self):
        """Clear all widgets from the main frame."""
        for widget in self._main_frame.winfo_children():
            widget.destroy()

    def _make_field_label(self, parent, text: str):
        tk.Label(
            parent, text=text,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_secondary"],
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(PAD["sm"], 2))

    def _update_phase_strip(self, phase: str):
        """Update the progress dots at the top of the screen."""
        for widget in self._phase_strip.winfo_children():
            widget.destroy()

        phases = [
            ("initial",         "①  Password",   COLORS["level1"]),
            ("level2",          "②  Security Q",  COLORS["level2"]),
            ("level3_otp",      "③  OTP",         COLORS["level3"]),
            ("level3_captcha",  "④  CAPTCHA",     COLORS["level3"]),
        ]

        phase_order = [p[0] for p in phases]
        current_idx = phase_order.index(phase) if phase in phase_order else 0

        for i, (key, label, color) in enumerate(phases):
            is_active = (i == current_idx)
            is_done = (i < current_idx)
            fg = color if is_active else (COLORS["text_secondary"] if not is_done else "#10b981")
            font = FONTS["small"] if not is_active else ("Segoe UI", 9, "bold")

            tk.Label(self._phase_strip,
                     text=("✓ " if is_done else "") + label,
                     bg=COLORS["bg_card"],
                     fg=fg,
                     font=font).pack(side="left", padx=8)

    def _open_register(self):
        """Open the registration window."""
        from ui.register_screen import RegisterScreen
        RegisterScreen(self)
