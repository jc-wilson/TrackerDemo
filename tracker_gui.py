import ast
import subprocess
import sys
from pathlib import Path
import tkinter as tk


PROJECT_ROOT = Path(__file__).resolve().parent
ANALYSIS_PATH = PROJECT_ROOT / "analysis.py"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"

STAT_ORDER = [
    "Games Played",
    "Playtime",
    "ADR",
    "ACS",
    "K/D",
    "K/R",
    "Entry Success Rate %",
    "Entry Attempt Rate %",
    "KAST %",
    "Round Win %",
    "HS %",
    "HS % Received",
]

VIEW_CONFIG = {
    "all": {
        "label": "All Stats",
        "analysis_label": "Stats in all games",
        "tagline": "Complete competitive sample",
    },
    "won": {
        "label": "Won Games",
        "analysis_label": "Stats in games won",
        "tagline": "Performance when closing matches out",
    },
    "lost": {
        "label": "Lost Games",
        "analysis_label": "Stats in games lost",
        "tagline": "Performance in matches that slipped away",
    },
    "won_rounds": {
        "label": "Won Rounds",
        "analysis_label": "Stats in rounds won",
        "tagline": "Round wins only",
    },
    "lost_rounds": {
        "label": "Lost Rounds",
        "analysis_label": "Stats in rounds lost",
        "tagline": "Round losses only",
    },
}

ROUND_VIEW_KEYS = {"won_rounds", "lost_rounds"}

COLORS = {
    "bg": "#09111d",
    "panel": "#101c2f",
    "panel_alt": "#14243c",
    "panel_edge": "#203149",
    "text": "#f3f7fb",
    "muted": "#8da2be",
    "subtle": "#5f7189",
    "accent": "#ff5c75",
    "accent_soft": "#32212d",
    "divider": "#1d2d46",
    "good": "#4bd7a8",
}


def get_python_executable():
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def _parse_analysis_output(stdout):
    expected = {
        "player info": None,
        "Stats in all games": None,
        "Stats in games won": None,
        "Stats in games lost": None,
        "Stats in rounds won": None,
        "Stats in rounds lost": None,
        "Stats by server": {},
    }

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line or ": " not in line:
            continue

        prefix, _, payload = line.partition(": ")
        if prefix not in expected:
            continue

        try:
            expected[prefix] = ast.literal_eval(payload)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(f"Could not parse '{prefix}' from analysis output.") from exc

    missing = [label for label, value in expected.items() if value is None]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"Missing expected analysis sections: {joined}")

    return {
        "player_info": expected["player info"],
        "stats": {
            "all": expected["Stats in all games"],
            "won": expected["Stats in games won"],
            "lost": expected["Stats in games lost"],
            "won_rounds": expected["Stats in rounds won"],
            "lost_rounds": expected["Stats in rounds lost"],
        },
        "server_stats": expected["Stats by server"] or {},
    }


