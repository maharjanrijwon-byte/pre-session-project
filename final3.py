# ChalkQuiz - Quiz Game
# Pre-university CS Project
# Date: 2026
import sys
import os
import re
import html
import json
import random
import datetime
import urllib.request
import urllib.error
import socket
import time
socket.setdefaulttimeout(6)
TRIVIA_API_URL = "https://opentdb.com/api.php"
TRIVIA_CATEGORY = 18  
QUESTIONS_PER_ROUND = 10
LETTERS = ["A", "B", "C", "D"]
USERS_FILE = "users.txt"
SCORES_FILE = "scores.txt"
def ensure_files_exist():
    for filename in (USERS_FILE, SCORES_FILE):
        if not os.path.exists(filename):
            try:
                with open(filename, "w"):
                    pass
            except OSError:
                pass
def load_users():
    users = {}
    try:
        with open(USERS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line != "":
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        users[parts[0]] = parts[1]
    except OSError:
        pass
    return users
def _http_get_json(url, timeout=5):
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))
def fetch_online_questions(n=QUESTIONS_PER_ROUND, max_attempts=3):
    """Pull a fresh batch of computer-science questions from the free Open
    Trivia Database (no signup, no key). Raises on any failure - the caller
    is expected to show the user an error, since there's no offline bank
    to fall back to."""
    data = None
    code = None
    for attempt in range(max_attempts):
        url = f"{TRIVIA_API_URL}?amount={n}&category={TRIVIA_CATEGORY}&type=multiple"
        try:
            data = _http_get_json(url)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"API request failed ({e.code})") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"couldn't reach opentdb.com: {e.reason}") from e
        except socket.timeout as e:
            raise RuntimeError("opentdb.com took too long to respond") from e
        code = data.get("response_code")
        if code == 0:
            break
        if attempt + 1 < max_attempts:
            time.sleep(1.5)  # opentdb rate-limits to ~1 request/5s; back off briefly
    if code != 0:
        raise RuntimeError(f"opentdb returned response_code {code}")
    questions = []
    for item in data.get("results", []):
        q_text = html.unescape(item.get("question", "")).strip()
        correct = html.unescape(item.get("correct_answer", "")).strip()
        wrong = [html.unescape(w).strip() for w in item.get("incorrect_answers", [])]
        if not q_text or not correct or len(wrong) != 3:
            continue
        answers = wrong + [correct]
        random.shuffle(answers)
        correct_letter = LETTERS[answers.index(correct)]
        options = [f"{LETTERS[i]}. {a}" for i, a in enumerate(answers)]
        questions.append({"question": q_text, "options": options, "answer": correct_letter})
    if len(questions) < 4:
        raise ValueError("opentdb didn't return enough usable questions")
    return questions
def quiz_status_text():
    """A short, user-facing note about where questions come from."""
    return "Each round pulls a fresh set of questions online."
