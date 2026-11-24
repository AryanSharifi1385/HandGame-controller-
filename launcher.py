"""Desktop control panel for the webcam hand-game controller."""
import subprocess
import sys
import time
import importlib.util
import platform
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from app_paths import app_dir, asset_path
from PIL import Image, ImageTk
from settings_store import (
    clear_stop_request,
    load_settings,
    read_status,
    request_stop,
    save_settings,
)
from profile_store import DEFAULT_PROFILE_NAME, delete_profile, load_profiles, save_profile, validate_profile_name

KEY_DISPLAY = {
    "space": "Space", "enter": "Enter", "tab": "Tab", "esc": "Escape",
    "backspace": "Backspace", "capslock": "Caps Lock", "lshift": "Left Shift",
    "rshift": "Right Shift", "lctrl": "Left Ctrl", "rctrl": "Right Ctrl",
    "lalt": "Left Alt", "ralt": "Right Alt", "grave": "` / ~",
    "minus": "- / _", "equal": "= / +", "bracketleft": "[ / {",
    "bracketright": "] / }", "backslash": "\\ / |", "semicolon": "; / :",
    "apostrophe": "' / \"", "comma": ", / <", "period": ". / >", "slash": "/ / ?",
    "pageup": "Page Up", "pagedown": "Page Down", "numlock": "Num Lock",
    "scrolllock": "Scroll Lock", "printscreen": "Print Screen", "pause": "Pause",
    "numpad_decimal": "Numpad .", "numpad_divide": "Numpad /",
    "numpad_multiply": "Numpad *", "numpad_subtract": "Numpad -",
    "numpad_add": "Numpad +", "numpad_enter": "Numpad Enter",
}
KEYSYM_TO_KEY = {
    "Escape": "esc", "Return": "enter", "KP_Enter": "numpad_enter",
    "BackSpace": "backspace", "space": "space", "Tab": "tab",
    "Caps_Lock": "capslock", "Shift_L": "lshift", "Shift_R": "rshift",
    "Control_L": "lctrl", "Control_R": "rctrl", "Alt_L": "lalt", "Alt_R": "ralt",
    "Prior": "pageup", "Next": "pagedown", "Page_Up": "pageup", "Page_Down": "pagedown",
    "Print": "printscreen", "Pause": "pause", "Num_Lock": "numlock",
    "Scroll_Lock": "scrolllock", "KP_Decimal": "numpad_decimal", "KP_Divide": "numpad_divide",
    "KP_Multiply": "numpad_multiply", "KP_Subtract": "numpad_subtract", "KP_Add": "numpad_add",
    "KP_0": "numpad0", "KP_1": "numpad1", "KP_2": "numpad2", "KP_3": "numpad3",
    "KP_4": "numpad4", "KP_5": "numpad5", "KP_6": "numpad6", "KP_7": "numpad7",
    "KP_8": "numpad8", "KP_9": "numpad9", "grave": "grave", "minus": "minus",
    "equal": "equal", "bracketleft": "bracketleft", "bracketright": "bracketright",
    "backslash": "backslash", "semicolon": "semicolon", "apostrophe": "apostrophe",
    "comma": "comma", "period": "period", "slash": "slash",
    "Up": "up", "Down": "down", "Left": "left", "Right": "right",
    "Insert": "insert", "Delete": "delete", "Home": "home", "End": "end",
    **{f"F{i}": f"f{i}" for i in range(1, 13)},
    **{f"KP_{i}": f"numpad{i}" for i in range(10)},
}
THEME_NAMES = ("Cyberpunk", "Ghost of Tsushima", "The Last of Us", "God of War", "GTA VI", "Call of Duty", "Stray", "Matrix", "Synthwave", "Arctic")

# Horizontal focal positions (0 = left edge, 1 = right edge) for wide key art.
# The same crop rule is used in the hero banner and the gallery cards.
THEME_FOCUS_X = {
    "Cyberpunk": 0.58, "Ghost of Tsushima": 0.72, "The Last of Us": 0.52,
    "God of War": 0.48, "GTA VI": 0.52, "Call of Duty": 0.54,
    "Stray": 0.76, "Matrix": 0.52, "Synthwave": 0.50, "Arctic": 0.50,
}
THEME_PRESENTATION = {
    "Cyberpunk": {"art":"cyberpunk.jpg", "font":"Bahnschrift", "display":"NIGHT CITY  /  GESTURE INTERFACE", "tagline":"NEON RESPONSE SYSTEM  •  LOW LATENCY  •  FULL CONTROL", "edition":"NIGHT CITY // 2077", "card_relief":"flat", "card_border":1, "card_pad":15, "motif":"╱╱", "title_size":20},
    "Ghost of Tsushima": {"art":"ghost_of_tsushima.jpg", "font":"Georgia", "display":"THE WAY OF THE HAND", "tagline":"PRECISION  •  DISCIPLINE  •  FLOW", "edition":"SHIMURA PROTOCOL", "card_relief":"ridge", "card_border":2, "card_pad":17, "motif":"✦", "title_size":21},
    "The Last of Us": {"art":"the_last_of_us.jpg", "font":"Trebuchet MS", "display":"SURVIVOR CONTROL SYSTEM", "tagline":"ADAPT  •  TRACK  •  SURVIVE", "edition":"FIELD KIT  /  01", "card_relief":"flat", "card_border":1, "card_pad":14, "motif":"▰", "title_size":20},
    "God of War": {"art":"god_of_war.jpg", "font":"Georgia", "display":"REALM CONTROL", "tagline":"FOCUS  •  POWER  •  PRECISION", "edition":"NINE REALMS EDITION", "card_relief":"groove", "card_border":2, "card_pad":16, "motif":"ᛟ", "title_size":22},
    "GTA VI": {"art":"gta_vi.jpg", "font":"Bahnschrift", "display":"VICE CITY CONTROL CLUB", "tagline":"NIGHT DRIVE  •  FAST INPUT  •  NO LIMITS", "edition":"VICE CITY / MIAMI", "card_relief":"flat", "card_border":2, "card_pad":15, "motif":"◆", "title_size":21},
    "Call of Duty": {"art":"call_of_duty.jpg", "font":"Bahnschrift", "display":"MISSION CONTROL", "tagline":"TACTICAL RESPONSE  •  PRECISION  •  READINESS", "edition":"TASK FORCE // INPUT SYSTEM", "card_relief":"flat", "card_border":2, "card_pad":15, "motif":"✚", "title_size":21},
    "Stray": {"art":"stray.jpg", "font":"Century Gothic", "display":"NEKO CONTROL SYSTEM", "tagline":"EXPLORE  •  ADAPT  •  FIND YOUR WAY HOME", "edition":"WALLED CITY / COMPANION MODE", "card_relief":"flat", "card_border":1, "card_pad":15, "motif":"◇", "title_size":21},
    "Matrix": {"art":"matrix.jpg", "font":"Consolas", "display":"INPUT://MATRIX", "tagline":"FOLLOW THE SIGNAL  •  CONTROL THE SYSTEM", "edition":"SIMULATION BUILD 01", "card_relief":"sunken", "card_border":1, "card_pad":14, "motif":"[ ]", "title_size":20},
    "Synthwave": {"art":"synthwave.jpg", "font":"Century Gothic", "display":"AFTERHOURS / CONTROL DECK", "tagline":"RETRO FUTURE  •  DIGITAL MOTION  •  INFINITE PLAY", "edition":"MIDNIGHT EDITION", "card_relief":"flat", "card_border":2, "card_pad":15, "motif":"✧", "title_size":20},
    "Arctic": {"art":"arctic.jpg", "font":"Segoe UI Light", "display":"POLARIS CONTROL STATION", "tagline":"CLEAR SIGNAL  •  CALM RESPONSE  •  PRECISE INPUT", "edition":"POLARIS / SERIES A", "card_relief":"ridge", "card_border":1, "card_pad":17, "motif":"◇", "title_size":20},
}
KEY_LABELS = {"space": "Space", "lshift": "Left Shift", "lctrl": "Left Ctrl", "lalt": "Left Alt"}
BINDINGS = (
    ("key_move_forward", "Movement gesture · Move forward", "Movement"),
    ("key_move_backward", "Movement gesture · Move backward", "Movement"),
    ("key_move_left", "Movement gesture · Move left", "Movement"),
    ("key_move_right", "Movement gesture · Move right", "Movement"),
    ("key_jump", "Right hand · Thumb + pinky pinch (Jump)", "Gestures"),
    ("key_interact", "Right hand · Thumb + middle pinch (Interact)", "Gestures"),
    ("key_fist_action", "Right hand · Fist (Fist action)", "Gestures"),
    ("key_sprint", "Left hand · Thumb + ring pinch (Sprint)", "Gestures"),
    ("key_reload", "Left hand · Thumb + pinky pinch (Reload)", "Gestures"),
    ("key_crouch", "Right hand · Thumb + ring pinch (Crouch)", "Gestures"),
    ("key_ability", "Right hand · Pinky pose (Ability)", "Gestures"),
    ("key_ctrl", "Right hand · Shaka pose (Ctrl action)", "Gestures"),
    ("key_alt", "Left hand · Thumb + index pinch (Alt action)", "Gestures"),
)


class ControllerLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("HandGame Controller  |  Gesture Control Studio")
        # Keep the window usable on smaller laptop screens. The content itself
        # scrolls, so users are never forced to resize the window to reach buttons.
        # Start at a presentation-friendly desktop size while respecting smaller displays.
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        start_w, start_h = min(1600, max(1100, screen_w - 80)), min(1000, max(720, screen_h - 80))
        self.root.geometry(f"{start_w}x{start_h}")
        self.root.minsize(900, 650)
        self.root.configure(background="#080b14")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.presentation_mode = False
        self.root.bind("<Escape>", self._exit_presentation_mode)

        self.process = None
        self.settings = load_settings()
        self.profiles = load_profiles()

        self.sensitivity_var = tk.DoubleVar(value=self.settings["mouse_sensitivity"])
        self.deadzone_var = tk.DoubleVar(value=self.settings["mouse_deadzone"])
        self.max_step_var = tk.IntVar(value=self.settings["mouse_max_step"])
        self.profile_var = tk.StringVar(value="Current settings")
        self.theme_var = tk.StringVar(value=self.settings.get("ui_theme", "Cyberpunk"))
        self.binding_vars = {
            key: tk.StringVar(value=self.settings[key])
            for key, _label, _group in BINDINGS
        }

        self._configure_style()
        self._build_ui()
        self._refresh_status()

    def _configure_style(self):
        """Apply a vivid, dark neon theme using built-in Tk/ttk only."""
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        palettes = {
            "Cyberpunk": {"bg":"#080b14","surface":"#111827","surface2":"#1c2638","text":"#f5f7ff","muted":"#a8b5c9","purple":"#ff2bd6","pink":"#ff3864","cyan":"#00f5ff","lime":"#d7ff00","orange":"#ff9e00","border":"#30445e","hero_bg":"#17102a","hero_border":"#ff2bd6","banner_off":"#222c46","banner_online":"#173b3a","banner_starting":"#3b321c","footer_bg":"#0d1422","stop_bg":"#5b243b","stop_border":"#9f365d"},
            "Ghost of Tsushima": {"bg":"#151713","surface":"#22251f","surface2":"#35392e","text":"#f4f0e5","muted":"#c0b9a6","purple":"#c4a66a","pink":"#a64b3c","cyan":"#d5c69a","lime":"#9eaa72","orange":"#e2a65a","border":"#5a5c48","hero_bg":"#29251c","hero_border":"#c4a66a","banner_off":"#39382f","banner_online":"#294037","banner_starting":"#554326","footer_bg":"#1b1d18","stop_bg":"#542c27","stop_border":"#9b5949"},
            "The Last of Us": {"bg":"#111713","surface":"#1d2820","surface2":"#2b3a2d","text":"#eef1e7","muted":"#aebba9","purple":"#a4b88b","pink":"#b85c50","cyan":"#8fc7a1","lime":"#b5d47a","orange":"#d7a35a","border":"#3d5544","hero_bg":"#1c2b20","hero_border":"#78956b","banner_off":"#303a32","banner_online":"#254636","banner_starting":"#4c4228","footer_bg":"#151e18","stop_bg":"#512d2a","stop_border":"#925247"},
            "God of War": {"bg":"#101820","surface":"#1b2935","surface2":"#2b3b49","text":"#f1f5f9","muted":"#a9bac8","purple":"#6fb7d6","pink":"#d95d52","cyan":"#72d3ed","lime":"#a6d17a","orange":"#e0a45a","border":"#3b5363","hero_bg":"#172b3a","hero_border":"#5cb8d5","banner_off":"#2a3741","banner_online":"#24433e","banner_starting":"#4b402a","footer_bg":"#131f29","stop_bg":"#552d32","stop_border":"#a34d56"},
            "GTA VI": {"bg":"#160f20","surface":"#25172f","surface2":"#3a2143","text":"#fff4fb","muted":"#d0b6d1","purple":"#ff5ab3","pink":"#ff6b8b","cyan":"#4de7f2","lime":"#d5f36a","orange":"#ffb45c","border":"#60365e","hero_bg":"#321a43","hero_border":"#ff5ab3","banner_off":"#3b2a43","banner_online":"#24483e","banner_starting":"#51402b","footer_bg":"#1d1228","stop_bg":"#612b4d","stop_border":"#a9487c"},
            "Matrix": {"bg":"#050b08","surface":"#0d1711","surface2":"#17261c","text":"#e7ffe9","muted":"#9bbca3","purple":"#5ef38c","pink":"#38d66b","cyan":"#00ff66","lime":"#b5ff4d","orange":"#c3f56b","border":"#245638","hero_bg":"#071c10","hero_border":"#00ff66","banner_off":"#1d3024","banner_online":"#153e28","banner_starting":"#394222","footer_bg":"#08110b","stop_bg":"#3e2529","stop_border":"#5d8d57"},
            "Synthwave": {"bg":"#100b26","surface":"#1c1640","surface2":"#30245c","text":"#fff2ff","muted":"#c0b4e8","purple":"#bb86fc","pink":"#ff4fd8","cyan":"#47eaff","lime":"#c9ff70","orange":"#ffb86b","border":"#4b367c","hero_bg":"#27134a","hero_border":"#ff4fd8","banner_off":"#30264d","banner_online":"#17463f","banner_starting":"#4d3b29","footer_bg":"#160f31","stop_bg":"#54264f","stop_border":"#9a3c87"},
            "Arctic": {"bg":"#edf4f8","surface":"#ffffff","surface2":"#dce9f1","text":"#182b3a","muted":"#536b7a","purple":"#5874c8","pink":"#d34f7b","cyan":"#167f9b","lime":"#4f8d45","orange":"#b56a18","border":"#b6cbd8","hero_bg":"#dcecf5","hero_border":"#5874c8","banner_off":"#dbe5eb","banner_online":"#cfe8da","banner_starting":"#f4e7c9","footer_bg":"#e3edf3","stop_bg":"#f0d9df","stop_border":"#bd7185"},
        }
        self.colors = palettes.get(getattr(self, "theme_var", tk.StringVar(value="Cyberpunk")).get(), palettes["Cyberpunk"]).copy()
        c = self.colors
        self.theme_presentation = THEME_PRESENTATION.get(self.theme_var.get(), THEME_PRESENTATION["Cyberpunk"])
        self.root.configure(background=c["bg"])
        style.configure("TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["surface"])
        font_family = self.theme_presentation["font"]
        style.configure("TLabel", background=c["surface"], foreground=c["text"], font=(font_family, 10))
        style.configure("Muted.TLabel", background=c["surface"], foreground=c["muted"], font=(font_family, 9))
        style.configure("CardTitle.TLabel", background=c["surface"], foreground=c["cyan"], font=(font_family, 11, "bold"))
        style.configure("TButton", padding=(12, 9), font=(font_family, 10, "bold"), background=c["surface2"], foreground=c["text"], bordercolor=c["surface2"], borderwidth=0, relief="flat", focusthickness=0)
        style.map("TButton", background=[("active", c["border"]), ("disabled", c["surface2"])], foreground=[("disabled", c["muted"])])
        style.configure("Accent.TButton", padding=(14, 10), background=c["purple"], foreground=c["bg"], bordercolor=c["purple"], borderwidth=0, relief="flat", focusthickness=0)
        style.map("Accent.TButton", background=[("active", c["purple"])], foreground=[("active", c["bg"])])
        style.configure("Stop.TButton", padding=(12, 10), background=c["stop_bg"], foreground=c["text"], bordercolor=c["stop_bg"], borderwidth=0, relief="flat", focusthickness=0)
        style.map("Stop.TButton", background=[("active", c["stop_border"])])
        style.configure("TScale", background=c["surface"], troughcolor=c["surface2"])
        style.configure("TCombobox", padding=5, fieldbackground=c["surface2"], background=c["surface2"], foreground=c["text"], arrowcolor=c["cyan"])
        style.map("TCombobox", fieldbackground=[("readonly", c["surface2"])], foreground=[("readonly", c["text"])])

    def _rounded_panel(self, parent, fill, border, *, radius=16, inset=8, pady=(0, 13)):
        """Create a rounded canvas shell with a padded widget area inside it."""
        shell = tk.Canvas(parent, bg=parent.cget("bg"), highlightthickness=0, bd=0, height=80)
        shell.pack(fill="x", pady=pady)
        content = tk.Frame(shell, bg=fill)
        window_id = shell.create_window((inset, inset), window=content, anchor="nw")

        def redraw(event=None):
            width = max(40, shell.winfo_width())
            height = max(40, content.winfo_reqheight() + inset * 2)
            shell.configure(height=height)
            shell.coords(window_id, inset, inset)
            shell.itemconfigure(window_id, width=max(1, width - inset * 2))
            shell.delete("rounded_panel_bg")
            r = min(radius, height // 3, width // 3)
            # Rasterized rounded background gives smooth corners at every scale.
            from PIL import ImageDraw
            panel_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            ImageDraw.Draw(panel_image).rounded_rectangle(
                (1, 1, width-2, height-2), radius=r, fill=fill, outline=border, width=1
            )
            photo = ImageTk.PhotoImage(panel_image)
            shell._rounded_panel_photo = photo
            shell.delete("rounded_panel_bg")
            shell.create_image(0, 0, anchor="nw", image=photo, tags=("rounded_panel_bg",))
            shell.tag_lower("rounded_panel_bg")

        content.bind("<Configure>", redraw)
        shell.bind("<Configure>", redraw)
        return shell, content

    def _build_ui(self):
        # Scrollable, card-based themed dashboard using native Tk/ttk widgets.
        c = self.colors
        old_shell = getattr(self, "_ui_shell", None)
        if old_shell is not None and old_shell.winfo_exists():
            old_shell.destroy()
        shell = tk.Frame(self.root, bg=self.colors["bg"])
        self._ui_shell = shell
        shell.pack(fill="both", expand=True)
        # Fixed navigation rail + scrollable workspace, inspired by a modern game launcher.
        sidebar = tk.Frame(shell, bg="#07111f", width=206, highlightbackground=self.colors["border"], highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        brand_mark = tk.Canvas(sidebar, width=44, height=44, bg="#07111f", highlightthickness=0)
        brand_mark.pack(anchor="w", padx=20, pady=(22, 8))
        brand_mark.create_oval(3, 3, 41, 41, fill=self.colors["cyan"], outline="")
        brand_mark.create_text(22, 22, text="H", fill="#07111f", font=("Segoe UI", 19, "bold"))
        tk.Label(sidebar, text="HandGame", bg="#07111f", fg="#f1f7ff", font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=20)
        tk.Label(sidebar, text="CONTROLLER", bg="#07111f", fg=self.colors["cyan"], font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(0, 22))
        nav_items = [("⌂", "Home", 0.0), ("♧", "Gesture Control", 0.36), ("▦", "Key Assignment", 0.82), ("♙", "Profiles", 0.70), ("⚙", "Settings", 0.90), ("◈", "Theme", 0.48)]
        self.nav_buttons = []
        self._nav_button_states = []
        def rounded_nav_shape(canvas, x1, y1, x2, y2, radius=13, **kwargs):
            points = [x1+radius,y1, x2-radius,y1, x2-radius/2,y1, x2,y1+radius/2,
                      x2,y2-radius/2, x2,y2-radius, x2-radius,y2,
                      x1+radius,y2, x1,y2-radius, x1,y1+radius]
            return canvas.create_polygon(points, smooth=True, splinesteps=20, **kwargs)
        self._active_nav_label = "Home"
        for symbol, label, fraction in nav_items:
            nav = tk.Canvas(sidebar, width=188, height=46, bg="#07111f", highlightthickness=0,
                            bd=0, cursor="hand2")
            nav.pack(fill="x", padx=8, pady=3)
            bg_item = rounded_nav_shape(nav, 2, 2, 184, 44, fill="#123b58" if label == "Home" else "#07111f", outline="")
            accent_item = nav.create_rectangle(2, 13, 5, 33, fill=self.colors["cyan"] if label == "Home" else "#07111f", outline="")
            icon_item = nav.create_text(27, 23, text=symbol, fill="#57c9ff" if label == "Home" else "#90a9c3", font=("Segoe UI Symbol", 15))
            text_item = nav.create_text(48, 23, text=label, anchor="w", fill="#eaf6ff" if label == "Home" else "#b6c8dc",
                                        font=("Segoe UI", 10, "bold" if label == "Home" else "normal"))
            state = {"canvas":nav, "bg":bg_item, "accent":accent_item, "icon":icon_item, "text":text_item,
                     "label":label, "fraction":fraction}
            self._nav_button_states.append(state)
            def activate(_event=None, item=state):
                self.canvas.yview_moveto(item["fraction"])
                self._set_active_nav(item["label"])
            def hover_on(_event=None, item=state):
                if item["label"] != self._active_nav_label:
                    item["canvas"].itemconfigure(item["bg"], fill="#10263a")
            def hover_off(_event=None, item=state):
                if item["label"] != self._active_nav_label:
                    item["canvas"].itemconfigure(item["bg"], fill="#07111f")
            nav.bind("<Button-1>", activate)
            nav.bind("<Enter>", hover_on)
            nav.bind("<Leave>", hover_off)
            for item_id in (bg_item, accent_item, icon_item, text_item):
                nav.tag_bind(item_id, "<Button-1>", activate)
                nav.tag_bind(item_id, "<Enter>", hover_on)
                nav.tag_bind(item_id, "<Leave>", hover_off)
            self.nav_buttons.append(nav)
        tk.Frame(sidebar, bg="#24364a", height=1).pack(fill="x", padx=18, pady=(24, 14))
        tk.Label(sidebar, text="♛  SHOWCASE MODE", bg="#07111f", fg="#f6cb58", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18)
        tk.Label(sidebar, text="University Presentation Build", bg="#07111f", fg="#7e96b3", font=("Segoe UI", 8), wraplength=165, justify="left").pack(anchor="w", padx=18, pady=(4, 0))
        tk.Label(sidebar, text="v2.2  •  SHOWCASE BUILD", bg="#07111f", fg="#7187a0", font=("Segoe UI", 8)).pack(side="bottom", anchor="w", padx=18, pady=18)

        self.canvas = tk.Canvas(shell, background=self.colors["bg"], highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(self.canvas, bg=self.colors["bg"], padx=28, pady=22)
        self._canvas_window = self.canvas.create_window((0, 0), window=outer, anchor="nw")

        # A compact product masthead makes the application read like a finished
        # desktop control studio, rather than a settings utility.
        masthead = tk.Frame(outer, bg=self.colors["bg"])
        masthead.pack(fill="x", pady=(0, 16))
        brand = tk.Frame(masthead, bg=self.colors["bg"])
        brand.pack(side="left", fill="x", expand=True)
        tk.Label(brand, text="HG / STUDIO", bg=self.colors["bg"], fg=self.colors["cyan"],
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(brand, text="HANDGAME CONTROLLER", bg=self.colors["bg"], fg=self.colors["text"],
                 font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(2, 0))
        tk.Label(brand, text="CAMERA-BASED GESTURE INPUT  /  PERSONAL CONTROL DECK", bg=self.colors["bg"],
                 fg=self.colors["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))
        self.build_badge = tk.Label(masthead, text="●  SHOWCASE BUILD", bg=self.colors["surface2"],
                 fg=self.colors["lime"], font=("Segoe UI", 9, "bold"), padx=13, pady=9,
                 highlightbackground=self.colors["border"], highlightthickness=1)
        self.build_badge.pack(side="right", anchor="n")
        self.status_banner = tk.Label(
            masthead, text="●  CONTROLLER OFFLINE", anchor="center", padx=12, pady=8,
            bg=self.colors["banner_off"], fg=self.colors["muted"],
            font=("Segoe UI", 9, "bold"), highlightthickness=1,
            highlightbackground=self.colors["border"], bd=0
        )
        self.status_banner.pack(side="right", anchor="n", padx=(0, 10))
        outer.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_scroll_content)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        # Cinematic theme banner: each theme has its own original illustrated scene,
        # typography, identity text and card treatment (not just a palette swap).
        self.hero_canvas = tk.Canvas(
            outer, height=282, bg=self.colors["bg"],
            highlightthickness=0, borderwidth=0
        )
        self.hero_canvas.pack(fill="x", pady=(0, 14))
        try:
            self._hero_source = Image.open(asset_path("theme_art/" + self.theme_presentation["art"])).convert("RGB")
        except Exception:
            self._hero_source = Image.new("RGB", (1600, 460), self.colors["hero_bg"])
        self._hero_bg_item = self.hero_canvas.create_image(0, 0, anchor="nw", tags=("hero_background",))
        self._hero_shade_item = None
        self._hero_kicker_item = self.hero_canvas.create_text(
            30, 24, anchor="nw", text=self.theme_presentation["edition"],
            fill=self.colors["cyan"], font=(self.theme_presentation["font"], 9, "bold")
        )
        self._hero_title_item = self.hero_canvas.create_text(
            28, 58, anchor="nw", text=self.theme_presentation["display"],
            fill=self.colors["text"], font=(self.theme_presentation["font"], self.theme_presentation["title_size"] + 5, "bold")
        )
        self._hero_tagline_item = self.hero_canvas.create_text(
            30, 105, anchor="nw", text=self.theme_presentation["tagline"],
            fill=self.colors["purple"], font=(self.theme_presentation["font"], 9, "bold")
        )
        self._hero_subtitle_item = self.hero_canvas.create_text(
            30, 134, anchor="nw", text="WEBCAM TRACKING   /   GESTURE MAPPING   /   GAME INPUT",
            fill=self.colors["muted"], font=(self.theme_presentation["font"], 8)
        )
        self.hero_canvas.create_text(30, 201, anchor="w", text="ACTIVE THEME", fill=self.colors["muted"],
                                      font=(self.theme_presentation["font"], 8, "bold"))
        self.theme_combo = ttk.Combobox(self.hero_canvas, textvariable=self.theme_var, values=THEME_NAMES, state="readonly", width=23)
        self._theme_combo_window = self.hero_canvas.create_window(155, 194, anchor="w", window=self.theme_combo)
        self.theme_combo.bind("<<ComboboxSelected>>", self._change_theme)
        self.hero_canvas.bind("<Configure>", self._render_hero_art)
        self._render_hero_art()

        def make_card(parent, title, accent):
            presentation = self.theme_presentation
            _card_shell, card = self._rounded_panel(
                parent, self.colors["surface"], self.colors["border"], radius=17, inset=12, pady=(0, 13)
            )
            card.configure(padx=presentation["card_pad"], pady=max(10, presentation["card_pad"] - 2))
            rail = tk.Frame(card, bg=accent, height=3)
            rail.pack(fill="x", pady=(0, 9))
            tk.Label(card, text=title, bg=self.colors["surface"], fg=accent,
                     font=(presentation["font"], 10, "bold")).pack(anchor="w", pady=(0, 7))
            return card

        # Three live panels echo the reference dashboard and surface the useful
        # camera/gesture/input state without burying it in a settings column.
        summary_row = tk.Frame(outer, bg=self.colors["bg"])
        summary_row.pack(fill="x", pady=(0, 2))
        for col in range(3):
            summary_row.columnconfigure(col, weight=1, uniform="summary")
        camera_column = tk.Frame(summary_row, bg=self.colors["bg"])
        gesture_column = tk.Frame(summary_row, bg=self.colors["bg"])
        input_column = tk.Frame(summary_row, bg=self.colors["bg"])
        camera_column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        gesture_column.grid(row=0, column=1, sticky="nsew", padx=7)
        input_column.grid(row=0, column=2, sticky="nsew", padx=(7, 0))

        camera_frame = make_card(camera_column, "●  CAMERA STATUS", self.colors["cyan"])
        self.controller_status = ttk.Label(camera_frame, text="Controller: checking…")
        self.controller_status.pack(anchor="w", pady=3)
        self.calibration_status = ttk.Label(camera_frame, text="Calibration: —")
        self.calibration_status.pack(anchor="w", pady=3)
        self.fps_status = ttk.Label(camera_frame, text="Tracking rate: —")
        self.fps_status.pack(anchor="w", pady=3)

        gesture_frame = make_card(gesture_column, "✋  GESTURE RECOGNITION", self.colors["purple"])
        self.left_status = ttk.Label(gesture_frame, text="Right hand: —")
        self.left_status.pack(anchor="w", pady=3)
        self.right_status = ttk.Label(gesture_frame, text="Left hand: —")
        self.right_status.pack(anchor="w", pady=3)
        self.movement_status = ttk.Label(gesture_frame, text="Movement: —")
        self.movement_status.pack(anchor="w", pady=3)

        input_frame = make_card(input_column, "⌖  ACTIVE CONTROLS", self.colors["lime"])
        self.mouse_status = ttk.Label(input_frame, text="Mouse mode: —")
        self.mouse_status.pack(anchor="w", pady=3)
        self.aim_status = ttk.Label(input_frame, text="Aim: —")
        self.aim_status.pack(anchor="w", pady=3)
        self.active_status = ttk.Label(input_frame, text="Active controls: none", wraplength=330, justify="left")
        self.active_status.pack(anchor="w", fill="x", pady=(5, 1))

        # Visual theme gallery: artwork is loaded from the project's bundled files.
        _gallery_shell, gallery = self._rounded_panel(
            outer, self.colors["surface"], self.colors["border"], radius=17, inset=12, pady=(0, 16)
        )
        gallery.configure(padx=2, pady=1)
        gallery_head = tk.Frame(gallery, bg=self.colors["surface"])
        gallery_head.pack(fill="x", pady=(0, 10))
        tk.Label(gallery_head, text="◈  THEME SELECTION", bg=self.colors["surface"], fg=self.colors["text"],
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(gallery_head, text="Choose your game atmosphere", bg=self.colors["surface"], fg=self.colors["muted"],
                 font=("Segoe UI", 9)).pack(side="left", padx=(10, 0))
        theme_grid = tk.Frame(gallery, bg=self.colors["surface"])
        theme_grid.pack(fill="x")
        self.theme_thumbnails = []
        self._theme_tile_canvases = []
        self._theme_tile_sources = {}
        # Wide, edge-to-edge image tiles: crop to fill (never letterbox), keep the
        # important artwork on the right, and fade the left edge for readable labels.
        for idx, theme_name in enumerate(THEME_NAMES):
            info = THEME_PRESENTATION[theme_name]
            tile = tk.Canvas(theme_grid, height=128, bg=self.colors["surface2"], highlightthickness=0,
                             bd=0, cursor="hand2", relief="flat")
            tile.grid(row=idx // 5, column=idx % 5, sticky="ew", padx=5, pady=5)
            theme_grid.columnconfigure(idx % 5, weight=1, uniform="theme_tiles")
            try:
                self._theme_tile_sources[theme_name] = Image.open(
                    asset_path("theme_art/" + info["art"])
                ).convert("RGB")
            except OSError:
                self._theme_tile_sources[theme_name] = Image.new("RGB", (640, 360), "#101b2b")
            tile._theme_name = theme_name
            tile.bind("<Configure>", lambda event, canvas=tile, name=theme_name: self._render_theme_tile(canvas, name))
            tile.bind("<Button-1>", lambda _e, name=theme_name: self._select_theme_from_gallery(name))
            self._theme_tile_canvases.append(tile)
            self._render_theme_tile(tile, theme_name)


        # Detailed controls sit below the live dashboard, keeping the first screen
        # presentation-focused while retaining every existing setting and binding.
        dashboard_columns = tk.Frame(outer, bg=self.colors["bg"])
        dashboard_columns.pack(fill="x", expand=True)
        dashboard_columns.columnconfigure(0, weight=1, uniform="dashboard")
        dashboard_columns.columnconfigure(1, weight=1, uniform="dashboard")
        left_column = tk.Frame(dashboard_columns, bg=self.colors["bg"])
        right_column = tk.Frame(dashboard_columns, bg=self.colors["bg"])
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        right_column.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        profiles_frame = make_card(left_column, "▣  GAME PROFILES  /  PRESETS", self.colors["purple"])
        tk.Label(
            profiles_frame,
            text="Save different control setups for different games. Loading a profile updates your saved settings; stop the controller first to change keyboard bindings safely.",
            bg=self.colors["surface"], fg=self.colors["muted"], font=(self.theme_presentation["font"], 9),
            wraplength=480, justify="left"
        ).pack(anchor="w", pady=(0, 10))
        profile_row = tk.Frame(profiles_frame, bg=self.colors["surface"])
        profile_row.pack(fill="x")
        self.profile_combo = ttk.Combobox(
            profile_row, textvariable=self.profile_var, state="readonly", width=24
        )
        self.profile_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(profile_row, text="LOAD PROFILE", command=self.load_selected_profile).pack(side="left", padx=(0, 6))
        ttk.Button(profile_row, text="SAVE AS…", command=self.save_profile_as).pack(side="left", padx=(0, 6))
        ttk.Button(profile_row, text="DELETE", command=self.delete_selected_profile).pack(side="left")
        self.profile_hint = tk.Label(
            profiles_frame, text="Default is protected. Save As creates your own profile.",
            bg=self.colors["surface"], fg=self.colors["cyan"], font=(self.theme_presentation["font"], 9)
        )
        self.profile_hint.pack(anchor="w", pady=(9, 0))
        self._refresh_profile_choices()

        settings_frame = make_card(left_column, "✧  POINTER TUNING", self.colors["pink"])
        tk.Label(settings_frame, text="Tune the cursor until it feels natural. Changes save to your user settings.",
                 bg=self.colors["surface"], fg=self.colors["muted"], font=(self.theme_presentation["font"], 9), wraplength=480, justify="left").pack(anchor="w", pady=(0, 10))
        self.sensitivity_label = ttk.Label(settings_frame, text="")
        self.sensitivity_label.pack(anchor="w")
        self.sensitivity_scale = ttk.Scale(settings_frame, from_=0.25, to=4.0, variable=self.sensitivity_var, command=lambda _value: self._update_setting_labels())
        self.sensitivity_scale.pack(fill="x", pady=(2, 10))
        self.deadzone_label = ttk.Label(settings_frame, text="")
        self.deadzone_label.pack(anchor="w")
        self.deadzone_scale = ttk.Scale(settings_frame, from_=0.0005, to=0.02, variable=self.deadzone_var, command=lambda _value: self._update_setting_labels())
        self.deadzone_scale.pack(fill="x", pady=(2, 10))
        self.max_step_label = ttk.Label(settings_frame, text="")
        self.max_step_label.pack(anchor="w")
        self.max_step_scale = ttk.Scale(settings_frame, from_=3, to=30, variable=self.max_step_var, command=lambda _value: self._update_setting_labels())
        self.max_step_scale.pack(fill="x", pady=(2, 2))
        self._update_setting_labels()

        bindings_frame = make_card(right_column, "⌘  INPUT MAPPING  /  KEY BINDINGS", self.colors["lime"])
        tk.Label(bindings_frame, text="Choose a gesture on the left and its output key on the right. Changes apply after restarting the controller.",
                 bg=self.colors["surface"], fg=self.colors["muted"], font=(self.theme_presentation["font"], 9), wraplength=480, justify="left").pack(anchor="w", pady=(0, 10))
        grid = tk.Frame(bindings_frame, bg=self.colors["surface"])
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=0)
        last_group = None
        row_index = 0
        self.binding_buttons = {}
        for key, label, group in BINDINGS:
            if group != last_group:
                tk.Label(grid, text=group.upper(), bg=self.colors["surface"], fg=self.colors["purple"],
                         font=(self.theme_presentation["font"], 9, "bold")).grid(row=row_index, column=0, columnspan=2, sticky="w", pady=(8, 4))
                row_index += 1
                last_group = group
            ttk.Label(grid, text=label).grid(row=row_index, column=0, sticky="w", padx=(0, 14), pady=4)
            self.binding_buttons = getattr(self, "binding_buttons", {})
            key_button = ttk.Button(grid, text=self._display_key(self.binding_vars[key].get()), width=16, command=lambda setting=key: self._begin_key_capture(setting))
            key_button.grid(row=row_index, column=1, sticky="e", pady=4)
            self.binding_buttons[key] = key_button
            row_index += 1

        diagnostics_frame = make_card(left_column, "✦  SHOWCASE READINESS  /  PREFLIGHT", self.colors["orange"])
        tk.Label(
            diagnostics_frame,
            text="Run a quick preflight before presenting. This checks project assets and environment prerequisites without opening the camera or sending game inputs.",
            bg=self.colors["surface"], fg=self.colors["muted"],
            font=(self.theme_presentation["font"], 9), wraplength=480, justify="left"
        ).pack(anchor="w", pady=(0, 10))
        self.preflight_summary = tk.Label(
            diagnostics_frame, text="Preflight not run yet", bg=self.colors["surface"],
            fg=self.colors["muted"], font=(self.theme_presentation["font"], 9),
            anchor="w", justify="left", wraplength=480
        )
        self.preflight_summary.pack(fill="x", anchor="w", pady=(9, 0))

        _actions_shell, controls = self._rounded_panel(
            outer, self.colors["surface"], self.colors["border"], radius=17, inset=12, pady=(5, 13)
        )
        controls.configure(padx=3, pady=2)
        tk.Label(controls, text="⚡  QUICK ACTIONS", bg=self.colors["surface"], fg=self.colors["text"],
                 font=(self.theme_presentation["font"], 10, "bold")).pack(side="left", padx=(0, 18))
        self.start_button = ttk.Button(controls, text="▶  START CONTROLLER", style="Accent.TButton", command=self.start_controller)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(controls, text="■  STOP SAFELY", style="Stop.TButton", command=self.stop_controller, state="disabled")
        self.stop_button.pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="PREFLIGHT CHECK", command=self.run_preflight).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="PRESENTATION MODE", command=self.toggle_presentation_mode).pack(side="left", padx=(8, 0))
        ttk.Button(controls, text="✦  SAVE SETTINGS", command=self.apply_settings).pack(side="right")

        _footer_shell, footer = self._rounded_panel(
            outer, self.colors["footer_bg"], self.colors["border"], radius=16, inset=13, pady=(0, 8)
        )
        tk.Label(footer, text="QUICK TIP", bg=self.colors["footer_bg"], fg=self.colors["orange"], font=(self.theme_presentation["font"], 9, "bold")).pack(anchor="w")
        tk.Label(footer, text="👍 Thumbs-up = mouse mode   ·   ☝ Index point = aim   ·   Stop safely releases held inputs   ·   ] = EXIT CAMERA",
                 bg=self.colors["footer_bg"], fg=self.colors["muted"], font=(self.theme_presentation["font"], 9), wraplength=1120, justify="left").pack(anchor="w", pady=(4, 0))

    def run_preflight(self):
        """Check common presentation prerequisites without touching camera or inputs."""
        checks = []
        base = app_dir()
        if getattr(sys, "frozen", False):
            core = base / "HandGameControllerCore.exe"
            checks.append(("Controller engine", core.is_file(), str(core)))
            checks.append(("Theme artwork", all(asset_path("theme_art/" + item["art"]).is_file() for item in THEME_PRESENTATION.values()), "Bundled theme images"))
        else:
            required = ("mian.py", "camera.py", "hand_tracker.py", "gesture_detector.py", "game_controller.py", "settings_store.py", "hand_landmarker.task")
            missing = [name for name in required if not (base / name).is_file()]
            checks.append(("Project files and model", not missing, "Missing: " + ", ".join(missing) if missing else "Core source files and model found"))
            checks.append(("Theme artwork", all((base / "theme_art" / item["art"]).is_file() for item in THEME_PRESENTATION.values()), "All configured theme images found"))
        for module in ("cv2", "mediapipe", "numpy", "PIL"):
            try:
                present = importlib.util.find_spec(module) is not None
            except (ImportError, ValueError):
                present = False
            checks.append((f"Dependency: {module}", present, "Available" if present else "Not found in this Python environment"))
        checks.append(("Windows input support", platform.system() == "Windows", "Windows detected" if platform.system() == "Windows" else "Not Windows; real keyboard/mouse injection must be verified on the presentation laptop"))
        passed = sum(1 for _, ok, _ in checks if ok)
        lines = [f"{'PASS' if ok else 'CHECK'}  {name} — {detail}" for name, ok, detail in checks]
        self.preflight_summary.configure(
            text=f"Preflight: {passed}/{len(checks)} checks passed. Open report for details.",
            fg=self.colors["lime"] if passed == len(checks) else self.colors["orange"]
        )
        window = tk.Toplevel(self.root)
        window.title("Showcase preflight report")
        window.configure(bg=self.colors["bg"])
        window.transient(self.root)
        window.geometry("820x560")
        window.minsize(620, 400)
        tk.Label(window, text=f"SHOWCASE PREFLIGHT  ·  {passed}/{len(checks)} PASSED", bg=self.colors["bg"],
                 fg=self.colors["cyan"], font=(self.theme_presentation["font"], 15, "bold"), padx=18, pady=16).pack(anchor="w")
        report = tk.Text(window, wrap="word", bg=self.colors["surface"], fg=self.colors["text"],
                         insertbackground=self.colors["text"], relief="flat", padx=14, pady=12,
                         font=("Consolas", 10), height=16)
        report.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        report.insert("1.0", "\n".join(lines) + "\n\nNote: this preflight does not test camera access, gesture accuracy, real input injection, or gameplay. Those require a manual rehearsal on the presentation laptop.")
        report.configure(state="disabled")
        ttk.Button(window, text="CLOSE REPORT", command=window.destroy).pack(anchor="e", padx=18, pady=(0, 16))

    def toggle_presentation_mode(self):
        self.presentation_mode = not self.presentation_mode
        self.root.attributes("-fullscreen", self.presentation_mode)
        if self.presentation_mode:
            self.status_banner.configure(text="✦  PRESENTATION MODE  ·  PRESS ESC TO EXIT")

    def _exit_presentation_mode(self, _event=None):
        if self.presentation_mode:
            self.presentation_mode = False
            self.root.attributes("-fullscreen", False)
            return "break"

    @staticmethod
    def _display_key(key):
        key = str(key).lower()
        if key in KEY_DISPLAY:
            return KEY_DISPLAY[key]
        if key.startswith("f") and key[1:].isdigit():
            return key.upper()
        if key.startswith("numpad") and key[6:].isdigit():
            return f"Numpad {key[6:]}"
        return key.upper() if len(key) == 1 else key.replace("_", " ").title()

    def _begin_key_capture(self, setting_name):
        """Capture one physical key press for a gesture assignment."""
        if self.process is not None and self.process.poll() is None:
            messagebox.showinfo("Stop controller first", "Stop the controller before changing keyboard assignments.", parent=self.root)
            return
        button = self.binding_buttons.get(setting_name)
        if button is None:
            return
        button.configure(text="Press any key…")
        button.focus_set()
        button.bind("<KeyPress>", lambda event, setting=setting_name: self._finish_key_capture(setting, event), add="+")
        button.bind("<FocusOut>", lambda _event, setting=setting_name: self._cancel_key_capture(setting), add="+")

    def _finish_key_capture(self, setting_name, event):
        key = KEYSYM_TO_KEY.get(event.keysym)
        if key is None:
            keysym = event.keysym
            if len(keysym) == 1 and keysym.isalpha():
                key = keysym.lower()
            elif len(keysym) == 1 and keysym.isdigit():
                key = keysym
        if key not in self.settings_key_names():
            self._cancel_key_capture(setting_name)
            messagebox.showwarning(
                "Unsupported key", "That key is not supported by the current Windows input layer. Try a letter, number, function key, punctuation key, navigation key, or numpad key.", parent=self.root
            )
            return "break"
        self.binding_vars[setting_name].set(key)
        button = self.binding_buttons.get(setting_name)
        if button:
            button.configure(text=self._display_key(key))
            button.unbind("<KeyPress>")
            button.unbind("<FocusOut>")
        return "break"

    @staticmethod
    def settings_key_names():
        # Imported lazily to keep the UI and settings validation in sync.
        from settings_store import ALLOWED_KEYS
        return ALLOWED_KEYS

    def _cancel_key_capture(self, setting_name):
        button = self.binding_buttons.get(setting_name)
        if button:
            button.configure(text=self._display_key(self.binding_vars[setting_name].get()))
            button.unbind("<KeyPress>")
            button.unbind("<FocusOut>")

    @staticmethod
    def _cover_crop(source, target_ratio, focus_x=0.5, focus_y=0.5):
        """Crop to a target aspect ratio while keeping the selected focal area."""
        source = source.convert("RGB")
        sw, sh = source.size
        source_ratio = sw / max(1, sh)
        if source_ratio > target_ratio:
            crop_w = max(1, int(sh * target_ratio))
            left = int((sw - crop_w) * max(0.0, min(1.0, focus_x)))
            left = min(max(0, left), sw - crop_w)
            return source.crop((left, 0, left + crop_w, sh))
        crop_h = max(1, int(sw / target_ratio))
        top = int((sh - crop_h) * max(0.0, min(1.0, focus_y)))
        top = min(max(0, top), sh - crop_h)
        return source.crop((0, top, sw, top + crop_h))

    @staticmethod
    def _apply_left_fade(image, color, max_opacity=190, fade_fraction=0.52):
        """Blend a dark tint into the left side, reaching clear artwork near the middle."""
        from PIL import ImageDraw
        image = image.convert("RGBA")
        width, height = image.size
        fade_width = max(1, int(width * fade_fraction))
        row = [int(max_opacity * (1.0 - (x / max(1, fade_width - 1))) ** 1.55)
               if x < fade_width else 0 for x in range(width)]
        alpha = Image.new("L", (width, 1))
        alpha.putdata(row)
        alpha = alpha.resize((width, height))
        tint = Image.new("RGBA", (width, height), color)
        tint.putalpha(alpha)
        return Image.alpha_composite(image, tint)

    def _render_theme_tile(self, canvas, theme_name):
        """Render rounded, correctly cropped theme artwork with a soft left fade."""
        if not canvas.winfo_exists():
            return
        width = max(150, canvas.winfo_width())
        height = max(100, canvas.winfo_height())
        try:
            from PIL import ImageDraw
            source = self._theme_tile_sources.get(theme_name)
            if source is None:
                return
            focus_x = THEME_FOCUS_X.get(theme_name, 0.55)
            cropped = self._cover_crop(source, width / height, focus_x=focus_x, focus_y=0.48)
            image = cropped.resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
            # The left fades into the same dark surface used by the label region.
            image = self._apply_left_fade(image, (5, 11, 18, 255), max_opacity=168, fade_fraction=0.48)
            # A restrained lower shadow gives the label contrast without a hard strip.
            shade_h = max(1, int(height * 0.25))
            shade = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            shade_alpha = Image.new("L", (1, height))
            shade_alpha.putdata([int(112 * (y / max(1, shade_h - 1)) ** 1.5) if y < shade_h else 112 for y in range(height)])
            shade_alpha = shade_alpha.resize((width, height))
            shade_layer = Image.new("RGBA", (width, height), (3, 7, 12, 0))
            shade_layer.putalpha(shade_alpha)
            image = Image.alpha_composite(image, shade_layer)
            mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle((1, 1, width - 2, height - 2), radius=15, fill=255)
            image.putalpha(mask)
            photo = ImageTk.PhotoImage(image)
            canvas._theme_photo = photo
            canvas.delete("all")
            canvas.create_image(0, 0, anchor="nw", image=photo)
            selected = theme_name == self.theme_var.get()
            border = self.colors["cyan"] if selected else self.colors["border"]
            radius = 15
            line_width = 3 if selected else 1
            # Rounded outline drawn on top of the clipped image.
            canvas.create_line(radius, 1, width-radius, 1, fill=border, width=line_width)
            canvas.create_line(radius, height-2, width-radius, height-2, fill=border, width=line_width)
            canvas.create_line(1, radius, 1, height-radius, fill=border, width=line_width)
            canvas.create_line(width-2, radius, width-2, height-radius, fill=border, width=line_width)
            canvas.create_arc(1, 1, radius*2+1, radius*2+1, start=90, extent=90, style="arc", outline=border, width=line_width)
            canvas.create_arc(width-radius*2-1, 1, width-1, radius*2+1, start=0, extent=90, style="arc", outline=border, width=line_width)
            canvas.create_arc(width-radius*2-1, height-radius*2-1, width-1, height-1, start=270, extent=90, style="arc", outline=border, width=line_width)
            canvas.create_arc(1, height-radius*2-1, radius*2+1, height-1, start=180, extent=90, style="arc", outline=border, width=line_width)
            canvas.create_text(14, height - 18, anchor="w", text=theme_name,
                               fill="#f3f7ff", font=("Segoe UI", 9, "bold" if selected else "normal"))
            if selected:
                canvas.create_oval(width - 31, 9, width - 11, 29, fill=self.colors["cyan"], outline="")
                canvas.create_text(width - 21, 19, text="✓", fill="#07111f", font=("Segoe UI", 10, "bold"))
        except (OSError, tk.TclError, AttributeError, ValueError):
            pass

    def _render_hero_art(self, event=None):
        """Place 16:9 key art on the right and fade it naturally into the left copy zone."""
        if not hasattr(self, "hero_canvas") or not self.hero_canvas.winfo_exists():
            return
        width = max(640, self.hero_canvas.winfo_width())
        height = max(220, self.hero_canvas.winfo_height())
        try:
            from PIL import ImageDraw, ImageEnhance
            focus_x = THEME_FOCUS_X.get(self.theme_var.get(), 0.55)
            # A right-side image zone with a cinematic 2:1 crop avoids the ultra-wide
            # letterbox-like stretch and preserves faces/characters in the supplied art.
            art_width = min(int(width * 0.50), int(height * 2.0))
            art_width = max(360, art_width)
            target_ratio = art_width / max(1, height)
            source = self._cover_crop(self._hero_source, target_ratio, focus_x=focus_x, focus_y=0.48)
            art = source.resize((art_width, height), Image.Resampling.LANCZOS).convert("RGB")
            art = ImageEnhance.Contrast(art).enhance(1.08)
            art = ImageEnhance.Color(art).enhance(1.10).convert("RGBA")

            base_rgb = self.colors.get("hero_bg", self.colors["bg"])
            base = Image.new("RGBA", (width, height), base_rgb)
            art_x = width - art_width
            # Fade the art itself: transparent at the midpoint, fully present toward
            # the right edge. No separate rectangular overlay can cut across the image.
            fade_span = int(art_width * 0.55)
            alpha_values = [int(255 * (x / max(1, fade_span - 1)) ** 1.35) if x < fade_span else 255
                            for x in range(art_width)]
            alpha_mask = Image.new("L", (art_width, 1))
            alpha_mask.putdata(alpha_values)
            alpha_mask = alpha_mask.resize((art_width, height))
            art.putalpha(alpha_mask)
            base.alpha_composite(art, (art_x, 0))

            # A slight right-edge vignette brings the artwork into the UI palette.
            vignette_values = [int(42 * (x / max(1, art_width - 1)) ** 3) for x in range(art_width)]
            vignette_row = Image.new("L", (art_width, 1))
            vignette_row.putdata(vignette_values)
            vignette = vignette_row.resize((art_width, height))
            tint = Image.new("RGBA", (art_width, height), (0, 0, 0, 0))
            tint.putalpha(vignette)
            base.alpha_composite(tint, (art_x, 0))

            mask = Image.new("L", (width, height), 0)
            ImageDraw.Draw(mask).rounded_rectangle((1, 1, width - 2, height - 2), radius=20, fill=255)
            base.putalpha(mask)
            self.hero_photo = ImageTk.PhotoImage(base)
            self.hero_canvas.itemconfigure(self._hero_bg_item, image=self.hero_photo)
            self.hero_canvas.coords(self._hero_bg_item, 0, 0)
            self.hero_canvas.coords(self._hero_kicker_item, 30, 24)
            self.hero_canvas.coords(self._hero_title_item, 28, 62)
            self.hero_canvas.coords(self._hero_tagline_item, 30, 110)
            self.hero_canvas.coords(self._hero_subtitle_item, 30, 140)
            self.hero_canvas.coords(self._theme_combo_window, 155, 194)
            self.hero_canvas.itemconfigure(self._hero_title_item, width=int(width * 0.58))
            self.hero_canvas.tag_lower(self._hero_bg_item)
            self.hero_canvas.delete("hero_round_outline")
            radius = 20
            border = self.colors["hero_border"]
            self.hero_canvas.create_line(radius, 1, width-radius, 1, fill=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_line(radius, height-2, width-radius, height-2, fill=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_line(1, radius, 1, height-radius, fill=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_line(width-2, radius, width-2, height-radius, fill=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_arc(1, 1, radius*2+1, radius*2+1, start=90, extent=90, style="arc", outline=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_arc(width-radius*2-1, 1, width-1, radius*2+1, start=0, extent=90, style="arc", outline=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_arc(width-radius*2-1, height-radius*2-1, width-1, height-1, start=270, extent=90, style="arc", outline=border, width=2, tags=("hero_round_outline",))
            self.hero_canvas.create_arc(1, height-radius*2-1, radius*2+1, height-1, start=180, extent=90, style="arc", outline=border, width=2, tags=("hero_round_outline",))
        except Exception:
            return

    def _update_scroll_region(self, _event=None):
        if hasattr(self, "canvas"):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_scroll_content(self, event):
        if hasattr(self, "_canvas_window"):
            self.canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Scroll the launcher rather than trapping the user in a clipped form.
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-3, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(3, "units")
        else:
            delta = getattr(event, "delta", 0)
            if delta:
                # Windows reports multiples of 120; macOS usually reports small values.
                units = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
                self.canvas.yview_scroll(units * 3, "units")

    def _set_active_nav(self, label):
        """Keep the sidebar's rounded navigation pill in sync with the selected section."""
        self._active_nav_label = label
        for item in getattr(self, "_nav_button_states", []):
            active = item["label"] == label
            item["canvas"].itemconfigure(item["bg"], fill="#123b58" if active else "#07111f")
            item["canvas"].itemconfigure(item["accent"], fill=self.colors["cyan"] if active else "#07111f")
            item["canvas"].itemconfigure(item["icon"], fill="#57c9ff" if active else "#90a9c3")
            item["canvas"].itemconfigure(item["text"], fill="#eaf6ff" if active else "#b6c8dc",
                                          font=("Segoe UI", 10, "bold" if active else "normal"))

    def _select_theme_from_gallery(self, name):
        if name not in THEME_NAMES or name == self.theme_var.get():
            return
        self.theme_var.set(name)
        self._change_theme()

    def _change_theme(self, _event=None):
        selected = self.theme_var.get()
        if selected not in THEME_NAMES:
            self.theme_var.set("Cyberpunk")
        values = self._collect_ui_settings()
        try:
            self.settings = save_settings(values)
        except OSError as exc:
            messagebox.showerror("Could not save theme", str(exc), parent=self.root)
            self.theme_var.set(self.settings.get("ui_theme", "Cyberpunk"))
            return
        self._configure_style()
        self._build_ui()

    def _update_setting_labels(self):
        self.sensitivity_label.configure(
            text=f"Mouse sensitivity: {self.sensitivity_var.get():.2f}"
        )
        self.deadzone_label.configure(
            text=f"Jitter dead zone: {self.deadzone_var.get():.4f}"
        )
        self.max_step_label.configure(
            text=f"Maximum movement per frame: {int(round(self.max_step_var.get()))} px"
        )

    def _refresh_profile_choices(self):
        if not hasattr(self, "profile_combo"):
            return
        names = ["Current settings", DEFAULT_PROFILE_NAME]
        names.extend(sorted(name for name in self.profiles if name != DEFAULT_PROFILE_NAME))
        self.profile_combo.configure(values=names)
        if self.profile_var.get() not in names:
            self.profile_var.set("Current settings")

    def _collect_ui_settings(self):
        values = {
            "ui_theme": self.theme_var.get(),
            "mouse_sensitivity": self.sensitivity_var.get(),
            "mouse_deadzone": self.deadzone_var.get(),
            "mouse_max_step": self.max_step_var.get(),
        }
        values.update({key: variable.get() for key, variable in self.binding_vars.items()})
        return values

    def _confirm_unique_bindings(self, values):
        chosen_keys = [values[key] for key, _label, _group in BINDINGS]
        if len(set(chosen_keys)) != len(chosen_keys):
            return messagebox.askyesno(
                "Duplicate key assignments",
                "Two or more controls use the same key. This can cause overlapping inputs. Continue?",
                parent=self.root,
            )
        return True

    def load_selected_profile(self):
        name = self.profile_var.get()
        if name == "Current settings":
            messagebox.showinfo("Current settings", "These are the settings currently shown in the control panel.", parent=self.root)
            return
        if self.process is not None and self.process.poll() is None:
            messagebox.showwarning(
                "Stop the controller first",
                "Stop the controller before loading a profile so all keyboard mappings are applied consistently.",
                parent=self.root,
            )
            return
        profile = self.profiles.get(name)
        if profile is None:
            messagebox.showerror("Profile not found", "That profile is no longer available.", parent=self.root)
            self.profiles = load_profiles()
            self._refresh_profile_choices()
            return
        if not self._confirm_unique_bindings(profile):
            return
        self._set_ui_settings(profile)
        if not self.apply_settings():
            return
        self.profile_var.set(name)
        self.profile_hint.configure(text=f"Loaded profile: {name}")

    def _set_ui_settings(self, values):
        self.sensitivity_var.set(values["mouse_sensitivity"])
        self.deadzone_var.set(values["mouse_deadzone"])
        self.max_step_var.set(values["mouse_max_step"])
        for key, variable in self.binding_vars.items():
            variable.set(values[key])
            if key in getattr(self, "binding_buttons", {}):
                self.binding_buttons[key].configure(text=self._display_key(values[key]))
        self._update_setting_labels()

    def save_profile_as(self):
        name = simpledialog.askstring(
            "Save control profile",
            "Give this setup a name (for example, Cyberpunk FPS):",
            parent=self.root,
        )
        if name is None:
            return
        values = self._collect_ui_settings()
        if not self._confirm_unique_bindings(values):
            return
        try:
            clean_name = validate_profile_name(name)
            existing = next((item for item in self.profiles if item.casefold() == clean_name.casefold()), None)
            if existing and existing.casefold() != DEFAULT_PROFILE_NAME.casefold():
                if not messagebox.askyesno(
                    "Replace profile?", f'A profile named "{existing}" already exists. Replace it?', parent=self.root
                ):
                    return
            # Persist the active settings and the profile snapshot together from the user's perspective.
            self.settings = save_settings(values)
            saved_name, normalized = save_profile(name, self.settings)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not save profile", str(exc), parent=self.root)
            return
        self.profiles = load_profiles()
        self._set_ui_settings(normalized)
        self.profile_var.set(saved_name)
        self._refresh_profile_choices()
        self.profile_var.set(saved_name)
        self.profile_hint.configure(text=f"Saved profile: {saved_name}")

    def delete_selected_profile(self):
        name = self.profile_var.get()
        if name in ("Current settings", DEFAULT_PROFILE_NAME):
            messagebox.showinfo("Cannot delete profile", "Choose one of your saved profiles. The built-in Default profile is protected.", parent=self.root)
            return
        if not messagebox.askyesno("Delete profile", f'Delete the profile "{name}"? This cannot be undone.', parent=self.root):
            return
        try:
            delete_profile(name)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Could not delete profile", str(exc), parent=self.root)
            return
        self.profiles = load_profiles()
        self.profile_var.set("Current settings")
        self._refresh_profile_choices()
        self.profile_hint.configure(text=f"Deleted profile: {name}")

    def apply_settings(self):
        values = self._collect_ui_settings()
        if not self._confirm_unique_bindings(values):
            return False
        try:
            self.settings = save_settings(values)
        except OSError as exc:
            messagebox.showerror("Could not save settings", str(exc), parent=self.root)
            return False
        self.sensitivity_var.set(self.settings["mouse_sensitivity"])
        self.deadzone_var.set(self.settings["mouse_deadzone"])
        self.max_step_var.set(self.settings["mouse_max_step"])
        for key, variable in self.binding_vars.items():
            variable.set(self.settings[key])
            if key in getattr(self, "binding_buttons", {}):
                self.binding_buttons[key].configure(text=self._display_key(self.settings[key]))
        self._update_setting_labels()
        if self.process is not None and self.process.poll() is None:
            messagebox.showinfo(
                "Settings saved",
                "Mouse settings are applied live. Keyboard binding changes take effect after you stop and start the controller again.",
                parent=self.root,
            )
        return True

    def start_controller(self):
        if self.process is not None and self.process.poll() is None:
            return

        if not self.apply_settings():
            return
        clear_stop_request()

        try:
            if getattr(sys, "frozen", False):
                command = [str(app_dir() / "HandGameControllerCore.exe")]
            else:
                command = [sys.executable, str(app_dir() / "mian.py")]

            self.process = subprocess.Popen(
                command,
                cwd=str(app_dir())
            )
        except (OSError, ValueError) as exc:
            messagebox.showerror(
                "Could not start controller",
                f"{exc}\n\nCheck that the project files and dependencies are installed.",
                parent=self.root
            )
            self.process = None
            return

        self.controller_status.configure(text="Controller: starting")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def stop_controller(self):
        if self.process is not None and self.process.poll() is None:
            request_stop()
            self.controller_status.configure(text="Controller: stopping safely…")
            self.status_banner.configure(text="◌  STOPPING SAFELY…", bg=self.colors["stop_bg"], fg=self.colors["pink"])
        else:
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _refresh_status(self):
        status = read_status()
        process_running = self.process is not None and self.process.poll() is None
        status_fresh = (
            status
            and status.get("running")
            and (time.time() - status.get("updated_at", 0) < 2.0)
        )

        if process_running:
            self.controller_status.configure(text="Controller: running")
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.status_banner.configure(
                text="●  CONTROLLER ONLINE" if status_fresh else "◌  STARTING CAMERA + HAND TRACKING…",
                bg=self.colors["banner_online"] if status_fresh else self.colors["banner_starting"],
                fg=self.colors["lime"] if status_fresh else self.colors["orange"],
            )
        else:
            self.controller_status.configure(text="Controller: stopped")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.status_banner.configure(text="●  CONTROLLER OFFLINE", bg=self.colors["banner_off"], fg=self.colors["muted"])
            self.process = None

        if process_running and status_fresh:
            self.calibration_status.configure(
                text="Calibration: ready" if status.get("calibrated") else "Calibration: waiting"
            )
            self.left_status.configure(
                text="Right hand: detected" if status.get("left_hand_detected") else "Right hand: not detected"
            )
            self.right_status.configure(
                text="Left hand: detected" if status.get("right_hand_detected") else "Left hand: not detected"
            )
            active = status.get("active_controls") or []
            self.active_status.configure(
                text="Active controls: " + (", ".join(active) if active else "none")
            )
            self.movement_status.configure(
                text=f"Movement: {status.get('movement', '—')}"
            )
            self.mouse_status.configure(
                text=(
                    "Mouse mode: active"
                    if status.get("mouse_active")
                    else "Mouse mode: off"
                )
            )
            self.fps_status.configure(
                text=f"Tracking rate: {status.get('fps', 0.0):.1f} FPS"
            )
            self.aim_status.configure(text="Aim: ACTIVE" if status.get("aim_active") else "Aim: off")
        elif not process_running:
            self.calibration_status.configure(text="Calibration: —")
            self.left_status.configure(text="Right hand: —")
            self.right_status.configure(text="Left hand: —")
            self.active_status.configure(text="Active controls: none")
            self.movement_status.configure(text="Movement: —")
            self.mouse_status.configure(text="Mouse mode: —")
            self.fps_status.configure(text="Tracking rate: —")
            self.aim_status.configure(text="Aim: —")

        self.root.after(300, self._refresh_status)

    def on_close(self):
        if self.process is not None and self.process.poll() is None:
            request_stop()
            self.root.after(500, self.root.destroy)
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    ControllerLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
