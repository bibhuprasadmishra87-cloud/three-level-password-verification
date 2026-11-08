"""
dashboard_screen.py — Success Dashboard
Shown after a user successfully logs in through all required levels.
Displays user info, security level achieved, and login history.
"""
import tkinter as tk
from tkinter import messagebox
import datetime
from ui.styles import COLORS, FONTS, PAD
from ui.widgets import Separator, StyledButton, LevelBadge


class DashboardScreen(tk.Toplevel):
    """
    The 'You are logged in!' success screen.
    Shows a welcome message and user details.
    """

    def __init__(self, parent, user: dict):
        super().__init__(parent)
        self.parent = parent
        self.user = user

        level = user.get("level", 1)
        level_names = {1: "Basic", 2: "Medium", 3: "Expert"}

        self.title(f"✓ Welcome, {user['username']}! — SecureAuth Pro")
        self.geometry("500x560")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])
        self.grab_set()

        self._center_window()
        self._build_ui()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 500) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"500x560+{x}+{y}")

    def _build_ui(self):
        # ── SUCCESS BANNER ───────────────────────────────────────────────
        banner = tk.Frame(self, bg=COLORS["success"], pady=PAD["xl"])
        banner.pack(fill="x")

        tk.Label(banner, text="✅",
                 font=("Segoe UI Emoji", 48),
                 bg=COLORS["success"]).pack()
        tk.Label(banner, text="Access Granted!",
                 bg=COLORS["success"], fg="#ffffff",
                 font=FONTS["title"]).pack()
        tk.Label(banner,
                 text=f"Welcome back, {self.user['username']}",
                 bg=COLORS["success"], fg="#dcfce7",
                 font=FONTS["body"]).pack(pady=(4, 0))

        # ── USER DETAILS CARD ────────────────────────────────────────────
        body = tk.Frame(self, bg=COLORS["bg_dark"], padx=PAD["xl"], pady=PAD["lg"])
        body.pack(fill="both", expand=True)

        # Level badge
        level = self.user.get("level", 1)
        badge_frame = tk.Frame(body, bg=COLORS["bg_dark"])
        badge_frame.pack(pady=(0, PAD["md"]))
        LevelBadge(badge_frame, level).pack()

        # Info card
        card = tk.Frame(body, bg=COLORS["bg_card"], padx=PAD["lg"], pady=PAD["lg"])
        card.pack(fill="x", pady=(0, PAD["md"]))

        tk.Label(card, text="SESSION INFORMATION",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")

        Separator(card).pack(fill="x", pady=PAD["xs"])

        info_items = [
            ("👤  Username",    self.user["username"]),
            ("🛡️  Security Level", f"Level {level} — {['', 'Basic', 'Medium', 'Expert'][level]}"),
            ("🕐  Login Time",  datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")),
            ("✅  Auth Status", "All verification steps passed"),
        ]

        for label, value in info_items:
            row = tk.Frame(card, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label,
                     bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                     font=FONTS["small"], width=20, anchor="w").pack(side="left")
            tk.Label(row, text=value,
                     bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                     font=FONTS["body"]).pack(side="left")

        # Verification steps completed
        steps_card = tk.Frame(body, bg=COLORS["bg_card"],
                              padx=PAD["lg"], pady=PAD["md"])
        steps_card.pack(fill="x", pady=(0, PAD["md"]))

        tk.Label(steps_card, text="COMPLETED VERIFICATION STEPS",
                 bg=COLORS["bg_card"], fg=COLORS["text_secondary"],
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        Separator(steps_card).pack(fill="x", pady=PAD["xs"])

        all_steps = [
            (True,  "🔑 Password Verification"),
            (level >= 2, "❓ Security Question Answer"),
            (level >= 3, "📱 One-Time Password (OTP)"),
            (level >= 3, "🤖 CAPTCHA Verification"),
        ]

        for completed, step_name in all_steps:
            row = tk.Frame(steps_card, bg=COLORS["bg_card"])
            row.pack(fill="x", pady=2)
            status_icon = "✅" if completed else "⬜"
            status_color = COLORS["success"] if completed else COLORS["text_secondary"]
            tk.Label(row, text=f"{status_icon}  {step_name}",
                     bg=COLORS["bg_card"], fg=status_color,
                     font=FONTS["small"]).pack(anchor="w")

        # Logout button
        StyledButton(
            body, text="🚪  LOGOUT",
            command=self._logout,
            bg_color="#374151",
            hover_color="#4b5563",
            width=20,
        ).pack(fill="x", ipady=8, pady=PAD["xs"])

    def _logout(self):
        """Log out and return to the login screen."""
        self.destroy()
        # Reset the parent login screen
        self.parent._current_user = None
        self.parent._attempts = 0
        self.parent._show_initial_login()