def run_desktop():
    import threading
    import tkinter as tk
    from tkinter import messagebox, ttk
    SLATE_950 = "#020617"
    SLATE_900 = "#0f172a"
    SLATE_800 = "#1e293b"
    SLATE_700 = "#334155"
    SLATE_500 = "#64748b"
    SLATE_400 = "#94a3b8"
    SLATE_100 = "#f1f5f9"
    SLATE_50 = "#f8fafc"
    AMBER_200 = "#fde68a"
    AMBER_300 = "#fcd34d"
    AMBER_400 = "#fbbf24"
    SKY_400 = "#38bdf8"
    VIOLET_400 = "#a78bfa"
    TEAL_400 = "#2dd4bf"
    EMERALD_400 = "#34d399"
    EMERALD_500 = "#10b981"
    ROSE_400 = "#fb7185"
    ROSE_500 = "#f43f5e"
    CHALK_ACCENTS = [SKY_400, VIOLET_400, AMBER_400, TEAL_400]
    FONT_DISPLAY = ("Segoe UI", 26, "bold")
    FONT_H1 = ("Segoe UI", 18, "bold")
    FONT_H2 = ("Segoe UI", 14, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_BODY_BOLD = ("Segoe UI", 11, "bold")
    FONT_SMALL = ("Segoe UI", 9)
    FONT_SMALL_BOLD = ("Segoe UI", 9, "bold")
    FONT_MONO = ("Consolas", 10)
    FONT_MONO_BOLD = ("Consolas", 11, "bold")
    FONT_SCORE_BIG = ("Consolas", 42, "bold")
    FONT_BUTTON = ("Segoe UI", 11, "bold")
    FONT_OPTION = ("Segoe UI", 11)
    def _clamp(v):
        return max(0, min(255, int(v)))
    def blend_hex(hex_a, hex_b, t):
        """Blend two hex colors. t=0 -> hex_a, t=1 -> hex_b."""
        a = hex_a.lstrip("#")
        b = hex_b.lstrip("#")
        ar, ag, ab = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
        br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
        r = _clamp(ar + (br - ar) * t)
        g = _clamp(ag + (bg - ag) * t)
        bch = _clamp(ab + (bb - ab) * t)
        return f"#{r:02x}{g:02x}{bch:02x}"
    def tint(accent, t=0.82, base=SLATE_900):
        """A subtle background tint of an accent color over a dark panel."""
        return blend_hex(accent, base, t)
    def _auto_hover(fill):
        """Lighten dark fills, darken light fills, for a visible hover state."""
        hexv = fill.lstrip("#")
        r, g, b = int(hexv[0:2], 16), int(hexv[2:4], 16), int(hexv[4:6], 16)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        if luminance > 200:
            return blend_hex(fill, SLATE_400, 0.35)
        return blend_hex(fill, "#ffffff", 0.18)

    def _rounded_points(x1, y1, x2, y2, r):
        r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
        return [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1,
            x2, y1 + r,
            x2, y2 - r,
            x2, y2,
            x2 - r, y2,
            x1 + r, y2,
            x1, y2,
            x1, y2 - r,
            x1, y1 + r,
            x1, y1,
        ]
    def draw_pill(canvas, x1, y1, x2, y2, radius, color):
        pts = _rounded_points(x1, y1, x2, y2, radius)
        canvas.create_polygon(pts, smooth=True, fill=color, outline="")
    def draw_progress(canvas, total, current_index):
        """A rail of chalk-colored pill segments standing in for a progress bar."""
        canvas.delete("all")
        dot_w, dot_h, gap, radius = 22, 7, 7, 4
        pad = 3
        x = pad
        for i in range(total):
            if i < current_index:
                color = AMBER_400
            elif i == current_index:
                color = AMBER_300
                halo = blend_hex(AMBER_400, SLATE_950, 0.6)
                draw_pill(canvas, x - 3, 4 - 3, x + dot_w + 3, 4 + dot_h + 3,
                          radius + 3, halo)
            else:
                color = SLATE_800
            draw_pill(canvas, x, 4, x + dot_w, 4 + dot_h, radius, color)
            x += dot_w + gap
        canvas.config(width=x - gap + pad + 3, height=dot_h + 14)
    class RoundedButton(tk.Canvas):
        """A pill-shaped button drawn on a Canvas (Tk has no built-in rounded button)."""
        def __init__(self, parent, text, command=None, width=260, height=46,
                     radius=23, bg=SLATE_950, fill=AMBER_400, hover=None,
                     fg=SLATE_950, font=FONT_BUTTON):
            super().__init__(parent, width=width, height=height, bg=bg,
                              highlightthickness=0, bd=0)
            self.command = command
            self.bg_color = bg
            self.fill = fill
            self.hover = hover or _auto_hover(fill)
            self.fg = fg
            self.radius = radius
            self.w = width
            self.h = height
            self.font = font
            self.text = text
            self._render(self.fill)
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<Button-1>", self._on_click)
        def _render(self, color):
            self.delete("all")
            shadow = blend_hex(self.bg_color, "#000000", 0.45)
            shadow_pts = _rounded_points(3, 4, self.w - 1, self.h, self.radius)
            self.create_polygon(shadow_pts, smooth=True, fill=shadow, outline="")
            pts = _rounded_points(2, 2, self.w - 2, self.h - 2, self.radius)
            self.create_polygon(pts, smooth=True, fill=color, outline="")
            self.create_text(self.w / 2, self.h / 2, text=self.text,
                              fill=self.fg, font=self.font)
        def _on_enter(self, _event):
            self._render(self.hover)
            self.config(cursor="hand2")

        def _on_leave(self, _event):
            self._render(self.fill)

        def _on_click(self, _event):
            if self.command:
                self.command()
    class LinkLabel(tk.Label):
        """A low-emphasis text link for secondary navigation actions."""
        def __init__(self, parent, text, command=None, bg=SLATE_900,
                     fg=AMBER_300, hover_fg=AMBER_200, font=FONT_SMALL_BOLD):
            super().__init__(parent, text=text, bg=bg, fg=fg, font=font, cursor="hand2")
            self.command = command
            self._fg = fg
            self._hover_fg = hover_fg
            self.bind("<Button-1>", self._on_click)
            self.bind("<Enter>", lambda e: self.config(fg=self._hover_fg))
            self.bind("<Leave>", lambda e: self.config(fg=self._fg))
        def _on_click(self, _event):
            if self.command:
                self.command()
    class OptionChip(tk.Canvas):
        """One answer option: a lettered badge + text on a rounded chalk-colored chip."""
        def __init__(self, parent, index, text, accent, on_select,
                     width=480, height=56, radius=28, bg=SLATE_900):
            super().__init__(parent, width=width, height=height, bg=bg,
                              highlightthickness=0, bd=0)
            self.index = index
            self.letter = LETTERS[index]
            self.text = text
            self.accent = accent
            self.on_select = on_select
            self.bg_color = bg
            self.w = width
            self.h = height
            self.radius = radius
            self.locked = False
            self.set_idle()
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            self.bind("<Button-1>", self._on_click)
        def _draw(self, chip_fill, border, badge_fill, badge_fg, badge_label, text_fg):
            self.delete("all")
            shadow = blend_hex(self.bg_color, "#000000", 0.4)
            shadow_pts = _rounded_points(3, 4, self.w - 1, self.h, self.radius)
            self.create_polygon(shadow_pts, smooth=True, fill=shadow, outline="")
            pts = _rounded_points(2, 2, self.w - 2, self.h - 2, self.radius)
            self.create_polygon(pts, smooth=True, fill=chip_fill, outline=border, width=1.5)
            cx, cy, br = 32, self.h / 2, 15
            self.create_oval(cx - br, cy - br, cx + br, cy + br, fill=badge_fill, outline="")
            self.create_text(cx, cy, text=badge_label, fill=badge_fg, font=FONT_BODY_BOLD)
            self.create_text(60, self.h / 2, text=self.text, fill=text_fg,
                              font=FONT_OPTION, anchor="w", width=self.w - 76)
        def set_idle(self):
            self.locked = False
            self._draw(tint(self.accent, 0.88), self.accent, self.accent,
                        SLATE_950, self.letter, SLATE_100)
        def _hover_draw(self):
            self._draw(tint(self.accent, 0.76), self.accent, self.accent,
                        SLATE_950, self.letter, SLATE_50)
        def set_correct(self):
            self.locked = True
            self._draw(tint(EMERALD_500, 0.82), EMERALD_400, EMERALD_400,
                        SLATE_950, "\u2713", SLATE_50)
        def set_wrong(self):
            self.locked = True
            self._draw(tint(ROSE_500, 0.82), ROSE_400, ROSE_400,
                        SLATE_950, "\u2715", SLATE_50)
        def set_dim(self):
            self.locked = True
            self._draw(SLATE_900, SLATE_800, SLATE_800, SLATE_500, self.letter, SLATE_500)
        def _on_enter(self, _e):
            if not self.locked:
                self._hover_draw()
                self.config(cursor="hand2")
        def _on_leave(self, _e):
            if not self.locked:
                self.set_idle()
        def _on_click(self, _e):
            if not self.locked and self.on_select:
                self.on_select(self.index)
    def build_wordmark(parent, bg=SLATE_950, size=26):
        """The 'Chalk' + 'Quiz' two-tone title with a hand-drawn underline."""
        frame = tk.Frame(parent, bg=bg)
        row = tk.Frame(frame, bg=bg)
        row.pack()
        tk.Label(row, text="Chalk", bg=bg, fg=SLATE_50,
                 font=("Segoe UI", size, "bold")).pack(side="left")
        tk.Label(row, text="Quiz", bg=bg, fg=AMBER_300,
                 font=("Segoe UI", size, "bold")).pack(side="left")
        squiggle = tk.Canvas(frame, width=120, height=10, bg=bg, highlightthickness=0)
        squiggle.create_line(4, 6, 26, 2, 48, 8, 70, 2, 92, 8, 116, 4,
                              fill=AMBER_300, width=2, smooth=True)
        squiggle.pack(pady=(3, 0))
        return frame
    def make_card(parent, accent=AMBER_400, bg=SLATE_950, panel_color=SLATE_900,
                  ring_color=SLATE_800):
        """A modern card shell: a faint accent-tinted glow ring, a solid accent
        strip along the top edge, and a flat panel underneath for real content.
        Returns (outer_frame_to_pack, panel_frame_to_build_content_in)."""
        glow = tk.Frame(parent, bg=blend_hex(accent, bg, 0.85))
        ring_frame = tk.Frame(glow, bg=ring_color)
        ring_frame.pack(padx=1, pady=1, fill="both", expand=True)
        panel_frame = tk.Frame(ring_frame, bg=panel_color)
        panel_frame.pack(padx=1, pady=1, fill="both", expand=True)
        tk.Frame(panel_frame, bg=accent, height=4).pack(fill="x")
        return glow, panel_frame
    class QuizApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("ChalkQuiz - Quiz Game")
            self.geometry("600x760")  # fallback size if maximizing isn't supported
            self.configure(bg=SLATE_950)
            self.resizable(True, True)
            self._maximize_window()
            ensure_files_exist()
            self.current_user = None
            self.quiz_questions = []
            self.current_q_index = 0
            self.score = 0
            self.answered = False
            self.selected_index = None
            self.answer_log = []
            self.option_widgets = []
            self._user_labels = []
            self._quiz_active = False
            self._loading_job = None
            self._loading_dots = 0
            self.container = tk.Frame(self, bg=SLATE_950)
            self.container.pack(fill="both", expand=True)
            self.build_login_screen()
            self.build_register_screen()
            self.build_dashboard_screen()
            self.build_loading_screen()
            self.build_quiz_screen()
            self.build_results_screen()
            self.build_review_screen()
            self.build_scores_screen()
            self.bind("<Key>", self._on_quiz_key)
            self.show_frame(self.login_frame)
        def _maximize_window(self):
            """Open maximized (title bar and taskbar still visible), with
            fallbacks since Tk's maximize support differs by platform."""
            try:
                self.state("zoomed")  # Windows, and some Linux window managers
                return
            except tk.TclError:
                pass
            try:
                self.attributes("-zoomed", True)  # most other Linux window managers
                return
            except tk.TclError:
                pass
            self.update_idletasks()
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            self.geometry(f"{w}x{h}+0+0")
        def show_frame(self, frame):
            frame.tkraise()
        def build_topbar(self, parent):
            bar = tk.Frame(parent, bg=SLATE_950)
            bar.pack(fill="x", padx=24, pady=(18, 0))
            left = tk.Frame(bar, bg=SLATE_950)
            left.pack(side="left")
            tk.Label(left, text="Chalk", bg=SLATE_950, fg=SLATE_50,
                     font=("Segoe UI", 13, "bold")).pack(side="left")
            tk.Label(left, text="Quiz", bg=SLATE_950, fg=AMBER_300,
                     font=("Segoe UI", 13, "bold")).pack(side="left")
            user_lbl = tk.Label(bar, text="", bg=SLATE_950, fg=SLATE_400, font=FONT_MONO)
            user_lbl.pack(side="right")
            self._user_labels.append(user_lbl)
            return bar
        def _refresh_user_labels(self):
            text = self.current_user or ""
            for lbl in self._user_labels:
                lbl.config(text=text)

        def _styled_entry(self, parent, show=None):
            kwargs = {}
            if show:
                kwargs["show"] = show
            return tk.Entry(parent, font=FONT_BODY, bg=SLATE_800, fg=SLATE_50,
                             insertbackground=SLATE_50, relief="flat",
                             highlightthickness=1, highlightbackground=SLATE_700,
                             highlightcolor=AMBER_400, width=26, **kwargs)
        def build_login_screen(self):
            self.login_frame = tk.Frame(self.container, bg=SLATE_950)
            self.login_frame.place(relwidth=1, relheight=1)
            wrap = tk.Frame(self.login_frame, bg=SLATE_950)
            wrap.place(relx=0.5, rely=0.5, anchor="center")
            build_wordmark(wrap).pack(pady=(0, 26))
            card, card_panel = make_card(wrap, accent=SKY_400)
            card.pack()
            inner = tk.Frame(card_panel, bg=SLATE_900)
            inner.pack(padx=36, pady=28)
            tk.Label(inner, text="\U0001F510", font=("Segoe UI", 22), bg=SLATE_900,
                     fg=SKY_400).pack(anchor="w", pady=(0, 6))
            tk.Label(inner, text="LOG IN", font=FONT_SMALL_BOLD, bg=SLATE_900,
                     fg=SLATE_400).pack(anchor="w", pady=(0, 14))
            tk.Label(inner, text="Username", font=FONT_SMALL, bg=SLATE_900,
                     fg=SLATE_400).pack(anchor="w")
            self.login_user_entry = self._styled_entry(inner)
            self.login_user_entry.pack(pady=(2, 14), fill="x")
            tk.Label(inner, text="Password", font=FONT_SMALL, bg=SLATE_900,
                     fg=SLATE_400).pack(anchor="w")
            self.login_pass_entry = self._styled_entry(inner, show="*")
            self.login_pass_entry.pack(pady=(2, 20), fill="x")
            RoundedButton(inner, "Log in", command=self.handle_login,
                          width=268, height=46, fill=AMBER_400,
                          bg=SLATE_900).pack(pady=(0, 12))
            LinkLabel(inner, "Need an account? Register",
                      command=lambda: self.show_frame(self.register_frame)).pack()
            self.login_user_entry.bind("<Return>", lambda e: self.handle_login())
            self.login_pass_entry.bind("<Return>", lambda e: self.handle_login())
        def handle_login(self):
            username = self.login_user_entry.get().strip()
            password = self.login_pass_entry.get().strip()
            users = load_users()
            if username in users and users[username] == password:
                self.current_user = username
                self.user_welcome_label.config(text=f"Welcome back, {username}")
                self._refresh_user_labels()
                self.login_user_entry.delete(0, tk.END)
                self.login_pass_entry.delete(0, tk.END)
                self.show_frame(self.dashboard_frame)
            else:
                messagebox.showerror("Error", "Wrong username or password.")
        def build_register_screen(self):
            self.register_frame = tk.Frame(self.container, bg=SLATE_950)
            self.register_frame.place(relwidth=1, relheight=1)
            wrap = tk.Frame(self.register_frame, bg=SLATE_950)
            wrap.place(relx=0.5, rely=0.5, anchor="center")
            build_wordmark(wrap).pack(pady=(0, 26))
            card, card_panel = make_card(wrap, accent=VIOLET_400)
            card.pack()
            inner = tk.Frame(card_panel, bg=SLATE_900)
            inner.pack(padx=36, pady=28)
            tk.Label(inner, text="\U0001F464", font=("Segoe UI", 20), bg=SLATE_900,
                     fg=VIOLET_400).pack(anchor="w", pady=(0, 6))
            tk.Label(inner, text="CREATE ACCOUNT", font=FONT_SMALL_BOLD, bg=SLATE_900,
                     fg=SLATE_400).pack(anchor="w", pady=(0, 14))
            tk.Label(inner, text="Choose a username", font=FONT_SMALL, bg=SLATE_900,
                     fg=SLATE_400).pack(anchor="w")
            self.reg_user_entry = self._styled_entry(inner)
            self.reg_user_entry.pack(pady=(2, 14), fill="x")
            tk.Label(inner, text="Choose a password", font=FONT_SMALL, bg=SLATE_900,
                     fg=SLATE_400).pack(anchor="w")
            self.reg_pass_entry = self._styled_entry(inner, show="*")
            self.reg_pass_entry.pack(pady=(2, 20), fill="x")
            RoundedButton(inner, "Create account", command=self.handle_register,
                          width=268, height=46, fill=AMBER_400,
                          bg=SLATE_900).pack(pady=(0, 12))
            LinkLabel(inner, "Back to log in",
                      command=lambda: self.show_frame(self.login_frame)).pack()
            self.reg_user_entry.bind("<Return>", lambda e: self.handle_register())
            self.reg_pass_entry.bind("<Return>", lambda e: self.handle_register())
        def handle_register(self):
            username = self.reg_user_entry.get().strip()
            password = self.reg_pass_entry.get().strip()
            if username == "":
                messagebox.showwarning("Warning", "Username can't be blank.")
                return
            if "," in username:
                messagebox.showwarning("Warning", "Username can't contain a comma.")
                return
            users = load_users()
            if username in users:
                messagebox.showwarning("Warning", "That username already exists.")
                return
            if password == "":
                messagebox.showwarning("Warning", "Password can't be blank.")
                return
            try:
                with open(USERS_FILE, "a") as f:
                    f.write(f"{username},{password}\n")
            except OSError as e:
                messagebox.showerror("Error", f"Could not save your account: {e}")
                return
            messagebox.showinfo("Success", "Account created - you can log in now.")
            self.reg_user_entry.delete(0, tk.END)
            self.reg_pass_entry.delete(0, tk.END)
            self.show_frame(self.login_frame)
        def handle_logout(self):
            self.current_user = None
            self._quiz_active = False
            self._refresh_user_labels()
            self.show_frame(self.login_frame)
        def build_dashboard_screen(self):
            self.dashboard_frame = tk.Frame(self.container, bg=SLATE_950)
            self.dashboard_frame.place(relwidth=1, relheight=1)
            self.build_topbar(self.dashboard_frame)

            wrap = tk.Frame(self.dashboard_frame, bg=SLATE_950)
            wrap.place(relx=0.5, rely=0.52, anchor="center")
            self.user_welcome_label = tk.Label(wrap, text="", font=FONT_H1,
                                                bg=SLATE_950, fg=SLATE_50)
            self.user_welcome_label.pack(pady=(0, 4))
            tk.Label(wrap, text="Ready for another round?", font=FONT_BODY,
                     bg=SLATE_950, fg=SLATE_400).pack(pady=(0, 6))
            self.ai_status_label = tk.Label(wrap, text=quiz_status_text(), font=FONT_SMALL,
                                             bg=SLATE_950, fg=SLATE_500, wraplength=320,
                                             justify="center")
            self.ai_status_label.pack(pady=(0, 22))
            RoundedButton(wrap, "\u25B6  Start quiz", command=self.start_quiz,
                          width=280, height=50, fill=AMBER_400,
                          bg=SLATE_950).pack(pady=(0, 12))
            RoundedButton(wrap, "\U0001F3C6  View scores & leaderboard",
                          command=self.load_and_show_scores,
                          width=280, height=44, fill=SLATE_800, fg=SLATE_50,
                          bg=SLATE_950).pack(pady=(0, 22))
            LinkLabel(wrap, "Log out", command=self.handle_logout,
                      bg=SLATE_950, fg=SLATE_500, hover_fg=ROSE_400).pack()
        def build_loading_screen(self):
            self.loading_frame = tk.Frame(self.container, bg=SLATE_950)
            self.loading_frame.place(relwidth=1, relheight=1)
            self.build_topbar(self.loading_frame)
            wrap = tk.Frame(self.loading_frame, bg=SLATE_950)
            wrap.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(wrap, text="\u270e", font=("Segoe UI", 34, "bold"),
                     bg=SLATE_950, fg=AMBER_300).pack(pady=(0, 12))
            self.loading_label = tk.Label(wrap, text="Generating fresh questions",
                                           font=FONT_H2, bg=SLATE_950, fg=SLATE_50)
            self.loading_label.pack()
            tk.Label(wrap, text="Fetching a new round of questions online",
                     font=FONT_BODY, bg=SLATE_950, fg=SLATE_400).pack(pady=(4, 0))
        def _animate_loading(self):
            self._loading_dots = (self._loading_dots + 1) % 4
            self.loading_label.config(text="Generating fresh questions" + "." * self._loading_dots)
            self._loading_job = self.after(400, self._animate_loading)
        def _stop_loading_animation(self):
            if self._loading_job is not None:
                self.after_cancel(self._loading_job)
                self._loading_job = None
        def build_quiz_screen(self):
            self.quiz_frame = tk.Frame(self.container, bg=SLATE_950)
            self.quiz_frame.place(relwidth=1, relheight=1)
            self.build_topbar(self.quiz_frame)
            header = tk.Frame(self.quiz_frame, bg=SLATE_950)
            header.pack(fill="x", padx=30, pady=(22, 10))
            self.progress_canvas = tk.Canvas(header, bg=SLATE_950,
                                              highlightthickness=0, height=14)
            self.progress_canvas.pack(side="left")
            self.score_label = tk.Label(header, text="score 00", font=FONT_MONO,
                                         bg=SLATE_950, fg=SLATE_400)
            self.score_label.pack(side="right")
            card, card_panel = make_card(self.quiz_frame, accent=AMBER_400)
            card.pack(padx=30, pady=(0, 12), fill="both", expand=True)
            self.quiz_card_inner = tk.Frame(card_panel, bg=SLATE_900)
            self.quiz_card_inner.pack(padx=26, pady=24, fill="both", expand=True)
            self.q_num_label = tk.Label(self.quiz_card_inner, text="", font=FONT_MONO,
                                         bg=SLATE_900, fg=SLATE_500, anchor="w")
            self.q_num_label.pack(fill="x")
            self.q_text_label = tk.Label(self.quiz_card_inner, text="", font=FONT_H2,
                                          bg=SLATE_900, fg=SLATE_50, wraplength=430,
                                          justify="left", anchor="w")
            self.q_text_label.pack(fill="x", pady=(6, 18))
            self.options_holder = tk.Frame(self.quiz_card_inner, bg=SLATE_900)
            self.options_holder.pack()
            self.next_btn_holder = tk.Frame(self.quiz_card_inner, bg=SLATE_900)
            self.next_btn_holder.pack(pady=(16, 0))
            tk.Label(self.quiz_frame, text="Press 1-4 or A-D to answer \u00b7 Enter to continue",
                     font=FONT_SMALL, bg=SLATE_950, fg=SLATE_500).pack(pady=(0, 14))
        def start_quiz(self):
            """Kick off a new round: show a loading screen while a fresh batch of
            questions is generated in the background, then jump into the quiz."""
            self._loading_dots = 0
            self.show_frame(self.loading_frame)
            self._animate_loading()
            threading.Thread(target=self._generate_questions_worker, daemon=True).start()

        def _generate_questions_worker(self):
            """Runs off the main thread - does the (possibly slow) network call."""
            error = None
            questions = None
            try:
                questions = fetch_online_questions(QUESTIONS_PER_ROUND)
            except Exception as e:
                error = str(e)
            self.after(0, lambda: self._on_questions_ready(questions, error))

        def _on_questions_ready(self, questions, error):
            """Runs back on the main thread - safe to touch Tk widgets here."""
            self._stop_loading_animation()
            if error:
                messagebox.showerror(
                    "Couldn't load questions",
                    "Couldn't load questions online (" + error + ").\n\n"
                    "Check your internet connection and try again."
                )
                self.show_frame(self.dashboard_frame)
                return
            self.quiz_questions = questions
            self.current_q_index = 0
            self.score = 0
            self.answer_log = []
            self._quiz_active = True
            self.load_question()
            self.show_frame(self.quiz_frame)
        def load_question(self):
            q = self.quiz_questions[self.current_q_index]
            self.answered = False
            self.selected_index = None
            self.q_num_label.config(text=f"question {self.current_q_index + 1} of {len(self.quiz_questions)}")
            self.q_text_label.config(text=q["question"])
            self.score_label.config(text=f"score {self.score:02d}")
            draw_progress(self.progress_canvas, len(self.quiz_questions), self.current_q_index)
            for w in self.options_holder.winfo_children():
                w.destroy()
            for w in self.next_btn_holder.winfo_children():
                w.destroy()
            self.option_widgets = []
            for i, opt in enumerate(q["options"]):
                label = re.sub(r"^[A-D]\.\s*", "", opt)
                chip = OptionChip(self.options_holder, i, label, CHALK_ACCENTS[i],
                                   on_select=self.pick_option)
                chip.pack(pady=6)
                self.option_widgets.append(chip)
        def pick_option(self, index):
            if self.answered:
                return
            self.answered = True
            self.selected_index = index
            q = self.quiz_questions[self.current_q_index]
            correct_index = LETTERS.index(q["answer"])
            is_correct = index == correct_index
            for i, chip in enumerate(self.option_widgets):
                if i == correct_index:
                    chip.set_correct()
                elif i == index:
                    chip.set_wrong()
                else:
                    chip.set_dim()
            if is_correct:
                self.score += 1
                self.score_label.config(text=f"score {self.score:02d}")
            self.answer_log.append({
                "question": q["question"],
                "user_ans": LETTERS[index],
                "correct_ans": q["answer"],
                "correct": is_correct,
            })
            is_last = self.current_q_index + 1 >= len(self.quiz_questions)
            RoundedButton(
                self.next_btn_holder,
                "See results" if is_last else "Next question",
                command=self.advance_question,
                width=200, height=44, fill=SLATE_50, fg=SLATE_950, bg=SLATE_900,
            ).pack()
        def advance_question(self):
            if self.current_q_index + 1 < len(self.quiz_questions):
                self.current_q_index += 1
                self.load_question()
            else:
                self.finish_quiz()
        def _on_quiz_key(self, event):
            if not self._quiz_active:
                return
            if not self.answered:
                key = (event.char or "").upper()
                if key in LETTERS:
                    self.pick_option(LETTERS.index(key))
                elif key in ("1", "2", "3", "4"):
                    self.pick_option(int(key) - 1)
            else:
                if event.keysym in ("Return", "space"):
                    self.advance_question()
        def build_results_screen(self):
            self.results_frame = tk.Frame(self.container, bg=SLATE_950)
            self.results_frame.place(relwidth=1, relheight=1)
            self.build_topbar(self.results_frame)
            wrap = tk.Frame(self.results_frame, bg=SLATE_950)
            wrap.place(relx=0.5, rely=0.54, anchor="center")
            card, card_panel = make_card(wrap, accent=EMERALD_400)
            card.pack()
            inner = tk.Frame(card_panel, bg=SLATE_900)
            inner.pack(padx=40, pady=(24, 32))
            tk.Label(inner, text="QUIZ COMPLETE", font=FONT_SMALL_BOLD, bg=SLATE_900,
                     fg=SLATE_400).pack(pady=(0, 10))
            self.chart_canvas = tk.Canvas(inner, width=200, height=210, bg=SLATE_900,
                                           highlightthickness=0)
            self.chart_canvas.pack(pady=(0, 6))

            self.result_score_big = tk.Label(inner, text="", font=FONT_SCORE_BIG,
                                              bg=SLATE_900, fg=SLATE_50)
            self.result_score_big.pack()
            self.result_msg_label = tk.Label(inner, text="", font=FONT_BODY,
                                              bg=SLATE_900, fg=SLATE_400)
            self.result_msg_label.pack(pady=(2, 22))
            legend = tk.Frame(inner, bg=SLATE_900)
            legend.pack(pady=(0, 20))
            tk.Canvas(legend, width=12, height=12, bg=EMERALD_500,
                      highlightthickness=0).grid(row=0, column=0, padx=(0, 6))
            tk.Label(legend, text="Correct", font=FONT_SMALL, bg=SLATE_900,
                     fg=SLATE_400).grid(row=0, column=1, padx=(0, 18))
            tk.Canvas(legend, width=12, height=12, bg=ROSE_500,
                      highlightthickness=0).grid(row=0, column=2, padx=(0, 6))
            tk.Label(legend, text="Incorrect", font=FONT_SMALL, bg=SLATE_900,
                     fg=SLATE_400).grid(row=0, column=3)
            btn_row = tk.Frame(inner, bg=SLATE_900)
            btn_row.pack()
            RoundedButton(btn_row, "Review answers", command=self.show_review_screen,
                          width=170, height=44, fill=AMBER_400,
                          bg=SLATE_900).grid(row=0, column=0, padx=6)
            RoundedButton(btn_row, "Back to dashboard",
                          command=lambda: self.show_frame(self.dashboard_frame),
                          width=170, height=44, fill=SLATE_800, fg=SLATE_50,
                          bg=SLATE_900).grid(row=0, column=1, padx=6)
        def finish_quiz(self):
            self._quiz_active = False
            total = len(self.quiz_questions)
            today = datetime.date.today().strftime("%d/%m/%Y")
            try:
                with open(SCORES_FILE, "a") as f:
                    f.write(f"{self.current_user},{self.score},{total},{today}\n")
            except OSError as e:
                messagebox.showwarning("Warning", f"Could not save your score: {e}")
            self.show_results_screen(self.score, total)
        def draw_pie_chart(self, score, total):
            canvas = self.chart_canvas
            canvas.delete("all")
            cx, cy, r = 100, 100, 84
            percentage = (score / total * 100) if total else 0
            shadow = blend_hex(SLATE_900, "#000000", 0.35)
            canvas.create_oval(cx - r + 3, cy - r + 8, cx + r + 3, cy + r + 8,
                                fill=shadow, outline="")
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=SLATE_800, outline="")
            if total and score == 0:
                canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=ROSE_500, outline="")
            elif total and score == total:
                canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=EMERALD_500, outline="")
            elif total:
                extent = percentage / 100 * 360
                canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=90,
                                   extent=-extent, fill=EMERALD_500, outline=SLATE_900, width=2)
                canvas.create_arc(cx - r, cy - r, cx + r, cy + r, start=90 - extent,
                                   extent=-(360 - extent), fill=ROSE_500, outline=SLATE_900, width=2)
            inner_r = 50
            canvas.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                                fill=SLATE_900, outline="")
            canvas.create_text(cx, cy, text=f"{percentage:.0f}%", font=FONT_H1, fill=SLATE_50)
        def show_results_screen(self, score, total):
            if total and score == total:
                msg = "Perfect score - chalk one up."
            elif total and score >= total * 0.75:
                msg = "Sharp. Really sharp."
            elif total and score >= total * 0.5:
                msg = "Solid effort - keep practising."
            else:
                msg = "Room to grow. Go again?"
            self.result_score_big.config(text=f"{score}/{total}")
            self.result_msg_label.config(text=msg)
            self.draw_pie_chart(score, total)
            self.show_frame(self.results_frame)
        def build_review_screen(self):
            self.review_frame = tk.Frame(self.container, bg=SLATE_950)
            self.review_frame.place(relwidth=1, relheight=1)
            self.build_topbar(self.review_frame)
            tk.Label(self.review_frame, text="Answer review", font=FONT_H1,
                     bg=SLATE_950, fg=SLATE_50).pack(pady=(14, 10))
            card, card_panel = make_card(self.review_frame, accent=TEAL_400)
            card.pack(fill="both", expand=True, padx=24, pady=(0, 10))
            wrapper = tk.Frame(card_panel, bg=SLATE_900)
            wrapper.pack(fill="both", expand=True, padx=12, pady=(4, 12))
            scroll_canvas = tk.Canvas(wrapper, bg=SLATE_900, highlightthickness=0)
            scrollbar = tk.Scrollbar(wrapper, orient="vertical", command=scroll_canvas.yview,
                                      bg=SLATE_800, troughcolor=SLATE_900,
                                      activebackground=SLATE_700)
            scroll_canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            scroll_canvas.pack(side="left", fill="both", expand=True)
            self.review_inner = tk.Frame(scroll_canvas, bg=SLATE_900)
            self.review_window_id = scroll_canvas.create_window(
                (0, 0), window=self.review_inner, anchor="nw"
            )
            def on_frame_configure(_event):
                scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
            def on_canvas_configure(event):
                scroll_canvas.itemconfig(self.review_window_id, width=event.width)
            self.review_inner.bind("<Configure>", on_frame_configure)
            scroll_canvas.bind("<Configure>", on_canvas_configure)
            self.scroll_canvas_ref = scroll_canvas
            RoundedButton(self.review_frame, "Back to results",
                          command=lambda: self.show_frame(self.results_frame),
                          width=200, height=42, fill=SLATE_800, fg=SLATE_50,
                          bg=SLATE_950).pack(pady=(4, 16))
        def show_review_screen(self):
            for w in self.review_inner.winfo_children():
                w.destroy()
            for i, entry in enumerate(self.answer_log):
                row_bg = SLATE_900 if i % 2 == 0 else SLATE_800
                row = tk.Frame(self.review_inner, bg=row_bg, pady=10, padx=14)
                row.pack(fill="x", pady=3)
                if entry["correct"]:
                    mark, mark_color = "\u2713", EMERALD_400
                else:
                    mark, mark_color = "\u2715", ROSE_400
                tk.Label(row, text=mark, font=("Segoe UI", 14, "bold"), bg=row_bg,
                         fg=mark_color, width=2).grid(row=0, column=0, rowspan=2,
                                                       sticky="n", padx=(0, 10))
                tk.Label(row, text=f"Q{i + 1}. {entry['question']}", font=FONT_BODY_BOLD,
                         bg=row_bg, fg=SLATE_50, wraplength=430, justify="left",
                         anchor="w").grid(row=0, column=1, sticky="w")
                if entry["correct"]:
                    detail = f"Your answer: {entry['user_ans']} - correct"
                    detail_color = EMERALD_400
                else:
                    detail = f"Your answer: {entry['user_ans']}   Correct answer: {entry['correct_ans']}"
                    detail_color = ROSE_400
                tk.Label(row, text=detail, font=FONT_SMALL, bg=row_bg, fg=detail_color,
                         anchor="w", justify="left").grid(row=1, column=1, sticky="w")
            self.scroll_canvas_ref.yview_moveto(0)
            self.show_frame(self.review_frame)
        def build_scores_screen(self):
            self.scores_frame = tk.Frame(self.container, bg=SLATE_950)
            self.scores_frame.place(relwidth=1, relheight=1)
            self.build_topbar(self.scores_frame)
            tk.Label(self.scores_frame, text="Scores & leaderboard", font=FONT_H1,
                     bg=SLATE_950, fg=SLATE_50).pack(pady=(14, 12))
            card, card_panel = make_card(self.scores_frame, accent=VIOLET_400)
            card.pack(padx=24, pady=(0, 10), fill="both", expand=True)
            style = ttk.Style(self)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            style.configure("Dark.TNotebook", background=SLATE_900, borderwidth=0)
            style.configure("Dark.TNotebook.Tab", background=SLATE_900, foreground=SLATE_400,
                             padding=(16, 8), font=FONT_BODY_BOLD, borderwidth=0)
            style.map("Dark.TNotebook.Tab",
                      background=[("selected", SLATE_800)],
                      foreground=[("selected", AMBER_300)])
            notebook = ttk.Notebook(card_panel, style="Dark.TNotebook")
            notebook.pack(padx=12, pady=12, fill="both", expand=True)
            self.personal_tab = tk.Frame(notebook, bg=SLATE_900)
            notebook.add(self.personal_tab, text="Your attempts")
            self.personal_listbox = tk.Listbox(self.personal_tab, font=FONT_MONO,
                                                bg=SLATE_900, fg=SLATE_100,
                                                selectbackground=AMBER_400,
                                                selectforeground=SLATE_950,
                                                highlightthickness=0, borderwidth=0,
                                                activestyle="none")
            self.personal_listbox.pack(padx=10, pady=10, fill="both", expand=True)
            self.leaderboard_tab = tk.Frame(notebook, bg=SLATE_900)
            notebook.add(self.leaderboard_tab, text="Leaderboard")
            self.leaderboard_listbox = tk.Listbox(self.leaderboard_tab, font=FONT_MONO,
                                                   bg=SLATE_900, fg=SLATE_100,
                                                   selectbackground=AMBER_400,
                                                   selectforeground=SLATE_950,
                                                   highlightthickness=0, borderwidth=0,
                                                   activestyle="none")
            self.leaderboard_listbox.pack(padx=10, pady=10, fill="both", expand=True)
            RoundedButton(self.scores_frame, "Back to dashboard",
                          command=lambda: self.show_frame(self.dashboard_frame),
                          width=200, height=42, fill=SLATE_800, fg=SLATE_50,
                          bg=SLATE_950).pack(pady=(0, 16))
        def load_and_show_scores(self):
            self.personal_listbox.delete(0, tk.END)
            self.leaderboard_listbox.delete(0, tk.END)
            try:
                with open(SCORES_FILE, "r") as f:
                    lines = f.readlines()
            except OSError:
                lines = []
            my_scores = []
            all_scores = []
            for line in lines:
                line = line.strip()
                if line == "":
                    continue
                parts = line.split(",")
                if len(parts) == 4:
                    try:
                        record = [parts[0], int(parts[1]), int(parts[2]), parts[3]]
                    except ValueError:
                        continue
                    if record[2] <= 0:
                        continue
                    all_scores.append(record)
                    if parts[0] == self.current_user:
                        my_scores.append(record)
            if len(my_scores) == 0:
                self.personal_listbox.insert(tk.END, "  No attempts yet - start a quiz from the dashboard.")
            else:
                for i, r in enumerate(my_scores):
                    pct = r[1] / r[2] * 100
                    self.personal_listbox.insert(
                        tk.END, f"  Attempt {i + 1}   {r[1]}/{r[2]}  ({pct:.0f}%)   {r[3]}"
                    )
            if len(all_scores) == 0:
                self.leaderboard_listbox.insert(tk.END, "  No scores recorded yet - be the first!")
            else:
                all_scores.sort(key=lambda r: r[1] / r[2], reverse=True)
                medals = {0: "\U0001F947", 1: "\U0001F948", 2: "\U0001F949"}
                for count, r in enumerate(all_scores[:10]):
                    pct = r[1] / r[2] * 100
                    rank_label = medals.get(count, f"{count + 1}.")
                    self.leaderboard_listbox.insert(
                        tk.END, f"  {rank_label:<3} {r[0]:<14} {r[1]}/{r[2]}  ({pct:.0f}%)   {r[3]}"
                    )
            self.show_frame(self.scores_frame)
    ensure_files_exist()
    app = QuizApp()
    app.mainloop()