def load_stats_payload():
    if not ANALYSIS_PATH.exists():
        raise FileNotFoundError(f"Could not find {ANALYSIS_PATH.name}.")

    result = subprocess.run(
        [get_python_executable(), str(ANALYSIS_PATH)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip() or "analysis.py exited with a non-zero status."
        raise RuntimeError(stderr)

    return _parse_analysis_output(result.stdout)


def format_stat_value(name, value):
    if value in (None, ""):
        return "N/A"

    if isinstance(value, float):
        if name in {"K/D", "K/R"}:
            return f"{value:.2f}"
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"

    return str(value)


def coerce_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def coerce_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class StatCard(tk.Frame):
    def __init__(self, master, stat_name):
        super().__init__(
            master,
            bg=COLORS["panel"],
            highlightbackground=COLORS["panel_edge"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=16,
        )
        self.stat_name = stat_name

        accent = tk.Canvas(
            self,
            width=10,
            height=56,
            bg=COLORS["panel"],
            highlightthickness=0,
            bd=0,
        )
        accent.create_rectangle(0, 0, 4, 56, fill=COLORS["divider"], outline="")
        accent.create_rectangle(0, 14, 4, 42, fill=COLORS["accent"], outline="")
        accent.grid(row=0, column=0, rowspan=2, sticky="ns")

        label = tk.Label(
            self,
            text=stat_name,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Bahnschrift SemiBold", 12),
            anchor="w",
        )
        label.grid(row=0, column=1, sticky="w", padx=(12, 12))

        self.value_label = tk.Label(
            self,
            text="N/A",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Bahnschrift SemiBold", 25),
            anchor="w",
        )
        self.value_label.grid(row=1, column=1, sticky="w", padx=(12, 12), pady=(6, 0))

        dots = tk.Canvas(
            self,
            width=14,
            height=42,
            bg=COLORS["panel"],
            highlightthickness=0,
            bd=0,
        )
        for index in range(3):
            top = 5 + (index * 12)
            dots.create_oval(4, top, 10, top + 6, fill=COLORS["accent"], outline="")
        dots.grid(row=0, column=2, rowspan=2, sticky="ne")

        self.grid_columnconfigure(1, weight=1)

    def update_value(self, value):
        self.value_label.configure(text=value)


class TrackerStatsApp(tk.Tk):
    def __init__(self, payload=None, error_message=None):
        super().__init__()
        self.title("Tracker Demo Overview")
        self.geometry("1120x760")
        self.minsize(980, 660)
        self.configure(bg=COLORS["bg"])

        self.payload = payload
        self.error_message = error_message
        self.active_view = "all"
        self.active_server = None
        self.toggle_buttons = {}
        self.metric_cards = {}
        self.server_var = tk.StringVar(value="Server")
        self.server_button = None

        self._build_shell()
        if self.error_message:
            self._render_error_state()
        else:
            self._build_dashboard()
            self.show_view(self.active_view)

    def _build_shell(self):
        self.outer = tk.Frame(self, bg=COLORS["bg"], padx=26, pady=24)
        self.outer.pack(fill="both", expand=True)

        self.header_label = tk.Label(
            self.outer,
            text="Tracker Demo Overview",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            font=("Bahnschrift SemiBold", 24),
            anchor="w",
        )
        self.header_label.pack(anchor="w")

        self.main_panel = tk.Frame(
            self.outer,
            bg=COLORS["panel_alt"],
            highlightbackground=COLORS["panel_edge"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=18,
        )
        self.main_panel.pack(fill="both", expand=True)

    def _render_error_state(self):
        card = tk.Frame(
            self.main_panel,
            bg=COLORS["panel"],
            highlightbackground=COLORS["panel_edge"],
            highlightthickness=1,
            bd=0,
            padx=28,
            pady=28,
        )
        card.pack(fill="both", expand=True)

        tk.Label(
            card,
            text="Stats could not be loaded",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Bahnschrift SemiBold", 24),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            card,
            text="The GUI could not parse the current output from analysis.py.",
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 11),
            anchor="w",
        ).pack(anchor="w", pady=(8, 18))

        message = self.error_message.strip() if self.error_message else "Unknown error."
        tk.Label(
            card,
            text=message,
            bg=COLORS["panel"],
            fg=COLORS["accent"],
            font=("Consolas", 11),
            justify="left",
            wraplength=860,
            anchor="w",
        ).pack(anchor="w")

    def _build_dashboard(self):
        self.player_info = self.payload["player_info"]
        self.stats_by_view = self.payload["stats"]
        self.server_stats_by_name = self.payload.get("server_stats", {})

        self._build_hero()
        self._build_toggle()
        self._build_cards()

    def _build_hero(self):
        hero = tk.Frame(
            self.main_panel,
            bg=COLORS["panel"],
            highlightbackground=COLORS["panel_edge"],
            highlightthickness=1,
            bd=0,
            padx=22,
            pady=20,
        )
        hero.pack(fill="x")
        hero.grid_columnconfigure(0, weight=3)
        hero.grid_columnconfigure(1, weight=2)

        player_name = self.player_info.get("name") or "Unknown Player"
        player_tag = self.player_info.get("tag") or "N/A"

        left = tk.Frame(hero, bg=COLORS["panel"])
        left.grid(row=0, column=0, sticky="nsew")

        tk.Label(
            left,
            text=f"{player_name} #{player_tag}",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Bahnschrift SemiBold", 28),
            anchor="w",
        ).pack(anchor="w")

        mini_strip = tk.Frame(left, bg=COLORS["panel"])
        mini_strip.pack(anchor="w", pady=(14, 0))

        self.hero_badges = {}
        for key in ("rank", "level", "Playtime", "Games Played"):
            frame = tk.Frame(
                mini_strip,
                bg=COLORS["panel_alt"],
                highlightbackground=COLORS["panel_edge"],
                highlightthickness=1,
                bd=0,
                padx=14,
                pady=12,
            )
            frame.pack(side="left", padx=(0, 12))

            if key in {"rank", "level"}:
                label_text = key.title()
            else:
                label_text = key

            tk.Label(
                frame,
                text=label_text,
                bg=COLORS["panel_alt"],
                fg=COLORS["subtle"],
                font=("Segoe UI", 10),
                anchor="w",
            ).pack(anchor="w")

            value_label = tk.Label(
                frame,
                text="N/A",
                bg=COLORS["panel_alt"],
                fg=COLORS["text"],
                font=("Bahnschrift SemiBold", 16),
                anchor="w",
            )
            value_label.pack(anchor="w", pady=(5, 0))
            self.hero_badges[key] = value_label

        right = tk.Frame(hero, bg=COLORS["panel"])
        right.grid(row=0, column=1, sticky="nsew", padx=(18, 0))

        badge_wrap = tk.Frame(
            right,
            bg=COLORS["panel_alt"],
            highlightbackground=COLORS["panel_edge"],
            highlightthickness=1,
            bd=0,
            padx=18,
            pady=18,
        )
        badge_wrap.pack(fill="both", expand=True)

        ring = tk.Canvas(
            badge_wrap,
            width=150,
            height=150,
            bg=COLORS["panel_alt"],
            highlightthickness=0,
            bd=0,
        )
        ring.pack(side="left")
        ring.create_oval(18, 18, 132, 132, outline=COLORS["divider"], width=16)
        self.ring_canvas = ring
        self.loss_arc = ring.create_arc(
            18,
            18,
            132,
            132,
            start=90,
            extent=0,
            outline=COLORS["accent"],
            style="arc",
            width=16,
        )
        self.win_arc = ring.create_arc(
            18,
            18,
            132,
            132,
            start=90,
            extent=0,
            outline=COLORS["good"],
            style="arc",
            width=16,
        )
        self.ring_mode_label = ring.create_text(
            75,
            60,
            text="W / L",
            fill=COLORS["muted"],
            font=("Segoe UI", 10, "bold"),
        )
        self.ring_record_label = ring.create_text(
            75,
            88,
            text="0 / 0",
            fill=COLORS["text"],
            font=("Bahnschrift SemiBold", 15),
        )

        context = tk.Frame(badge_wrap, bg=COLORS["panel_alt"])
        context.pack(side="left", fill="both", expand=True, padx=(18, 0))

        tk.Label(
            context,
            text="Competitive snapshot",
            bg=COLORS["panel_alt"],
            fg=COLORS["subtle"],
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(anchor="w")

        self.context_title = tk.Label(
            context,
            text="All Stats",
            bg=COLORS["panel_alt"],
            fg=COLORS["text"],
            font=("Bahnschrift SemiBold", 22),
            anchor="w",
        )
        self.context_title.pack(anchor="w", pady=(8, 8))

        self.context_summary = tk.Label(
            context,
            text="Pulled from your current analysis.py sample.",
            bg=COLORS["panel_alt"],
            fg=COLORS["muted"],
            font=("Segoe UI", 11),
            justify="left",
            wraplength=260,
            anchor="w",
        )
        self.context_summary.pack(anchor="w")

    def _build_toggle(self):
        strip = tk.Frame(self.main_panel, bg=COLORS["panel_alt"], pady=18)
        strip.pack(fill="x")

        container = tk.Frame(
            strip,
            bg=COLORS["panel"],
            highlightbackground=COLORS["panel_edge"],
            highlightthickness=1,
            bd=0,
            padx=6,
            pady=6,
        )
        container.pack(anchor="w")

        for index, (view_key, config) in enumerate(VIEW_CONFIG.items()):
            button = tk.Button(
                container,
                text=config["label"],
                command=lambda key=view_key: self.show_view(key),
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["text"],
                relief="flat",
                bd=0,
                padx=18,
                pady=10,
                font=("Bahnschrift SemiBold", 11),
                cursor="hand2",
            )
            button.grid(row=0, column=index, padx=4)
            self.toggle_buttons[view_key] = button

        if self.server_stats_by_name:
            self.server_button = tk.Menubutton(
                container,
                textvariable=self.server_var,
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["text"],
                relief="flat",
                bd=0,
                padx=18,
                pady=10,
                font=("Bahnschrift SemiBold", 11),
                cursor="hand2",
                indicatoron=False,
                highlightthickness=0,
            )
            self.server_button.grid(row=0, column=len(VIEW_CONFIG), padx=(14, 4))

            menu = tk.Menu(
                self.server_button,
                tearoff=0,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                activebackground=COLORS["accent"],
                activeforeground=COLORS["text"],
                bd=0,
            )
            for server_name in sorted(self.server_stats_by_name):
                menu.add_command(
                    label=server_name,
                    command=lambda name=server_name: self.show_server_view(name),
                )
            self.server_button.configure(menu=menu)

    def _build_cards(self):
        self.cards_frame = tk.Frame(self.main_panel, bg=COLORS["panel_alt"])
        self.cards_frame.pack(fill="both", expand=True)

        for column in range(3):
            self.cards_frame.grid_columnconfigure(column, weight=1, uniform="stat")

        for index, stat_name in enumerate(STAT_ORDER):
            row = index // 3
            column = index % 3
            card = StatCard(self.cards_frame, stat_name)
            card.grid(row=row, column=column, sticky="nsew", padx=8, pady=8)
            self.metric_cards[stat_name] = card

    def _get_view_record(self, view_key):
        if view_key == "won_rounds":
            return 1, 0
        if view_key == "lost_rounds":
            return 0, 1

        total_games = coerce_int(self.stats_by_view.get("all", {}).get("Games Played"))
        won_games = coerce_int(self.stats_by_view.get("won", {}).get("Games Played"))
        lost_games = coerce_int(self.stats_by_view.get("lost", {}).get("Games Played"))

        if view_key == "won":
            return won_games, 0
        if view_key == "lost":
            return 0, lost_games
        if total_games > 0:
            return won_games, lost_games
        return 0, 0

    def _set_ring(self, wins, losses, label_text, record_text):
        total = wins + losses

        if total <= 0:
            win_extent = 0
            loss_extent = 0
        elif wins > 0 and losses == 0:
            win_extent = -359.9
            loss_extent = 0
        elif losses > 0 and wins == 0:
            win_extent = 0
            loss_extent = -359.9
        else:
            win_extent = -(wins / total) * 360
            loss_extent = -(losses / total) * 360

        self.ring_canvas.itemconfigure(self.win_arc, start=90, extent=win_extent)
        self.ring_canvas.itemconfigure(self.loss_arc, start=90 + win_extent, extent=loss_extent)
        self.ring_canvas.itemconfigure(self.ring_mode_label, text=label_text)
        self.ring_canvas.itemconfigure(self.ring_record_label, text=record_text)

    def _update_ring(self, view_key):
        wins, losses = self._get_view_record(view_key)
        if view_key == "won_rounds":
            ring_text = "100% W"
        elif view_key == "lost_rounds":
            ring_text = "100% L"
        else:
            ring_text = f"{wins} / {losses}"
        self._set_ring(wins, losses, "W / L", ring_text)

    def _update_server_ring(self, current_stats):
        games_played = coerce_int(current_stats.get("Games Played"))
        games_won = coerce_int(current_stats.get("Games Won"))
        games_lost = max(0, games_played - games_won)
        self._set_ring(games_won, games_lost, "W / L", f"{games_won} / {games_lost}")

    def _set_server_button_active(self, is_active):
        if not self.server_button:
            return
        self.server_button.configure(
            bg=COLORS["accent"] if is_active else COLORS["panel"],
            fg=COLORS["text"] if is_active else COLORS["muted"],
            activebackground=COLORS["accent"] if is_active else COLORS["panel"],
            activeforeground=COLORS["text"],
        )

    def show_view(self, view_key):
        self.active_view = view_key
        self.active_server = None
        current_stats = self.stats_by_view.get(view_key, {})
        config = VIEW_CONFIG[view_key]

        for key, button in self.toggle_buttons.items():
            is_active = key == view_key
            button.configure(
                bg=COLORS["accent"] if is_active else COLORS["panel"],
                fg=COLORS["text"] if is_active else COLORS["muted"],
                activebackground=COLORS["accent"] if is_active else COLORS["panel"],
                activeforeground=COLORS["text"],
            )
        self.server_var.set("Server")
        self._set_server_button_active(False)

        self.context_title.configure(text=config["label"])

        playtime = format_stat_value("Playtime", current_stats.get("Playtime"))
        games_played = format_stat_value("Games Played", current_stats.get("Games Played"))
        rank_value = self.player_info.get("rank") or "N/A"
        level_value = self.player_info.get("level") or "N/A"

        self.hero_badges["rank"].configure(text=str(rank_value))
        self.hero_badges["level"].configure(text=str(level_value))
        self.hero_badges["Playtime"].configure(text=playtime)
        self.hero_badges["Games Played"].configure(text=games_played)

        if view_key in ROUND_VIEW_KEYS:
            summary_text = "Loaded directly from analysis.py round splits. Missing fields stay N/A."
        else:
            summary_text = f"{games_played} matches in view with {playtime} of recorded playtime."

        self.context_summary.configure(text=summary_text)
        self._update_ring(view_key)

        for stat_name in STAT_ORDER:
            display_value = format_stat_value(stat_name, current_stats.get(stat_name))
            self.metric_cards[stat_name].update_value(display_value)

    def show_server_view(self, server_name):
        self.active_server = server_name
        current_stats = self.server_stats_by_name.get(server_name, {})

        for button in self.toggle_buttons.values():
            button.configure(
                bg=COLORS["panel"],
                fg=COLORS["muted"],
                activebackground=COLORS["panel"],
                activeforeground=COLORS["text"],
            )

        self.server_var.set(server_name)
        self._set_server_button_active(True)
        self.context_title.configure(text=f"{server_name} Server")

        playtime = format_stat_value("Playtime", current_stats.get("Playtime"))
        games_played = format_stat_value("Games Played", current_stats.get("Games Played"))
        rank_value = self.player_info.get("rank") or "N/A"
        level_value = self.player_info.get("level") or "N/A"

        self.hero_badges["rank"].configure(text=str(rank_value))
        self.hero_badges["level"].configure(text=str(level_value))
        self.hero_badges["Playtime"].configure(text=playtime)
        self.hero_badges["Games Played"].configure(text=games_played)

        summary_text = f"{games_played} matches recorded on {server_name} with {playtime} of playtime."
        self.context_summary.configure(text=summary_text)
        self._update_server_ring(current_stats)

        for stat_name in STAT_ORDER:
            display_value = format_stat_value(stat_name, current_stats.get(stat_name))
            self.metric_cards[stat_name].update_value(display_value)


def main():
    try:
        payload = load_stats_payload()
        app = TrackerStatsApp(payload=payload)
    except Exception as exc:  # noqa: BLE001
        app = TrackerStatsApp(error_message=str(exc))
    app.mainloop()


if __name__ == "__main__":
    main()