def run_web(host="127.0.0.1", port=5000, debug=True):
    import threading
    import webbrowser
    from flask import Flask, session, request, redirect, url_for, render_template_string

    app = Flask(__name__)
    app.secret_key = "chalkquiz-dev-secret-change-me"  # fine for local dev only
    BASE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#020617">
<title>ChalkQuiz</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --slate-950:#020617; --slate-900:#0f172a; --slate-850:#131f38; --slate-800:#1e293b;
    --slate-700:#334155; --slate-500:#64748b; --slate-400:#94a3b8;
    --slate-100:#f1f5f9; --slate-50:#f8fafc;
    --amber-200:#fde68a; --amber-300:#fcd34d; --amber-400:#fbbf24;
    --sky-400:#38bdf8; --violet-400:#a78bfa; --teal-400:#2dd4bf;
    --emerald-400:#34d399; --emerald-500:#10b981;
    --rose-400:#fb7185; --rose-500:#f43f5e;
    --font-display:'Manrope','Segoe UI',system-ui,sans-serif;
    --font-body:'Inter','Segoe UI',system-ui,sans-serif;
    --font-mono:'JetBrains Mono',Consolas,monospace;
    --radius-lg:20px; --radius-pill:999px;
    --shadow-card:0 1px 0 rgba(255,255,255,0.03) inset, 0 16px 40px -16px rgba(0,0,0,0.65);
    --ease:cubic-bezier(.2,.7,.3,1);
  }
  * { box-sizing: border-box; }
  html { -webkit-tap-highlight-color: transparent; }
  body {
    background:
      radial-gradient(60rem 30rem at 12% -10%, rgba(56,189,248,0.09), transparent 60%),
      radial-gradient(50rem 26rem at 110% 8%, rgba(251,191,36,0.08), transparent 55%),
      radial-gradient(46rem 26rem at 50% 120%, rgba(167,139,250,0.07), transparent 55%),
      var(--slate-950);
    color: var(--slate-50);
    font-family: var(--font-body);
    margin: 0; min-height: 100vh; display:flex; flex-direction:column;
    -webkit-font-smoothing: antialiased;
  }
  ::selection { background: var(--amber-400); color: var(--slate-950); }
  .dust { position:fixed; inset:0; pointer-events:none; z-index:0; overflow:hidden; }
  .dust::before, .dust::after {
    content:""; position:absolute; inset:-10%;
    background-image:
      radial-gradient(2px 2px at 10% 20%, rgba(251,191,36,.35), transparent 60%),
      radial-gradient(2px 2px at 80% 10%, rgba(56,189,248,.3), transparent 60%),
      radial-gradient(1.5px 1.5px at 60% 70%, rgba(167,139,250,.3), transparent 60%),
      radial-gradient(1.5px 1.5px at 30% 85%, rgba(45,212,191,.3), transparent 60%),
      radial-gradient(2px 2px at 90% 60%, rgba(251,191,36,.25), transparent 60%);
    animation: drift 34s linear infinite;
  }
  .dust::after { animation-duration: 52s; animation-direction: reverse; opacity:.6; }
  @keyframes drift {
    from { transform: translate3d(0,0,0); }
    to { transform: translate3d(-4%,4%,0); }
  }
  .topbar { position:sticky; top:0; z-index:2; display:flex; justify-content:space-between;
    align-items:center; padding: 16px 32px; font-family: var(--font-display);
    background: rgba(2,6,23,0.55); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    border-bottom: 1px solid rgba(255,255,255,0.05); }
  .brand { position:relative; font-weight:800; font-size:16px; letter-spacing:-0.01em;
    padding-bottom: 7px; }
  .brand::after { content:""; position:absolute; left:1px; right:auto; bottom:0; width:74%;
    height:4px; background-image: radial-gradient(circle, var(--amber-300) 1.4px, transparent 1.6px);
    background-size: 7px 4px; background-repeat: repeat-x; opacity:.6; }
  .brand .quiz { color: var(--amber-300); }
  .user { display:flex; align-items:center; gap:9px; color: var(--slate-400);
    font-family: var(--font-mono); font-size:13px; }
  .avatar { width:26px; height:26px; border-radius:50%; display:flex; align-items:center;
    justify-content:center; font-family: var(--font-display); font-weight:700; font-size:12px;
    color: var(--slate-950);
    background: linear-gradient(135deg, var(--sky-400), var(--violet-400)); }
  .wrap { position:relative; z-index:1; flex:1; display:flex; align-items:center;
    justify-content:center; padding: 24px; }
  .card {
    background: linear-gradient(180deg, var(--slate-850), var(--slate-900));
    border:1px solid var(--slate-800); border-radius: var(--radius-lg);
    padding: 34px 38px; width: 100%; max-width: 480px;
    box-shadow: var(--shadow-card);
    animation: rise .5s var(--ease) both;
    transition: transform .2s var(--ease), box-shadow .2s var(--ease);
  }
  .card:hover { transform: translateY(-2px);
    box-shadow: 0 1px 0 rgba(255,255,255,0.04) inset, 0 22px 48px -18px rgba(0,0,0,.7); }
  .icon-badge { width:46px; height:46px; border-radius:14px; display:flex; align-items:center;
    justify-content:center; margin-bottom:14px;
    box-shadow: 0 1px 0 rgba(255,255,255,.15) inset; }
  .icon-badge svg { width:22px; height:22px; }
  h1 { font-family: var(--font-display); font-weight:800; letter-spacing:-0.01em;
    font-size: 23px; margin: 0 0 6px; }
  .sub { color: var(--slate-400); font-size: 14px; margin-bottom: 20px; }
  label { display:block; font-size: 11px; font-weight:600; text-transform:uppercase;
    letter-spacing:.06em; color: var(--slate-500); margin: 14px 0 6px; }
  input[type=text], input[type=password] {
    width: 100%; padding: 11px 14px; background: var(--slate-800); color: var(--slate-50);
    border: 1px solid var(--slate-700); border-radius: 10px; font-size: 14px;
    font-family: var(--font-body);
    transition: border-color .15s var(--ease), box-shadow .15s var(--ease);
  }
  input[type=text]:hover, input[type=password]:hover { border-color: var(--slate-500); }
  input:focus-visible {
    outline: none; border-color: var(--amber-400);
    box-shadow: 0 0 0 3px rgba(251,191,36,0.22);
  }
  .btn {
    display:inline-flex; align-items:center; justify-content:center; gap:8px;
    text-decoration:none; text-align:center; cursor:pointer;
    background: linear-gradient(180deg, var(--amber-300), var(--amber-400));
    color: var(--slate-950); font-weight:700; font-family: var(--font-display);
    padding: 13px 22px; border-radius: var(--radius-pill); border:none; font-size:14px;
    width:100%; margin-top: 16px; box-sizing:border-box;
    box-shadow: 0 1px 0 rgba(255,255,255,.35) inset, 0 10px 22px -10px rgba(251,191,36,.6);
    transition: transform .15s var(--ease), box-shadow .15s var(--ease), filter .15s var(--ease);
  }
  .btn:hover { filter: brightness(1.05); transform: translateY(-1px);
    box-shadow: 0 1px 0 rgba(255,255,255,.35) inset, 0 14px 26px -10px rgba(251,191,36,.7); }
  .btn:active { transform: translateY(0); filter: brightness(.97); }
  .btn:focus-visible { outline: 2px solid var(--amber-200); outline-offset: 2px; }
  .btn.secondary {
    background: var(--slate-800); color: var(--slate-50);
    box-shadow: 0 1px 0 rgba(255,255,255,.04) inset, 0 10px 22px -14px rgba(0,0,0,.7);
  }
  .btn.secondary:hover { background: var(--slate-700); }
  .btn-icon { width:17px; height:17px; flex-shrink:0; }
  .link { color: var(--amber-300); font-size: 13px; text-decoration:none;
    border-bottom: 1px dashed rgba(252,211,77,.4); transition: color .15s var(--ease); }
  .link:hover { color: var(--amber-200); }
  .msg { text-align:center; margin-top: 16px; }
  .flash { display:flex; align-items:center; gap:8px; background: rgba(244,63,94,.1);
    border:1px solid var(--rose-500);
    color: var(--rose-400); padding: 10px 14px; border-radius: 10px; font-size: 13px;
    margin-bottom: 14px; }
  .flash.ok { border-color: var(--emerald-500); color: var(--emerald-400);
    background: rgba(16,185,129,.1); }
  .progress { display:flex; gap:6px; padding: 22px 32px 0; }
  .seg { width:22px; height:6px; border-radius:3px; background: var(--slate-800);
    transition: background .25s var(--ease); }
  .seg.done { background: linear-gradient(90deg, var(--amber-300), var(--amber-400)); }
  .seg.now { background: rgba(251,191,36,.35); }
  .score-tag { font-family: var(--font-mono); font-weight:600; color: var(--slate-400);
    float:right; }
  .qcard {
    background: linear-gradient(180deg, var(--slate-850), var(--slate-900));
    border:1px solid var(--slate-800); border-radius: var(--radius-lg);
    padding: 26px 28px; max-width: 560px; width:100%;
    box-shadow: var(--shadow-card);
    animation: rise .45s var(--ease) both;
  }
  .qnum { color: var(--slate-500); font-family: var(--font-mono); font-size:12px;
    text-transform:uppercase; letter-spacing:.06em; }
  .qtext { font-family: var(--font-display); font-size: 19px; font-weight:700;
    letter-spacing:-0.01em; line-height:1.35; margin: 10px 0 20px; }
  .opt { display:flex; align-items:center; gap:14px; background: var(--slate-800);
    border: 1.5px solid var(--slate-700); border-radius: var(--radius-pill);
    padding: 13px 20px 13px 14px; margin-bottom: 10px; text-decoration:none;
    color: var(--slate-100); font-size:14.5px; font-family: var(--font-body);
    transition: transform .12s var(--ease), border-color .15s var(--ease),
      box-shadow .15s var(--ease); }
  .opt:hover { cursor:pointer; border-color: var(--slate-500); transform: translateY(-1px);
    box-shadow: 0 10px 20px -12px rgba(0,0,0,.75); }
  .opt:focus-visible { outline: 2px solid var(--amber-300); outline-offset: 2px; }
  .opt .badge { width:30px; height:30px; border-radius:50%; background: var(--slate-700);
    color: var(--slate-50); display:flex; align-items:center; justify-content:center;
    font-weight:700; font-family: var(--font-display); font-size:13px; flex-shrink:0;
    box-shadow: 0 1px 0 rgba(255,255,255,.08) inset; }
  form.opt-form { margin:0; }
  .opt-btn { all:unset; box-sizing:border-box; display:flex; align-items:center; gap:14px;
    width:100%; background: var(--slate-800); border: 1.5px solid var(--slate-700);
    border-radius: var(--radius-pill); padding: 13px 20px 13px 14px; margin-bottom: 10px;
    color: var(--slate-100); font-size:14.5px; font-family: var(--font-body); cursor:pointer;
    transition: transform .12s var(--ease), border-color .15s var(--ease),
      box-shadow .15s var(--ease); }
  .opt-btn .badge { width:30px; height:30px; border-radius:50%; background: var(--slate-700);
    color: var(--slate-50); display:flex; align-items:center; justify-content:center;
    font-weight:700; font-family: var(--font-display); font-size:13px; flex-shrink:0;
    box-shadow: 0 1px 0 rgba(255,255,255,.08) inset; }
  .badge-A { background: var(--sky-400); color: var(--slate-950); }
  .badge-B { background: var(--violet-400); color: var(--slate-950); }
  .badge-C { background: var(--amber-400); color: var(--slate-950); }
  .badge-D { background: var(--teal-400); color: var(--slate-950); }
  .opt-btn.correct { background: rgba(16,185,129,.14); border-color: var(--emerald-400); }
  .opt-btn.wrong { background: rgba(244,63,94,.14); border-color: var(--rose-400); }
  .opt-btn.dim { opacity: .4; }
  .opt-btn .badge.correct-badge { background: var(--emerald-400); color: var(--slate-950); }
  .opt-btn .badge.wrong-badge { background: var(--rose-400); color: var(--slate-950); }
  .center { text-align:center; }
  .big-score { font-family: var(--font-mono); font-size: 46px; font-weight:700;
    letter-spacing:-0.02em; margin: 12px 0 0; }
  .card.perfect { box-shadow: var(--shadow-card), 0 0 0 1px rgba(251,191,36,.25),
    0 0 60px -10px rgba(251,191,36,.35); }
  .celebrate { font-size: 28px; letter-spacing:.15em; margin: 2px 0 12px; }
  table { width:100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 13px; }
  td, th { padding: 9px 8px; border-bottom: 1px solid var(--slate-800); text-align:left; }
  th { color: var(--slate-500); font-weight:600; text-transform:uppercase; font-size:11px;
    letter-spacing:.06em; }
  tr:hover td { background: rgba(255,255,255,.02); }
  td.rank { font-size:15px; font-family: var(--font-display); font-weight:700;
    color: var(--slate-400); width: 34px; }
  tr:nth-child(-n+3) td.rank { font-size:18px; }
  .empty-row td { text-align:center; color: var(--slate-500); padding: 22px 8px;
    font-family: var(--font-body); }
  .correct-text { color: var(--emerald-400); }
  .wrong-text { color: var(--rose-400); }
  @keyframes rise { from { opacity:0; transform: translateY(10px); } to { opacity:1; transform: translateY(0); } }
  @media (max-width: 520px) {
    .card, .qcard { padding: 24px 20px; border-radius:16px; }
    .topbar { padding: 14px 18px; }
    .progress { padding: 18px 18px 0; }
    .qtext { font-size:17px; }
  }
  @media (prefers-reduced-motion: reduce) {
    .card, .qcard, .btn, .opt, .opt-btn, .seg { animation: none !important; transition: none !important; }
    .dust::before, .dust::after { animation: none !important; }
  }
</style>
</head>
<body>
  <div class="dust" aria-hidden="true"></div>
  <div class="topbar">
    <div class="brand">Chalk<span class="quiz">Quiz</span></div>
    <div class="user">
      {% if session.get('username') %}<span class="avatar">{{ session.get('username')[0]|upper }}</span>{% endif %}
      {{ session.get('username','') }}
    </div>
  </div>
  <div class="wrap">
    {{ body|safe }}
  </div>
</body>
</html>
"""
    def render(body, **ctx):
        return render_template_string(BASE, body=render_template_string(body, **ctx))
    @app.route("/")
    def home():
        if session.get("username"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))
    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            users = load_users()
            if username in users and users[username] == password:
                session["username"] = username
                return redirect(url_for("dashboard"))
            error = "Wrong username or password."
        body = """
        <div class="card">
          <div class="icon-badge" style="background:rgba(56,189,248,.15); color:var(--sky-400);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="4" y="11" width="16" height="9" rx="2"></rect>
              <path d="M8 11V7a4 4 0 0 1 8 0v4"></path>
            </svg>
          </div>
          <h1>Log in</h1>
          <div class="sub">Welcome back.</div>
          {% if error %}<div class="flash">{{ error }}</div>{% endif %}
          <form method="post">
            <label>Username</label>
            <input type="text" name="username" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <button class="btn" type="submit">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"></path></svg>
              Log in
            </button>
          </form>
          <div class="msg"><a class="link" href="{{ url_for('register') }}">Need an account? Register</a></div>
        </div>
        """
        return render(body, error=error)
    @app.route("/register", methods=["GET", "POST"])
    def register():
        error = None
        success = None
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            users = load_users()
            if not username:
                error = "Username can't be blank."
            elif "," in username:
                error = "Username can't contain a comma."
            elif username in users:
                error = "That username already exists."
            elif not password:
                error = "Password can't be blank."
            else:
                with open(USERS_FILE, "a") as f:
                    f.write(f"{username},{password}\n")
                success = "Account created - you can log in now."
        body = """
        <div class="card">
          <div class="icon-badge" style="background:rgba(167,139,250,.15); color:var(--violet-400);">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M19 8v6M22 11h-6"></path>
            </svg>
          </div>
          <h1>Create account</h1>
          <div class="sub">Choose a username and password.</div>
          {% if error %}<div class="flash">{{ error }}</div>{% endif %}
          {% if success %}<div class="flash ok">{{ success }}</div>{% endif %}
          <form method="post">
            <label>Username</label>
            <input type="text" name="username" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <button class="btn" type="submit">
              <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5v14M5 12h14"></path></svg>
              Create account
            </button>
          </form>
          <div class="msg"><a class="link" href="{{ url_for('login') }}">Back to log in</a></div>
        </div>
        """
        return render(body, error=error, success=success)
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))
    def require_login():
        return session.get("username") is not None
    @app.route("/dashboard")
    def dashboard():
        if not require_login():
            return redirect(url_for("login"))
        error = request.args.get("error")
        body = """
        <div class="card center">
          <h1>Welcome back, {{ session.get('username') }}</h1>
          <div class="sub">Ready for another round?</div>
          {% if error %}<div class="flash">{{ error }}</div>{% endif %}
          <a class="btn" href="{{ url_for('start_quiz') }}">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"></polygon></svg>
            Start quiz
          </a>
          <a class="btn secondary" href="{{ url_for('scores') }}">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0V4Z"></path><path d="M5 4H3v2a4 4 0 0 0 4 4M19 4h2v2a4 4 0 0 1-4 4"></path></svg>
            View scores &amp; leaderboard
          </a>
          <div class="msg"><a class="link" href="{{ url_for('logout') }}">Log out</a></div>
        </div>
        """
        return render(body, error=error)
    @app.route("/start_quiz")
    def start_quiz():
        if not require_login():
            return redirect(url_for("login"))
        try:
            questions = fetch_online_questions(QUESTIONS_PER_ROUND)
        except Exception:
            return redirect(url_for(
                "dashboard",
                error="Couldn't load questions online. Check your connection and try again."
            ))
        session["quiz_questions"] = questions
        session["current_q_index"] = 0
        session["score"] = 0
        session["answer_log"] = []
        return redirect(url_for("quiz"))
    @app.route("/quiz")
    def quiz():
        if not require_login() or "quiz_questions" not in session:
            return redirect(url_for("dashboard"))
        questions = session["quiz_questions"]
        idx = session["current_q_index"]
        q = questions[idx]
        segs = "".join(
            f'<div class="seg {"done" if i < idx else ("now" if i == idx else "")}"></div>'
            for i in range(len(questions))
        )
        opts_html = "".join(
            f'<a class="opt" href="{{{{ url_for("answer", choice={i}) }}}}">'
            f'<span class="badge badge-{LETTERS[i]}">{LETTERS[i]}</span>{opt[3:]}</a>'
            for i, opt in enumerate(q["options"])
        )
        body = f"""
        <div style="width:100%; max-width:560px;">
          <div class="progress">{segs}</div>
          <div style="padding:0 30px;"><span class="score-tag">score {session['score']:02d}</span></div>
          <div class="qcard" style="margin-top:14px;">
            <div class="qnum">question {idx + 1} of {len(questions)}</div>
            <div class="qtext">{html.escape(q['question'])}</div>
            {opts_html}
          </div>
        </div>
        """
        return render(body)
    @app.route("/answer")
    def answer():
        if not require_login() or "quiz_questions" not in session:
            return redirect(url_for("dashboard"))
        choice = int(request.args.get("choice", -1))
        questions = session["quiz_questions"]
        idx = session["current_q_index"]
        q = questions[idx]
        correct_index = LETTERS.index(q["answer"])
        is_correct = choice == correct_index
        if is_correct:
            session["score"] = session["score"] + 1
        log = session["answer_log"]
        log.append({
            "question": q["question"],
            "user_ans": LETTERS[choice] if 0 <= choice < 4 else "?",
            "correct_ans": q["answer"],
            "correct": is_correct,
        })
        session["answer_log"] = log
        opts_html = ""
        for i, opt in enumerate(q["options"]):
            cls = ""
            badge_cls = f"badge-{LETTERS[i]}"
            if i == correct_index:
                cls, badge_cls = "correct", "correct-badge"
            elif i == choice:
                cls, badge_cls = "wrong", "wrong-badge"
            else:
                cls, badge_cls = "dim", ""
            opts_html += (
                f'<div class="opt-btn {cls}"><span class="badge {badge_cls}">{LETTERS[i]}</span>'
                f'{html.escape(opt[3:])}</div>'
            )
        is_last = idx + 1 >= len(questions)
        next_url = url_for("results") if is_last else url_for("next_question")
        next_label = "See results" if is_last else "Next question"
        segs = "".join(
            f'<div class="seg {"done" if i <= idx else ""}"></div>' for i in range(len(questions))
        )
        body = f"""
        <div style="width:100%; max-width:560px;">
          <div class="progress">{segs}</div>
          <div style="padding:0 30px;"><span class="score-tag">score {session['score']:02d}</span></div>
          <div class="qcard" style="margin-top:14px;">
            <div class="qnum">question {idx + 1} of {len(questions)}</div>
            <div class="qtext">{html.escape(q['question'])}</div>
            {opts_html}
            <a class="btn" href="{next_url}">{next_label}</a>
          </div>
        </div>
        """
        return render(body)
    @app.route("/next_question")
    def next_question():
        if not require_login() or "quiz_questions" not in session:
            return redirect(url_for("dashboard"))
        session["current_q_index"] = session["current_q_index"] + 1
        return redirect(url_for("quiz"))
    @app.route("/results")
    def results():
        if not require_login() or "quiz_questions" not in session:
            return redirect(url_for("dashboard"))
        total = len(session["quiz_questions"])
        score = session["score"]
        today = datetime.date.today().strftime("%d/%m/%Y")
        with open(SCORES_FILE, "a") as f:
            f.write(f"{session['username']},{score},{total},{today}\n")
        pct = (score / total * 100) if total else 0
        if total and score == total:
            msg = "Perfect score - chalk one up."
        elif total and score >= total * 0.75:
            msg = "Sharp. Really sharp."
        elif total and score >= total * 0.5:
            msg = "Solid effort - keep practising."
        else:
            msg = "Room to grow. Go again?"
        card_class = "card center perfect" if (total and score == total) else "card center"
        celebrate = (
            '<div class="celebrate">\U0001F389 \u2728 \U0001F389</div>'
            if (total and score == total) else ""
        )
        body = f"""
        <div class="{card_class}">
          {celebrate}
          <div class="sub">QUIZ COMPLETE</div>
          <div class="big-score">{score}/{total}</div>
          <div class="sub">{msg} ({pct:.0f}%)</div>
          <a class="btn" href="{{{{ url_for('review') }}}}">
            <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18l6-6-6-6"></path></svg>
            Review answers
          </a>
          <a class="btn secondary" href="{{{{ url_for('dashboard') }}}}">Back to dashboard</a>
        </div>
        """
        return render(body)
    @app.route("/review")
    def review():
        if not require_login() or "answer_log" not in session:
            return redirect(url_for("dashboard"))
        rows = ""
        for i, e in enumerate(session["answer_log"]):
            if e["correct"]:
                detail = f'<span class="correct-text">Your answer: {e["user_ans"]} - correct</span>'
            else:
                detail = (f'<span class="wrong-text">Your answer: {e["user_ans"]} '
                           f'&nbsp; Correct answer: {e["correct_ans"]}</span>')
            rows += (f'<tr><td>Q{i+1}</td><td>{html.escape(e["question"])}<br>{detail}</td></tr>')
        body = f"""
        <div class="card" style="max-width:600px;">
          <h1>Answer review</h1>
          <table>{rows}</table>
          <a class="btn secondary" href="{{{{ url_for('results') }}}}">Back to results</a>
        </div>
        """
        return render(body)
    @app.route("/scores")
    def scores():
        if not require_login():
            return redirect(url_for("login"))
        with open(SCORES_FILE, "r") as f:
            lines = f.readlines()
        my_scores, all_scores = [], []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) == 4:
                try:
                    record = [parts[0], int(parts[1]), int(parts[2]), parts[3]]
                except ValueError:
                    continue
                if record[2] <= 0:
                    continue
                all_scores.append(record)
                if parts[0] == session["username"]:
                    my_scores.append(record)
        mine_html = "".join(
            f"<tr><td class='rank'>#{i+1}</td><td>{r[1]}/{r[2]}</td>"
            f"<td>{(r[1]/r[2]*100):.0f}%</td><td>{r[3]}</td></tr>"
            for i, r in enumerate(my_scores)
        ) or ("<tr class='empty-row'><td colspan='4'>You haven't taken a round yet - "
              "start a quiz from the dashboard.</td></tr>")
        all_scores.sort(key=lambda r: r[1] / r[2], reverse=True)
        medals = {1: "\U0001F947", 2: "\U0001F948", 3: "\U0001F949"}
        board_html = "".join(
            f"<tr><td class='rank'>{medals.get(i + 1, f'#{i + 1}')}</td>"
            f"<td>{html.escape(r[0])}</td><td>{r[1]}/{r[2]}</td>"
            f"<td>{(r[1]/r[2]*100):.0f}%</td><td>{r[3]}</td></tr>"
            for i, r in enumerate(all_scores[:10])
        ) or "<tr class='empty-row'><td colspan='5'>No scores recorded yet - be the first!</td></tr>"
        body = f"""
        <div class="card" style="max-width:600px;">
          <h1>Your attempts</h1>
          <table><tr><th>#</th><th>Score</th><th>%</th><th>Date</th></tr>{mine_html}</table>
          <h1 style="margin-top:24px;">Leaderboard</h1>
          <table><tr><th>#</th><th>User</th><th>Score</th><th>%</th><th>Date</th></tr>{board_html}</table>
          <a class="btn secondary" href="{{{{ url_for('dashboard') }}}}">Back to dashboard</a>
        </div>
        """
        return render(body)
    ensure_files_exist()

    def _open_browser():
        browser_host = "127.0.0.1" if host == "0.0.0.0" else host
        webbrowser.open(f"http://{browser_host}:{port}/")
    threading.Timer(1.0, _open_browser).start()
    print(f"Starting ChalkQuiz - opening http://{host}:{port}/ in your browser...")

    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
def _prompt_mode():
    print("=" * 40)
    print(" ChalkQuiz")
    print("=" * 40)
    print("  1) Desktop app (opens a Tkinter window)")
    print("  2) Web app (starts a local server, open in your browser)")
    while True:
        choice = input("Choose 1 or 2: ").strip().lower()
        if choice in ("1", "desktop", "d"):
            return "desktop"
        if choice in ("2", "web", "w"):
            return "web"
        print("Please enter 1 or 2.")
def main():
    ensure_files_exist()
    args = [a.lower() for a in sys.argv[1:]]
    if "desktop" in args or "gui" in args:
        mode = "desktop"
    elif "web" in args:
        mode = "web"
    else:
        mode = _prompt_mode()

    if mode == "desktop":
        run_desktop()
    else:
        run_web()
if __name__ == "__main__":
    main()