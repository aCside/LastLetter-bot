import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, simpledialog
import random
import time
import json
import threading
import ctypes
import sys
import os
import subprocess
import winsound
import traceback
import queue
import string

# --- 0. SELF-INSTALLER & PRE-CHECKS ---
def check_and_install_libs():
    """Checks for required libraries and installs them if missing."""
    required_libs = [
        ("pydirectinput", "pydirectinput"),
        ("keyboard", "keyboard"),
        ("requests", "requests"),
        ("pygetwindow", "pygetwindow")
    ]
    
    install_needed = False
    for import_name, package_name in required_libs:
        try:
            __import__(import_name)
        except ImportError:
            print(f"[TitanBot] Installing missing library: {package_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                install_needed = True
            except subprocess.CalledProcessError as e:
                print(f"[TitanBot] Failed to install {package_name}. Error: {e}")
                input("Press Enter to exit...")
                sys.exit()
    
    if install_needed:
        print("[TitanBot] Libraries installed. Restarting...")
        time.sleep(1)
        # Restart script to ensure libs are loaded correctly
        os.execv(sys.executable, ['python'] + sys.argv)

# Run the check before anything else
check_and_install_libs()

# --- 1. ADMIN CHECK ---
try:
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Re-run the program with admin rights
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
except Exception as e:
    print(f"Admin Check Failed: {e}")

# --- 2. SETUP PATHS & FILES ---
try:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    os.chdir(SCRIPT_DIR)
except: 
    pass

USED_FILE = "used_words.json"
BLACKLIST_FILE = "blacklist.json"
PROFILES_FILE = "profiles.json"
DB_FILE = "word_database.json"
WINDOW_FILE = "window.json"
HISTORY_FILE = "history.json"
LAST_SET_FILE = "last_settings.json"

# --- 3. IMPORTS (Safe now) ---
import pydirectinput
import keyboard
import requests
import pygetwindow as gw

pydirectinput.PAUSE = 0.001
pydirectinput.FAILSAFE = False

KILLER_ENDINGS = ('x', 'z', 'j', 'q', 'v', 'k', 'b')
KEY_NEIGHBORS = {'q': 'wa', 'w': 'qase', 'e': 'wsdr', 'r': 'edft', 't': 'rfgy', 'y': 'tghu', 'u': 'yhji', 'i': 'ujko', 'o': 'iklp', 'p': 'ol', 'a': 'qwsz', 's': 'weadzx', 'd': 'ersfxc', 'f': 'rtdgcv', 'g': 'tyfhvb', 'h': 'ybgnjm', 'j': 'uinhkm', 'k': 'iojlm', 'l': 'opk', 'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb', 'b': 'vghn', 'n': 'bhjm', 'm': 'njk'}

# Words that theoretically exist but are often banned or considered garbage/proper nouns in word games
BUILTIN_BLACKLIST = {
    # Nonsense / Obscure codes provided by user
    'xvx', 'xxx', 'otcbb', 'otv', 'klez', 'kleeb', 'niab', 'apegnb',
    # Common Days/Months (Proper nouns)
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december',
    # Continents (Proper nouns)
    'africa', 'america', 'asia', 'europe', 'australia', 'antarctica',
    # Roman Numerals
    'ii', 'iii', 'iv', 'vi', 'vii', 'viii', 'ix', 'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx',
    # Popular Websites/Brands (often appear in loose dictionaries)
    'google', 'youtube', 'facebook', 'instagram', 'twitter', 'tiktok', 'reddit', 'wikipedia', 'amazon', 'yahoo', 
    'bing', 'msn', 'ebay', 'netflix', 'twitch', 'discord', 'whatsapp', 'skype', 'pinterest', 'linkedin'
}

# --- THEMES ---
THEMES = {
    "Dark": {
        "bg": "#121212", "panel": "#1E1E1E", "primary": "#00ADB5", 
        "text": "#EEEEEE", "text_dim": "#AAAAAA", "input_bg": "#2b2b2b", 
        "btn_bg": "#393E46", "warn": "#FFD600", "err": "#CF6679", "success": "#00C853",
        "sb_bg": "#333333", "sb_trough": "#121212", "sb_active": "#00ADB5"
    },
    "Light": {
        "bg": "#F5F5F5", "panel": "#FFFFFF", "primary": "#007ACC", 
        "text": "#222222", "text_dim": "#666666", "input_bg": "#E0E0E0", 
        "btn_bg": "#DDDDDD", "warn": "#FFC107", "err": "#D32F2F", "success": "#388E3C",
        "sb_bg": "#BBBBBB", "sb_trough": "#F0F0F0", "sb_active": "#007ACC"
    }
}

# --- 4. DATA MANAGER ---
class DataManager:
    def __init__(self):
        # Create files if they don't exist
        self.used = self.load_json(USED_FILE, [])
        self.blacklist = self.load_json(BLACKLIST_FILE, [])
        self.profiles = self.load_json(PROFILES_FILE, {})
        self.db = self.load_json(DB_FILE, {"titan": {}, "common": {}})
        self.history_data = self.load_json(HISTORY_FILE, [])
        self.last_settings = self.load_json(LAST_SET_FILE, {})
        self.window_cfg = self.load_json(WINDOW_FILE, {
            "0": "450x650", "1": "450x650", "2": "450x650", 
            "position": "", "last_tab": 0, "theme": "Dark",
            "last_profile": ""
        })
        self.session_used = set() # Store words used in this session to prevent repeats
    
    def load_json(self, f, d):
        if not os.path.exists(f): 
            self.save_json(d, f)
            return d
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                if isinstance(d, list) and not isinstance(data, list): return list(data)
                return data
        except: return d
        
    def save_json(self, d, f):
        try:
            with open(f, 'w') as file:
                json.dump(d, file, indent=4)
        except: pass
            
    def add_used(self, w): 
        if w not in self.used:
            self.used.append(w)
            self.save_json(self.used, USED_FILE)

    def remove_used(self, w):
        if w in self.used: 
            self.used.remove(w)
            self.save_json(self.used, USED_FILE)
        
    def add_blacklist(self, w): 
        if w not in self.blacklist:
            self.blacklist.append(w)
            self.save_json(self.blacklist, BLACKLIST_FILE)

    def remove_blacklist(self, w): 
        if w in self.blacklist: 
            self.blacklist.remove(w)
            self.save_json(self.blacklist, BLACKLIST_FILE)
        
    def save_history(self, history_list):
        self.save_json(history_list, HISTORY_FILE)

    def save_last_settings(self, settings):
        self.save_json(settings, LAST_SET_FILE)

    def save_profile_data(self): self.save_json(self.profiles, PROFILES_FILE)
    def save_win_data(self): self.save_json(self.window_cfg, WINDOW_FILE)

    def add_word_to_db(self, word):
        first = word[0].lower()
        if "common" not in self.db: self.db["common"] = {}
        if first not in self.db["common"]: self.db["common"][first] = []
        if word not in self.db["common"][first]:
            self.db["common"][first].append(word)
            self.save_json(self.db, DB_FILE)
            return True
        return False

# --- 5. WORD GENERATOR ---
class WordGenerator:
    def __init__(self, dm):
        self.dm = dm
        self.last_candidates = [] 
        self.last_index = 0

    def is_valid(self, w): 
        # Must be alpha, no hyphens/spaces
        if not w.replace("'", "").isalpha() or '-' in w or ' ' in w:
            return False
        # Must contain at least one vowel (filter out garbage like 'xvx', 'xxx')
        if not any(char in 'aeiouy' for char in w.lower()):
            return False
        return True
    
    def get_word(self, letters, min_len, max_len, strategy, priorities, current_target="", reroll=False):
        letters = letters.strip().lower()
        if not letters: return None, False

        # If rerolling, try to use the cached list to speed things up, 
        # but filter out words already used in session AND BLACKLISTED words
        if reroll and self.last_candidates:
            self.last_index += 1
            while self.last_index < len(self.last_candidates):
                candidate = self.last_candidates[self.last_index]
                # Check session used AND global blacklist/used in case it was just banned
                # AND check built-in blacklist
                if (candidate not in self.dm.session_used and 
                    candidate not in self.dm.blacklist and 
                    candidate not in self.dm.used and 
                    candidate not in BUILTIN_BLACKLIST):
                    return candidate, False
                self.last_index += 1
            # If we ran out of candidates in the cached list, fall through to regenerate

        candidates = []
        titan_list = self.dm.db.get("titan", {}).get(letters[0], [])
        common_list = self.dm.db.get("common", {}).get(letters[0], [])
        
        candidates.extend(titan_list)
        candidates.extend(common_list)
        
        if len(candidates) < 50: 
            try:
                # Add &md=p to get Parts of Speech tags
                r = requests.get(f"https://api.datamuse.com/words?sp={letters}*&max=300&md=p", timeout=1.5)
                if r.status_code == 200: 
                    # Filter based on tags (remove Proper Nouns)
                    for item in r.json():
                        w_str = item['word']
                        tags = item.get('tags', [])
                        # Skip if tagged as proper noun (names, cities, etc.)
                        if 'prop' in tags: continue 
                        candidates.append(w_str)
            except: pass
            
        valid = []
        for w in candidates:
            w = w.lower()
            if not self.is_valid(w) or not w.startswith(letters): continue
            if w in self.dm.used or w in self.dm.blacklist: continue
            if w in self.dm.session_used: continue # Check session used words
            if w in BUILTIN_BLACKLIST: continue # Check built-in garbage/names
            if w == current_target: continue 
            
            l = len(w)
            if l < min_len or l > max_len: continue
            valid.append(w)
            
        seen = set()
        unique_valid = [x for x in valid if not (x in seen or seen.add(x))]
        
        final_list = []

        # Helper to calculate killer score based on suffix rarity
        def get_killer_score(w):
            score = 0
            # Weight the last 5 characters
            # Char at -1 (last) gives most points, -2 gives less, etc.
            l = len(w)
            for i in range(1, 6):
                if l >= i:
                    char = w[-i]
                    if char in KILLER_ENDINGS:
                        # Prioritize position: last char is worth 10, then 5, 3, 2, 1
                        points = {1: 10, 2: 5, 3: 3, 4: 2, 5: 1}
                        score += points[i]
            return score

        if strategy == "Custom":
            pool = list(unique_valid)
            def extract_subset(source_list, criterion):
                extracted = []
                remaining = []
                for w in source_list:
                    match = False
                    if criterion == "Long & Killer":
                        # Check last char or high killer score
                        if w.endswith(KILLER_ENDINGS) or get_killer_score(w) > 3: match = True
                    elif criterion == "Killer":
                        if get_killer_score(w) > 0: match = True
                    elif criterion == "Longest": match = True 
                    elif criterion == "Random": match = True
                    if match: extracted.append(w)
                    else: remaining.append(w)
                
                if criterion == "Long & Killer":
                    # Sort by score desc, then length desc
                    extracted.sort(key=lambda x: (get_killer_score(x), len(x)), reverse=True)
                elif criterion == "Killer":
                    # Sort primarily by killer score
                    extracted.sort(key=lambda x: get_killer_score(x), reverse=True)
                elif criterion == "Longest":
                    extracted.sort(key=len, reverse=True)
                elif criterion == "Random":
                    random.shuffle(extracted)
                return extracted, remaining

            if priorities[0] != "Random" and priorities[0] != "Same Mode": 
                subset, pool = extract_subset(pool, priorities[0])
                final_list.extend(subset)
            if priorities[1] != "Random" and priorities[1] != "Same Mode":
                subset, pool = extract_subset(pool, priorities[1])
                final_list.extend(subset)
            if priorities[2] != "Random" and priorities[2] != "Same Mode":
                subset, pool = extract_subset(pool, priorities[2])
                final_list.extend(subset)
            
            pool.sort(key=len, reverse=True)
            final_list.extend(pool)

        elif strategy == "Killer": 
            # Sort by accumulated killer score of last 5 chars
            final_list = sorted(unique_valid, key=lambda x: get_killer_score(x), reverse=True)
        elif strategy == "Smart": 
            final_list = sorted(unique_valid, key=len, reverse=True)
        elif strategy == "Smart + Killer":
            final_list = sorted(unique_valid, key=lambda x: (get_killer_score(x), len(x)), reverse=True)
        else: 
            final_list = list(unique_valid)
            random.shuffle(final_list)

        self.last_candidates = final_list
        self.last_index = 0
        if not final_list: return None, False
        chosen = final_list[0]
        return chosen, (chosen not in common_list and chosen not in titan_list)

# --- 6. UTILS ---
class ScrollableFrame(tk.Frame):
    def __init__(self, container, bg_color="#121212", *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.configure(bg=bg_color)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=bg_color)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.window_item = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        
    def _on_frame_configure(self, event): self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_canvas_configure(self, event): self.canvas.itemconfig(self.window_item, width=event.width)
    def configure_colors(self, bg_color, sb_bg, sb_trough, sb_active):
        self.configure(bg=bg_color)
        self.canvas.configure(bg=bg_color)
        self.scrollable_frame.configure(bg=bg_color)
        try: self.scrollbar.configure(bg=sb_bg, troughcolor=sb_trough, activebackground=sb_active, borderwidth=0)
        except: pass

# --- 7. GUI CLASS ---
class BotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TitanBot v6.6")
        
        self.dm = DataManager()
        self.gen = WordGenerator(self.dm)
        self.gui_queue = queue.Queue()
        
        self.stop_flag = False
        self.is_typing_active = False 
        self.manual_step_active = True 
        self.target_word = ""
        self.typed_history = ""
        self.current_theme = self.dm.window_cfg.get("theme", "Dark")
        self.smart_input_active = False
        self.was_smart_active = False 
        self.smart_hooks = []
        self.active_step_hook = None 
        self.typing_gen = 0 # Generation ID for typing threads
        self.last_reroll_time = 0
        self.last_ban_time = 0
        self.processing_action = False # Flag to prevent overlap/spam
        
        self.topmost_var = tk.BooleanVar(value=True)
        self.sound_var = tk.BooleanVar(value=True)
        self.win_list_var = tk.StringVar(value="Active Window")
        
        self.entry_var = tk.StringVar()
        
        # --- Variables ---
        self.len_min_var = tk.IntVar(value=1)
        self.len_max_var = tk.IntVar(value=30)
        self.strat_var = tk.StringVar(value="Random")
        self.skip_var = tk.BooleanVar(value=True)
        self.human_var = tk.BooleanVar(value=True)
        self.auto_type_var = tk.BooleanVar(value=True)
        self.auto_enter_var = tk.BooleanVar(value=True)
        self.save_db_var = tk.BooleanVar(value=False)
        self.manual_step_var = tk.BooleanVar(value=True)
        self.ban_reroll_var = tk.BooleanVar(value=True)
        
        self.lat_min_var = tk.StringVar(value="50")
        self.lat_max_var = tk.StringVar(value="150")
        self.start_delay_min_var = tk.StringVar(value="250")
        self.start_delay_max_var = tk.StringVar(value="400")
        self.reroll_delay_min_var = tk.StringVar(value="500")
        self.reroll_delay_max_var = tk.StringVar(value="800")
        self.len_delay_min_var = tk.StringVar(value="10")
        self.len_delay_max_var = tk.StringVar(value="30")
        self.erase_speed_min_var = tk.StringVar(value="20")
        self.erase_speed_max_var = tk.StringVar(value="50")
        self.realization_min_var = tk.StringVar(value="150")
        self.realization_max_var = tk.StringVar(value="400")
        self.err_delay_min_var = tk.StringVar(value="1")
        self.err_delay_max_var = tk.StringVar(value="3")

        self.error_mode_var = tk.StringVar(value="Interval") 
        self.err_chance_val = tk.StringVar(value="4") 
        self.err_int_min = tk.StringVar(value="15") 
        self.err_int_max = tk.StringVar(value="30") 

        self.p1_var = tk.StringVar(value="Long & Killer")
        self.p2_var = tk.StringVar(value="Longest")
        self.p3_var = tk.StringVar(value="Killer")

        # Reroll Specific Priorities
        self.rr_p1_var = tk.StringVar(value="Same Mode")
        self.rr_p2_var = tk.StringVar(value="Same Mode")
        self.rr_p3_var = tk.StringVar(value="Same Mode")

        self.step_key_var = tk.StringVar(value="z")
        self.reroll_key_var = tk.StringVar(value="f4")
        self.smart_key_var = tk.StringVar(value="f2")
        self.stop_key_var = tk.StringVar(value="esc")
        self.ban_key_var = tk.StringVar(value="")
        self.unban_key_var = tk.StringVar(value="")
        
        self.stop_action_typing = tk.BooleanVar(value=True)
        self.stop_action_smart = tk.BooleanVar(value=False)

        self.profile_var = tk.StringVar()

        self.step_key = "z"
        self.reroll_key = "f4"
        self.smart_key = "f2"
        self.stop_key = "esc"
        self.ban_key = ""
        self.unban_key = ""

        # --- APPLY SAVED SETTINGS IF EXIST ---
        if self.dm.last_settings:
            self.apply_dict_settings(self.dm.last_settings)

        t = THEMES[self.current_theme]
        self.root.configure(bg=t["bg"])

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=t["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=t["panel"], foreground=t["text"], borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", t["primary"])], foreground=[("selected", "white")])

        self.setup_ui()
        self.apply_theme()
        
        self.current_tab = self.dm.window_cfg.get("last_tab", 0)
        
        init_size = self.dm.window_cfg.get(str(self.current_tab), "450x650")
        try:
            w_check, h_check = map(int, init_size.split("x"))
            if w_check < 200 or h_check < 200:
                init_size = "450x650"
        except:
            init_size = "450x650"

        init_pos = self.dm.window_cfg.get("position", "")
        self.root.geometry(f"{init_size}{init_pos}")
        self.root.attributes('-topmost', True)
        
        self.refresh_profile_list()
        self.update_binds()
        self.refresh_window_list()
        self.refresh_aux_lists()
        
        # Load persistent history
        for item in reversed(self.dm.history_data):
            self.history_list.insert(0, item)
        self.refresh_history_colors()
        
        try: self.notebook.select(self.current_tab)
        except: pass
        
        self.hook_handle = keyboard.hook(self.on_key_event)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.root.after(100, self.toggle_smart_input)
        self.process_gui_queue()

    def process_gui_queue(self):
        try:
            while True:
                task = self.gui_queue.get_nowait()
                task[0](*task[1])
        except queue.Empty: pass
        self.root.after(50, self.process_gui_queue)

    def setup_ui(self):
        t = THEMES[self.current_theme]
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.top_bar = tk.Frame(self.root, bg=t["bg"])
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        tk.Checkbutton(self.top_bar, text="Top", variable=self.topmost_var, command=lambda: self.root.attributes('-topmost', self.topmost_var.get()), 
                       bg=t["bg"], fg=t["text"], selectcolor=t["bg"], activebackground=t["bg"]).pack(side="left", padx=2)
        tk.Button(self.top_bar, text="Theme", command=self.toggle_theme, width=6, relief="flat", font=("Segoe UI", 8), bg=t["btn_bg"], fg=t["text"]).pack(side="left", padx=5)
        
        win_frame = tk.Frame(self.top_bar, bg=t["bg"])
        win_frame.pack(side="right", fill="x", expand=True, padx=5)
        self.win_cb = ttk.Combobox(win_frame, textvariable=self.win_list_var, state="readonly")
        self.win_cb.pack(side="right", fill="x", expand=True)
        self.win_cb.bind("<Button-1>", lambda e: self.refresh_window_list())
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # --- TAB 1: EXECUTE ---
        self.tab_gen = tk.Frame(self.notebook, bg=t["bg"])
        self.notebook.add(self.tab_gen, text=" EXECUTE ")
        self.tab_gen.columnconfigure(0, weight=1)
        self.tab_gen.rowconfigure(3, weight=1)

        self.title_lbl = tk.Label(self.tab_gen, text="TITAN OS", font=("Segoe UI", 18, "bold"), bg=t["bg"], fg=t["primary"])
        self.title_lbl.grid(row=0, column=0, pady=(15, 5))

        inp_frame = tk.Frame(self.tab_gen, bg=t["bg"])
        inp_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        inp_frame.columnconfigure(0, weight=1)
        
        self.entry = tk.Entry(inp_frame, textvariable=self.entry_var, font=("Consolas", 24), justify="center", relief="flat", bg=t["input_bg"], fg=t["primary"], insertbackground=t["text"])
        self.entry.grid(row=0, column=0, sticky="ew")
        self.entry.bind('<Return>', self.on_enter)
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        
        self.btn_smart = tk.Button(inp_frame, text="SMART\nINPUT", command=self.toggle_smart_input, font=("Segoe UI", 8, "bold"), relief="flat", bg=t["btn_bg"], fg=t["text"], width=6)
        self.btn_smart.grid(row=0, column=1, padx=(5, 0), sticky="ns")

        vis_frame = tk.Frame(self.tab_gen, bd=2, relief="flat", bg=t["bg"])
        vis_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        vis_frame.columnconfigure(0, weight=1)
        
        vis_header = tk.Frame(vis_frame, bg=t["bg"])
        vis_header.grid(row=0, column=0, sticky="ew")
        vis_header.columnconfigure(0, weight=1)
        
        self.res_lbl = tk.Label(vis_header, text="READY", font=("Segoe UI", 12, "bold"), bg=t["bg"], fg=t["text_dim"])
        self.res_lbl.grid(row=0, column=0, pady=2)
        
        self.btn_clear = tk.Button(vis_header, text="Clr", command=self.clear_visuals, font=("Segoe UI", 8), relief="flat", bg=t["btn_bg"], fg=t["text"])
        self.btn_clear.grid(row=0, column=1, padx=5, sticky="e")
        
        self.vis_text = tk.Text(vis_frame, font=("Consolas", 14), height=3, bd=0, cursor="arrow", wrap="word", bg=t["input_bg"], fg=t["text"])
        self.vis_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.vis_text.tag_config("correct", foreground="#777")
        self.vis_text.tag_config("wrong", foreground=t["err"], underline=1)
        self.vis_text.tag_config("remain", foreground=t["text"])
        self.vis_text.insert("1.0", "Waiting for input...")
        self.vis_text.configure(state="disabled")

        hist_frame = tk.Frame(self.tab_gen, bg=t["bg"])
        hist_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=5)
        
        self.info_notebook = ttk.Notebook(hist_frame)
        self.info_notebook.pack(fill="both", expand=True)

        def make_list_tab(name, has_controls=False):
            f = tk.Frame(self.info_notebook, bg=t["panel"])
            self.info_notebook.add(f, text=name)
            
            content = tk.Frame(f, bg=t["panel"])
            content.pack(fill="both", expand=True)
            
            sb = tk.Scrollbar(content, orient="vertical", bg=t["sb_bg"], troughcolor=t["sb_trough"], activebackground=t["sb_active"], borderwidth=0)
            
            lst = tk.Listbox(content, font=("Consolas", 10), bd=0, relief="flat", highlightthickness=0, 
                             yscrollcommand=sb.set, bg=t["panel"], fg=t["text"], selectbackground=t["primary"],
                             selectmode=tk.EXTENDED)
            sb.config(command=lst.yview)
            lst.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            
            if has_controls:
                ctrl = tk.Frame(f, bg=t["panel"], pady=2)
                ctrl.pack(fill="x")
                return f, lst, ctrl
            return f, lst

        _, self.history_list, self.hist_ctrl = make_list_tab("History", True)
        tk.Button(self.hist_ctrl, text="Add DB", command=self.add_selected_to_db, 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(self.hist_ctrl, text="BAN", command=self.ban_selected_from_history, 
                  bg=t["warn"], fg="#000", width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(self.hist_ctrl, text="Unban", command=self.unban_selected_from_history, 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(self.hist_ctrl, text="Clr Hist", command=self.clear_history, 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")

        _, self.blacklist_list, self.bl_ctrl = make_list_tab("Blacklist", True)
        self.create_list_controls(self.bl_ctrl, self.blacklist_list, "bl")

        _, self.db_list, self.db_ctrl = make_list_tab("Words DB", True)
        self.create_list_controls(self.db_ctrl, self.db_list, "db")

        _, self.profiles_list_tab, self.pf_ctrl = make_list_tab("Profiles", True)
        self.create_list_controls(self.pf_ctrl, self.profiles_list_tab, "pf")
        tk.Button(self.pf_ctrl, text="Load", command=lambda: self.load_profile_from_tab(None), 
                  bg=t["primary"], fg="white", width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(self.pf_ctrl, text="Save", command=self.save_profile, 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        self.profiles_list_tab.bind("<Double-Button-1>", self.load_profile_from_tab)


        btn_frame = tk.Frame(self.tab_gen, bg=t["bg"])
        btn_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=15)
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        self.btn_reroll = tk.Button(btn_frame, text="REROLL", command=self.reroll, font=("Segoe UI", 10, "bold"), relief="flat", bg=t["warn"], fg="#000")
        self.btn_reroll.grid(row=0, column=0, sticky="ew", padx=2)
        self.btn_stop = tk.Button(btn_frame, text="STOP", command=self.stop_typing, font=("Segoe UI", 10, "bold"), relief="flat", bg=t["err"], fg="#FFF")
        self.btn_stop.grid(row=0, column=1, sticky="ew", padx=2)
        
        self.status_lbl = tk.Label(self.tab_gen, text="System Ready", font=("Segoe UI", 9), bg=t["bg"], fg=t["text"])
        self.status_lbl.grid(row=5, column=0, pady=5)

        # --- TAB 2: CONFIG ---
        self.tab_set = tk.Frame(self.notebook, bg=t["bg"])
        self.notebook.add(self.tab_set, text=" CONFIG ")
        self.scroll_set = ScrollableFrame(self.tab_set, bg_color=t["bg"])
        self.scroll_set.configure_colors(t["bg"], t["sb_bg"], t["sb_trough"], t["sb_active"])
        self.scroll_set.pack(fill="both", expand=True)
        self.set_frame = self.scroll_set.scrollable_frame
        
        def add_header(parent, text): tk.Label(parent, text=text, font=("Segoe UI", 11, "bold"), anchor="w", bg=t["bg"], fg=t["primary"]).pack(fill="x", pady=(10, 5))
        def add_card(parent):
            f = tk.Frame(parent, padx=10, pady=10, bg=t["panel"])
            f.pack(fill="x", padx=10, pady=5)
            return f

        add_header(self.set_frame, "  WORD FILTERS")
        c1 = add_card(self.set_frame)
        r1 = tk.Frame(c1, bg=t["panel"]); r1.pack(fill="x")
        tk.Label(r1, text="Length:", width=8, anchor="w", bg=t["panel"], fg=t["text"]).pack(side="left")
        tk.Entry(r1, textvariable=self.len_min_var, width=5, justify="center", bg=t["input_bg"], fg=t["text"]).pack(side="left")
        tk.Label(r1, text="-", bg=t["panel"], fg=t["text"]).pack(side="left", padx=5)
        tk.Entry(r1, textvariable=self.len_max_var, width=5, justify="center", bg=t["input_bg"], fg=t["text"]).pack(side="left")
        ttk.Combobox(r1, textvariable=self.strat_var, values=["Random", "Smart", "Killer", "Smart + Killer", "Custom"], width=13, state="readonly").pack(side="right")

        tk.Label(c1, text="Custom Strategy Priority:", font=("Segoe UI", 9, "bold"), anchor="w", bg=t["panel"], fg=t["text"]).pack(fill="x", pady=(10,2))
        r_prio = tk.Frame(c1, bg=t["panel"]); r_prio.pack(fill="x")
        
        prio_opts = ["Long & Killer", "Longest", "Killer", "Random"]
        
        def make_prio_drop(var, lbl, parent_frame, opts):
            f = tk.Frame(parent_frame, bg=t["panel"])
            f.pack(side="left", fill="x", expand=True, padx=2)
            tk.Label(f, text=lbl, font=("Segoe UI", 8), bg=t["panel"], fg=t["text_dim"]).pack(anchor="w")
            ttk.Combobox(f, textvariable=var, values=opts, state="readonly", width=12).pack(fill="x")

        make_prio_drop(self.p1_var, "1st:", r_prio, prio_opts)
        make_prio_drop(self.p2_var, "2nd:", r_prio, prio_opts)
        make_prio_drop(self.p3_var, "3rd:", r_prio, prio_opts)

        add_header(self.set_frame, "  REROLL STRATEGY")
        c_rr = add_card(self.set_frame)
        r_rr = tk.Frame(c_rr, bg=t["panel"]); r_rr.pack(fill="x")
        rr_opts = ["Same Mode", "Long & Killer", "Longest", "Killer", "Random"]
        make_prio_drop(self.rr_p1_var, "Reroll 1st:", r_rr, rr_opts)
        make_prio_drop(self.rr_p2_var, "Reroll 2nd:", r_rr, rr_opts)
        make_prio_drop(self.rr_p3_var, "Reroll 3rd:", r_rr, rr_opts)

        add_header(self.set_frame, "  BEHAVIOR")
        c2 = add_card(self.set_frame)
        
        def add_range_row(p, txt, var_min, var_max):
            r = tk.Frame(p, bg=t["panel"]); r.pack(fill="x", pady=2)
            tk.Label(r, text=txt, width=18, anchor="w", bg=t["panel"], fg=t["text"]).pack(side="left")
            tk.Entry(r, textvariable=var_min, width=5, justify="center", bg=t["input_bg"], fg=t["text"]).pack(side="left")
            tk.Label(r, text="-", bg=t["panel"], fg=t["text"]).pack(side="left", padx=5)
            tk.Entry(r, textvariable=var_max, width=5, justify="center", bg=t["input_bg"], fg=t["text"]).pack(side="left")

        add_range_row(c2, "Latency (ms):", self.lat_min_var, self.lat_max_var)
        add_range_row(c2, "Start Delay (ms):", self.start_delay_min_var, self.start_delay_max_var)
        add_range_row(c2, "Thinking Time (ms):", self.reroll_delay_min_var, self.reroll_delay_max_var)
        add_range_row(c2, "Length Delay (ms/char):", self.len_delay_min_var, self.len_delay_max_var)
        add_range_row(c2, "Erase Speed (ms):", self.erase_speed_min_var, self.erase_speed_max_var)
        add_range_row(c2, "Realization (ms):", self.realization_min_var, self.realization_max_var)
        add_range_row(c2, "Error Delay (chars):", self.err_delay_min_var, self.err_delay_max_var)

        tk.Label(c2, text="Error Frequency:", font=("Segoe UI", 9, "bold"), anchor="w", bg=t["panel"], fg=t["text"]).pack(fill="x", pady=(5,2))
        
        r_err_mode = tk.Frame(c2, bg=t["panel"]); r_err_mode.pack(fill="x")
        
        def toggle_err_ui():
            if self.error_mode_var.get() == "Chance":
                f_chance.pack(side="left", fill="x", expand=True)
                f_int.pack_forget()
            else:
                f_chance.pack_forget()
                f_int.pack(side="left", fill="x", expand=True)

        ttk.Combobox(r_err_mode, textvariable=self.error_mode_var, values=["Chance", "Interval"], state="readonly", width=10).pack(side="left")
        self.error_mode_var.trace("w", lambda *args: toggle_err_ui())

        f_chance = tk.Frame(r_err_mode, bg=t["panel"])
        tk.Label(f_chance, text="Chance %:", bg=t["panel"], fg=t["text"]).pack(side="left", padx=5)
        tk.Entry(f_chance, textvariable=self.err_chance_val, width=5, bg=t["input_bg"], fg=t["text"], justify="center").pack(side="left")

        f_int = tk.Frame(r_err_mode, bg=t["panel"])
        tk.Label(f_int, text="Every:", bg=t["panel"], fg=t["text"]).pack(side="left", padx=5)
        tk.Entry(f_int, textvariable=self.err_int_min, width=4, bg=t["input_bg"], fg=t["text"], justify="center").pack(side="left")
        tk.Label(f_int, text="-", bg=t["panel"], fg=t["text"]).pack(side="left", padx=2)
        tk.Entry(f_int, textvariable=self.err_int_max, width=4, bg=t["input_bg"], fg=t["text"], justify="center").pack(side="left")
        tk.Label(f_int, text="Lett.", bg=t["panel"], fg=t["text"]).pack(side="left", padx=2)
        
        toggle_err_ui() 

        r_chk = tk.Frame(c2, bg=t["panel"]); r_chk.pack(fill="x", pady=5)
        def mk_chk(txt, var, r, c): tk.Checkbutton(r_chk, text=txt, variable=var, command=self.update_binds, bg=t["panel"], fg=t["text"], selectcolor=t["panel"], activebackground=t["panel"]).grid(row=r, column=c, sticky="w")
        mk_chk("Skip Input", self.skip_var, 0, 0)
        mk_chk("Human Errors", self.human_var, 0, 1)
        mk_chk("Auto Type", self.auto_type_var, 1, 0)
        mk_chk("Auto Enter", self.auto_enter_var, 1, 1)
        mk_chk("Save DB", self.save_db_var, 2, 0)
        mk_chk("Manual Step", self.manual_step_var, 2, 1)
        mk_chk("Ban Reroll", self.ban_reroll_var, 3, 0)

        add_header(self.set_frame, "  HOTKEYS")
        c3 = add_card(self.set_frame)
        def add_key_row(p, txt, var):
            r = tk.Frame(p, bg=t["panel"]); r.pack(fill="x", pady=2)
            tk.Label(r, text=txt, width=10, anchor="w", bg=t["panel"], fg=t["text"]).pack(side="left")
            tk.Entry(r, textvariable=var, width=10, justify="center", state="readonly", bg=t["input_bg"], fg=t["text"], readonlybackground=t["input_bg"]).pack(side="left", padx=5)
            tk.Button(r, text="Set", command=lambda: self.start_key_bind(var), width=4, relief="flat", font=("Segoe UI", 8), bg=t["btn_bg"], fg=t["text"]).pack(side="left")
        add_key_row(c3, "Step Key:", self.step_key_var)
        add_key_row(c3, "Reroll Key:", self.reroll_key_var)
        add_key_row(c3, "Smart Input:", self.smart_key_var)
        add_key_row(c3, "Stop Key:", self.stop_key_var)
        add_key_row(c3, "Ban Key:", self.ban_key_var)
        add_key_row(c3, "Unban Key:", self.unban_key_var)
        
        tk.Label(c3, text="Stop Key Action:", font=("Segoe UI", 9, "bold"), anchor="w", bg=t["panel"], fg=t["text"]).pack(fill="x", pady=(5,0))
        r_stop_act = tk.Frame(c3, bg=t["panel"]); r_stop_act.pack(fill="x")
        tk.Checkbutton(r_stop_act, text="Stop Typing", variable=self.stop_action_typing, bg=t["panel"], fg=t["text"], selectcolor=t["panel"], activebackground=t["panel"]).pack(side="left")
        tk.Checkbutton(r_stop_act, text="Disable Smart Input", variable=self.stop_action_smart, bg=t["panel"], fg=t["text"], selectcolor=t["panel"], activebackground=t["panel"]).pack(side="left")

        # --- TAB 3: HELP ---
        self.tab_help = tk.Frame(self.notebook, bg=t["bg"])
        self.notebook.add(self.tab_help, text=" HELP ")
        self.scroll_help = ScrollableFrame(self.tab_help, bg_color=t["bg"])
        self.scroll_help.configure_colors(t["bg"], t["sb_bg"], t["sb_trough"], t["sb_active"])
        self.scroll_help.pack(fill="both", expand=True)
        help_f = self.scroll_help.scrollable_frame
        
        def add_help_section(title, items):
            tk.Label(help_f, text=title, font=("Segoe UI", 12, "bold"), anchor="w", bg=t["bg"], fg=t["primary"]).pack(fill="x", padx=10, pady=(20, 5))
            for k, v in items.items():
                f = tk.Frame(help_f, pady=2, bg=t["bg"]); f.pack(fill="x", padx=15)
                tk.Label(f, text=f"• {k}:", font=("Segoe UI", 10, "bold"), anchor="nw", width=15, bg=t["bg"], fg=t["text"]).pack(side="left", anchor="n")
                tk.Label(f, text=v, font=("Segoe UI", 10), justify="left", anchor="w", wraplength=280, bg=t["bg"], fg=t["text"]).pack(side="left", fill="x")

        main_help = {"Active Window": "Select the game window to type into.",
            "Smart Input": "Captures your keystrokes to define the syllable, blocks them from game, then types full word.",
            "Input Field": "Manual entry box. Press Enter to search.",
            "Clr (Clear)": "Resets the current word and status.",
            "REROLL": "rejects current word, finds a new one, and auto-types it.",
            "STOP": "Immediately stops all typing and operations.",
            "History Tab": "Shows recent words. Use 'Ban' to block, 'Unban' to restore.",
            "Profiles Tab": "Save/Load different bot configurations."}
        
        config_help = {"Length": "Minimum and Maximum word length allowed.",
            "Strategy": "Algorithm to pick words (e.g., Killer uses hard letters).",
            "Priorities": "Order of strategies for 'Custom' mode (1st -> 2nd -> 3rd).",
            "Reroll Strat": "Specific strategies to use ONLY when rerolling.",
            "Latency": "Random delay range (ms) between each keystroke.",
            "Start Delay": "Wait time before typing a new word.",
            "Thinking Time": "Wait time specifically after a Reroll.",
            "Length Delay": "Extra wait time per character (Longer words = longer wait).",
            "Erase Speed": "Speed of backspacing (ms).",
            "Error Config": "Settings for intentional typos (Chance, Realization time, etc)."}
        
        toggle_help = {"Skip Input": "Bot assumes you typed the syllable and won't re-type it.",
            "Human Errors": "Enables/Disables simulated typos.",
            "Auto Type": "Type immediately when word is found.",
            "Auto Enter": "Press Enter after typing the word.",
            "Save DB": "Save valid words to local database for future use.",
            "Manual Step": "Use 'Step Key' to type one letter at a time.",
            "Ban Reroll": "Automatically reroll after banning a word."}
        
        keys_help = {
            "Step Key": "Types one character manually.",
            "Reroll Key": "Triggers Reroll function.",
            "Smart Input": "Toggles Smart Input mode.",
            "Stop Key": "Emergency stop.",
            "Ban/Unban": "Add/Remove current word from blacklist."}

        add_help_section("MAIN INTERFACE", main_help)
        add_help_section("CONFIGURATION", config_help)
        add_help_section("TOGGLES", toggle_help)
        add_help_section("HOTKEYS", keys_help)

    def create_list_controls(self, parent, listbox, type_tag):
        t = THEMES[self.current_theme]
        tk.Button(parent, text="Add", command=lambda: self.list_action(listbox, type_tag, "add"), 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(parent, text="Edit", command=lambda: self.list_action(listbox, type_tag, "edit"), 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(parent, text="Del", command=lambda: self.list_action(listbox, type_tag, "del"), 
                  bg=t["btn_bg"], fg=t["text"], width=6, relief="flat", font=("Segoe UI", 8)).pack(side="left", padx=2, expand=True, fill="x")

    def list_action(self, listbox, type_tag, action):
        sel_indices = listbox.curselection()
        if not sel_indices and action != "add": return
        
        selected_items = [listbox.get(i) for i in sel_indices]
        first_text = selected_items[0] if selected_items else None
        
        if action == "add":
            if type_tag == "pf": 
                self.add_profile()
                return
            self.open_bulk_add_dialog(type_tag)
                
        elif action == "edit":
            if not first_text: return
            if type_tag == "pf":
                self.rename_profile()
                return
            
            if len(selected_items) > 1:
                messagebox.showwarning("Edit", "Please select only one item to edit.")
                return

            val = simpledialog.askstring("Edit", f"Edit '{first_text}':", parent=self.root, initialvalue=first_text)
            if val and val != first_text:
                val = val.lower().strip()
                if type_tag == "bl":
                    self.dm.remove_blacklist(first_text)
                    self.dm.add_blacklist(val)
                elif type_tag == "db":
                    self.dm.remove_used(first_text)
                    self.dm.add_used(val)
                self.refresh_aux_lists()

        elif action == "del":
            if not selected_items: return
            msg = f"Delete '{first_text}'?" if len(selected_items) == 1 else f"Delete {len(selected_items)} items?"
            if messagebox.askyesno("Delete", msg):
                if type_tag == "pf":
                    for item in selected_items:
                          if item in self.dm.profiles: del self.dm.profiles[item]
                    self.dm.save_profile_data()
                elif type_tag == "bl":
                    for item in selected_items: self.dm.remove_blacklist(item)
                elif type_tag == "db":
                    for item in selected_items: self.dm.remove_used(item)
                self.refresh_aux_lists()

    def add_selected_to_db(self):
        sel = self.history_list.curselection()
        if not sel: return
        t = THEMES[self.current_theme]
        count = 0
        for i in sel:
            w = self.history_list.get(i)
            if w and w not in self.dm.used:
                self.dm.add_used(w)
                count += 1
        if count > 0:
            self.refresh_aux_lists()
            self.status_lbl.config(text=f"Added {count} to DB", fg=t["success"])
            
    def ban_selected_from_history(self):
        sel = self.history_list.curselection()
        if not sel: return
        count = 0
        for i in sel:
            w = self.history_list.get(i)
            if w and w not in self.dm.blacklist:
                self.dm.add_blacklist(w)
                self.dm.remove_used(w)
                if w == self.target_word:
                    self.target_word = ""
                    self.res_lbl.config(text="BANNED", fg=THEMES[self.current_theme]["err"])
                count += 1
        if count > 0:
            self.refresh_aux_lists()
            self.status_lbl.config(text=f"Banned {count} words", fg=THEMES[self.current_theme]["err"])

    def unban_selected_from_history(self):
        sel = self.history_list.curselection()
        if not sel: return
        count = 0
        for i in sel:
            w = self.history_list.get(i)
            if w and w in self.dm.blacklist:
                self.dm.remove_blacklist(w)
                # Removed adding back to DB as requested
                count += 1
        if count > 0:
            self.refresh_aux_lists()
            self.status_lbl.config(text=f"Unbanned {count} words", fg=THEMES[self.current_theme]["success"])
                
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the history?"):
            self.history_list.delete(0, tk.END)
            self.dm.save_history([])
            self.status_lbl.config(text="History Cleared", fg=THEMES[self.current_theme]["warn"])
        
    def open_bulk_add_dialog(self, type_tag):
        t = THEMES[self.current_theme]
        top = Toplevel(self.root)
        top.title("Bulk Add")
        # Increased size and logic for layout
        top.geometry("300x500") 
        top.configure(bg=t["bg"])
        top.attributes('-topmost', True)
        
        tk.Label(top, text="Enter words (separate by new line):", bg=t["bg"], fg=t["text"]).pack(pady=5)
        
        # --- FIX: Pack Button FIRST at the bottom so it's always visible
        def do_import():
            raw = txt_input.get("1.0", tk.END)
            lines = raw.replace(',', '\n').splitlines()
            count = 0
            for line in lines:
                w = line.strip().lower()
                if w:
                    if type_tag == "bl": self.dm.add_blacklist(w)
                    elif type_tag == "db": self.dm.add_used(w)
                    count += 1
            self.refresh_aux_lists()
            top.destroy()
            self.status_lbl.config(text=f"Added {count} items", fg=t["success"])

        tk.Button(top, text="Import", command=do_import, bg=t["primary"], fg="white", relief="flat", font=("Segoe UI", 10, "bold")).pack(side="bottom", fill="x", padx=10, pady=10)

        txt_frame = tk.Frame(top, bg=t["bg"])
        txt_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        
        txt_input = tk.Text(txt_frame, font=("Consolas", 10), bg=t["input_bg"], fg=t["text"], bd=0)
        txt_input.pack(side="left", fill="both", expand=True)

    def toggle_theme(self):
        self.current_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.dm.window_cfg["theme"] = self.current_theme
        self.apply_theme()

    def apply_theme(self):
        t = THEMES[self.current_theme]
        self.root.configure(bg=t["bg"])
        self.top_bar.configure(bg=t["bg"])
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=t["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=t["panel"], foreground=t["text"], borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", t["primary"])], foreground=[("selected", "white")])
        
        def recursive_bg(widget, bg_col, fg_col=None):
            try: 
                if isinstance(widget, (tk.Frame, ScrollableFrame)): widget.configure(bg=bg_col)
                elif isinstance(widget, (tk.Label, tk.Checkbutton)): 
                    widget.configure(bg=bg_col, fg=fg_col)
                    if isinstance(widget, tk.Checkbutton): widget.configure(selectcolor=bg_col, activebackground=bg_col)
                elif isinstance(widget, tk.Entry): 
                    widget.configure(bg=t["input_bg"], fg=t["text"], insertbackground=t["text"], readonlybackground=t["input_bg"])
                elif isinstance(widget, tk.Listbox): widget.configure(bg=t["panel"], fg=t["text"])
                elif isinstance(widget, tk.Button):
                    if widget not in [self.btn_reroll, self.btn_stop, self.btn_smart]:
                        widget.configure(bg=t["btn_bg"], fg=t["text"])

            except: pass
            for child in widget.winfo_children():
                recursive_bg(child, bg_col, fg_col)

        recursive_bg(self.tab_gen, t["bg"], t["text"])
        recursive_bg(self.tab_help, t["bg"], t["text"])
        self.scroll_set.configure_colors(t["bg"], t["sb_bg"], t["sb_trough"], t["sb_active"])
        self.scroll_help.configure_colors(t["bg"], t["sb_bg"], t["sb_trough"], t["sb_active"])
        
        self.title_lbl.configure(fg=t["primary"])
        self.entry.configure(bg=t["input_bg"], fg=t["primary"])
        self.vis_text.configure(bg=t["input_bg"], fg=t["text"])
        self.vis_text.tag_config("wrong", foreground=t["err"])
        self.vis_text.tag_config("remain", foreground=t["text"])
        self.res_lbl.configure(bg=t["bg"], fg=t["text_dim"])
        self.btn_clear.configure(bg=t["btn_bg"], fg=t["text"])
        
        self.btn_smart.configure(bg=t["btn_bg"] if not self.smart_input_active else t["primary"], fg=t["text"] if not self.smart_input_active else "#FFF")
        for btn in [self.btn_reroll, self.btn_stop, self.btn_clear]:
            btn.configure(bg=t["btn_bg"], fg=t["text"])
        self.btn_reroll.configure(bg=t["warn"], fg="#000")
        self.btn_stop.configure(bg=t["err"], fg="#FFF")
        
        for child in self.set_frame.winfo_children():
            if isinstance(child, tk.Frame) and child.winfo_width() > 1: 
                child.configure(bg=t["panel"])
                recursive_bg(child, t["panel"], t["text"])
            elif isinstance(child, tk.Label): 
                child.configure(bg=t["bg"], fg=t["primary"])

    def clear_visuals(self):
        self.target_word = ""
        self.typed_history = ""
        self.entry_var.set("")
        self.res_lbl.config(text="READY", fg=THEMES[self.current_theme]["text_dim"])
        self.update_vis_ui()
        # Ensure Step Key is unhooked when cleared
        self.unhook_step_key()

    def refresh_aux_lists(self):
        self.blacklist_list.delete(0, tk.END)
        for w in reversed(self.dm.blacklist):
            self.blacklist_list.insert(tk.END, w)
        self.db_list.delete(0, tk.END)
        for w in reversed(self.dm.used):
             self.db_list.insert(tk.END, w)
        self.profiles_list_tab.delete(0, tk.END)
        for p in reversed(list(self.dm.profiles.keys())):
            self.profiles_list_tab.insert(tk.END, p)
        self.refresh_history_colors()

    def refresh_history_colors(self):
        t = THEMES[self.current_theme]
        sz = self.history_list.size()
        for i in range(sz):
            w = self.history_list.get(i)
            if w in self.dm.blacklist:
                self.history_list.itemconfig(i, {'fg': t["err"]})
            elif w in self.dm.used:
                self.history_list.itemconfig(i, {'fg': t["success"]})
            else:
                self.history_list.itemconfig(i, {'fg': t["text"]})

    def load_profile_from_tab(self, event):
        sel = self.profiles_list_tab.curselection()
        if sel:
            name = self.profiles_list_tab.get(sel[0])
            self.profile_var.set(name)
            self.load_profile(None)
            self.status_lbl.config(text=f"Loaded {name}", fg=THEMES[self.current_theme]["success"])

    def enable_smart_input(self):
        if self.smart_input_active: return
        self.toggle_smart_input()

    def toggle_smart_input(self):
        self.smart_input_active = not self.smart_input_active
        t = THEMES[self.current_theme]
        
        if self.smart_input_active:
            self.btn_smart.configure(bg=t["primary"], fg="#FFF")
            self.entry_var.set("")
            self.status_lbl.config(text="Listening...", fg=t["warn"])
            
            for char in string.ascii_lowercase + string.digits:
                self.smart_hooks.append(keyboard.on_press_key(char, self.on_smart_key, suppress=True))
            self.smart_hooks.append(keyboard.on_press_key("backspace", self.on_smart_key, suppress=False))
            self.smart_hooks.append(keyboard.on_press_key("enter", self.on_smart_key, suppress=True))
            self.smart_hooks.append(keyboard.on_press_key("esc", self.on_smart_key, suppress=False))
        else:
            self.disable_smart_input()

    def disable_smart_input(self):
        self.smart_input_active = False
        t = THEMES[self.current_theme]
        self.btn_smart.configure(bg=t["btn_bg"], fg=t["text"])
        self.status_lbl.config(text="Ready", fg=t["text"])
        
        for hook in self.smart_hooks:
            try: keyboard.unhook(hook)
            except: pass
        self.smart_hooks.clear()

    def on_smart_key(self, event):
        if not self.smart_input_active: return
        key = event.name.lower()
        if key == "enter":
            self.gui_queue.put((self.finish_smart_input, []))
        elif key == "esc":
            pass 
        elif key == "backspace":
            cur = self.entry_var.get()
            self.entry_var.set(cur[:-1])
        elif len(key) == 1:
            self.entry_var.set(self.entry_var.get() + key)

    def finish_smart_input(self):
        self.was_smart_active = True 
        self.disable_smart_input()
        word = self.entry_var.get()
        self.entry_var.set("") 
        if word: self.process_word(word)
        else: self.enable_smart_input()

    def refresh_window_list(self):
        try:
            titles = [w.title for w in gw.getAllWindows() if w.title]
            current = self.win_list_var.get()
            self.win_cb['values'] = ["Active Window"] + sorted(titles)
            if current not in self.win_cb['values']: self.win_cb.current(0)
        except: pass

    def on_key_event(self, event):
        if event.event_type != 'down': return
        if self.is_typing_active: return # Ignore keys while bot is typing to prevent double-counting
        if not self.target_word: return
        key = event.name.lower()
        if key == 'backspace':
            if len(self.typed_history) > 0:
                self.typed_history = self.typed_history[:-1]
                self.gui_queue.put((self.update_vis_ui, []))
            return
        if len(key) > 1: return
        self.typed_history += key
        self.gui_queue.put((self.update_vis_ui, []))

    def update_vis_ui(self):
        self.vis_text.configure(state="normal")
        self.vis_text.delete("1.0", tk.END)
        if not self.target_word:
            self.vis_text.insert("1.0", "Waiting for input...")
            self.vis_text.configure(state="disabled")
            return

        correct_len = 0
        min_len = min(len(self.typed_history), len(self.target_word))
        for i in range(min_len):
            if self.typed_history[i] == self.target_word[i]: correct_len += 1
            else: break
        
        if correct_len > 0: self.vis_text.insert(tk.END, self.target_word[:correct_len], "correct")
        if len(self.typed_history) > correct_len: self.vis_text.insert(tk.END, self.typed_history[correct_len:], "wrong")
        
        remaining_idx = correct_len + max(0, len(self.typed_history) - correct_len)
        if remaining_idx < len(self.target_word): self.vis_text.insert(tk.END, self.target_word[remaining_idx:], "remain")
        self.vis_text.configure(state="disabled")

    def process_word(self, letters, reroll=False):
        # Normalize letters immediately to match WordGenerator logic and prevent partial matches
        letters = "".join(filter(str.isalpha, letters)).lower()

        # Increment generation to invalidate any previous typing threads immediately
        self.typing_gen += 1
        
        # FIX: Disable Smart Input if Auto Type is on to prevent hooks from catching bot output
        if self.smart_input_active and self.auto_type_var.get():
            self.was_smart_active = True
            self.disable_smart_input()

        self.last_input = letters
        self.status_lbl.config(text="Searching...", fg=THEMES[self.current_theme]["warn"])
        self.root.update()
        
        # Smart Erase Logic: Calculate if we can keep the prefix
        if reroll and self.typed_history:
            prefix_to_keep = ""
            # Only keep prefix if Skip Input is ON and the history actually matches current input
            if self.skip_var.get() and letters and self.typed_history.startswith(letters):
                prefix_to_keep = letters
            self.erase_current_word(prefix_to_keep)

        # DETERMINING PRIORITIES:
        # If reroll, check if specific reroll strategy is set.
        current_priorities = [self.p1_var.get(), self.p2_var.get(), self.p3_var.get()]
        if reroll:
            # If a reroll priority is NOT "Same Mode", use it. Otherwise fall back to main.
            rp1 = self.rr_p1_var.get()
            rp2 = self.rr_p2_var.get()
            rp3 = self.rr_p3_var.get()
            
            if rp1 != "Same Mode": current_priorities[0] = rp1
            if rp2 != "Same Mode": current_priorities[1] = rp2
            if rp3 != "Same Mode": current_priorities[2] = rp3

        word, is_new = self.gen.get_word(letters, self.len_min_var.get(), self.len_max_var.get(), self.strat_var.get(), current_priorities, current_target=self.target_word, reroll=reroll)
        
        if word:
            self.dm.session_used.add(word) 
            self.target_word = word
            
            # Decide what part of the word is "already typed" based on Skip setting
            self.typed_history = ""
            start_index = 0
            
            # STRICT START CHECK: Only skip if enabled AND word starts with letters
            if self.skip_var.get() and letters and word.startswith(letters): 
                self.typed_history = letters
                start_index = len(letters)
            
            was_in_db = word in self.dm.used
            if not was_in_db and self.save_db_var.get():
                self.dm.add_used(word)
                self.db_list.insert(0, word) 
            
            self.history_list.insert(0, word)
            self.refresh_history_colors()

            if self.history_list.size() > 50: self.history_list.delete(50, tk.END)
            
            self.res_lbl.config(text=word.upper(), fg=THEMES[self.current_theme]["primary"])
            if not self.smart_input_active:
                self.entry_var.set("")
            self.update_vis_ui()
            if self.sound_var.get(): winsound.Beep(800, 50)
            
            self.hook_step_key()

            if self.auto_type_var.get():
                self.is_typing_active = True
                self.stop_flag = False
                threading.Thread(target=self.type_thread, args=(word, self.typing_gen, start_index, reroll)).start()
            else:
                if self.was_smart_active:
                    self.enable_smart_input()
        else:
            self.res_lbl.config(text="NO WORDS", fg=THEMES[self.current_theme]["err"])
            if self.was_smart_active:
                self.enable_smart_input()

    def erase_current_word(self, prefix_to_keep=""):
        count = len(self.typed_history)
        keep_len = len(prefix_to_keep)
        
        if count == 0: return
        
        self.focus_target()
        try: 
            es_min = float(self.erase_speed_min_var.get()) / 1000.0
            es_max = float(self.erase_speed_max_var.get()) / 1000.0
        except: 
            es_min = 0.02; es_max = 0.05
            
        # Only erase characters that are NOT part of the preserved prefix
        to_erase = max(0, count - keep_len)
        
        for _ in range(to_erase): 
            pydirectinput.press('backspace')
            time.sleep(random.uniform(es_min, es_max))
            
        # Manually set history to prefix so visual UI stays synced
        self.typed_history = prefix_to_keep
        self.gui_queue.put((self.update_vis_ui, []))

    def focus_target(self):
        target = self.win_list_var.get()
        if target == "Active Window": return True
        try:
            wins = gw.getWindowsWithTitle(target)
            if wins:
                w = wins[0]
                if not w.isActive: w.activate(); time.sleep(0.1)
                return True
        except: pass
        return False

    def _press(self, key):
        # Humanize hold time: 15ms to 40ms to simulate real finger press
        hold = random.uniform(0.015, 0.04)
        pydirectinput.keyDown(key)
        time.sleep(hold)
        pydirectinput.keyUp(key)

    def type_thread(self, word, my_gen, start_index, is_reroll=False):
        try:
            try:
                # Base Delay
                if is_reroll:
                    d_min = int(self.reroll_delay_min_var.get()) / 1000.0
                    d_max = int(self.reroll_delay_max_var.get()) / 1000.0
                else:
                    d_min = int(self.start_delay_min_var.get()) / 1000.0
                    d_max = int(self.start_delay_max_var.get()) / 1000.0
                
                base_delay = random.uniform(d_min, d_max)

                # Length Delay
                ld_min = int(self.len_delay_min_var.get()) / 1000.0
                ld_max = int(self.len_delay_max_var.get()) / 1000.0
                len_delay = random.uniform(ld_min, ld_max) * len(word)

                time.sleep(base_delay + len_delay)
            except:
                time.sleep(0.3)
                
            self.focus_target()
            
            try:
                l_min = float(self.lat_min_var.get()) / 1000.0
                l_max = float(self.lat_max_var.get()) / 1000.0
                rl_min = float(self.realization_min_var.get()) / 1000.0
                rl_max = float(self.realization_max_var.get()) / 1000.0
                es_min = float(self.erase_speed_min_var.get()) / 1000.0
                es_max = float(self.erase_speed_max_var.get()) / 1000.0
                ed_min = int(self.err_delay_min_var.get())
                ed_max = int(self.err_delay_max_var.get())
                
                err_mode = self.error_mode_var.get()
                err_chance = float(self.err_chance_val.get()) / 100.0
                err_int_a = int(self.err_int_min.get())
                err_int_b = int(self.err_int_max.get())
                
                next_error_at = random.randint(err_int_a, err_int_b) if err_mode == "Interval" else 9999
                chars_since_err = 0
            except: 
                l_min=0.05; l_max=0.15; rl_min=0.2; rl_max=0.4
                es_min=0.02; es_max=0.05; ed_min=1; ed_max=3
                err_mode="Chance"; err_chance=0.04; next_error_at=9999
            
            # Start typing from the index determined by Skip Input logic
            i = start_index
            error_pending = False
            error_idx = -1
            notice_idx = -1
            
            # FIXED LOOP CONDITION: Keep going if error is pending (even at end of word)
            while i < len(word) or error_pending:
                # Stop if flag set OR if this thread is from an old generation
                if self.stop_flag or self.typing_gen != my_gen: break
                
                # --- ERROR TRIGGER CHECK ---
                should_err = False
                if not error_pending and self.human_var.get():
                    if i < len(word):
                        if err_mode == "Chance":
                            if random.random() < err_chance: should_err = True
                        else: # Interval
                            if chars_since_err >= next_error_at: should_err = True

                if should_err:
                    error_pending = True
                    error_idx = i
                    delay = random.randint(ed_min, ed_max)
                    notice_idx = i + delay
                    
                    char_to_type = random.choice(KEY_NEIGHBORS.get(word[i], 'a')) if i < len(word) else 'a'
                    self._press(char_to_type)
                    
                    i += 1
                    time.sleep(random.uniform(l_min, l_max))
                    continue

                if error_pending:
                    # FIX: Notice if we hit delay OR we typed past word length
                    if i >= notice_idx or i >= len(word):
                        time.sleep(random.uniform(rl_min, rl_max)) 
                        
                        backspaces = i - error_idx
                        for _ in range(backspaces):
                            pydirectinput.press('backspace')
                            time.sleep(random.uniform(es_min, es_max))
                        
                        i = error_idx
                        error_pending = False
                        
                        chars_since_err = 0
                        if err_mode == "Interval":
                            next_error_at = random.randint(err_int_a, err_int_b)
                            
                        time.sleep(0.1)
                        continue 
                    else:
                        if i < len(word):
                            char = word[i]
                            self._press(char)
                        else:
                            self._press(random.choice('abcdefghijklmnopqrstuvwxyz'))
                            
                        time.sleep(random.uniform(l_min, l_max))
                        i += 1
                        continue

                # Standard Typing
                # FIX: Break if loop condition was met by "i < len" but we have no error
                if i >= len(word): break
                
                char = word[i]
                self._press(char)
                
                # Manually update history to ensure erase logic works even if hooks fail
                self.typed_history += char
                
                chars_since_err += 1
                # Latency: Sleep random amount between min and max
                time.sleep(random.uniform(l_min, l_max))
                i += 1
                
            if self.auto_enter_var.get() and not self.stop_flag and self.typing_gen == my_gen: self._press('enter')
            if self.typing_gen == my_gen:
                self.gui_queue.put((self.status_lbl.config, [], {"text": "Done", "fg": THEMES[self.current_theme]["success"]}))
        except Exception as e: print(f"Type Thread Error: {e}")
        finally:
            # Only reset active status if we are the current thread
            if self.typing_gen == my_gen:
                self.is_typing_active = False 
                if self.was_smart_active:
                    self.gui_queue.put((self.enable_smart_input, []))
            pass

    def step_type(self, event=None):
        if not self.manual_step_var.get(): return
        if not self.target_word: return

        current_len = len(self.typed_history)
        
        if not self.target_word.startswith(self.typed_history):
            if self.focus_target(): 
                pydirectinput.press('backspace')
            return

        if current_len < len(self.target_word):
            if self.focus_target():
                char_to_type = self.target_word[current_len]
                self._press(char_to_type)

    def on_tab_changed(self, event):
        try:
            current = self.notebook.index("current")
            if current != 0: 
                if self.smart_input_active:
                    self.disable_smart_input()
        except: pass

        geo = self.root.geometry()
        try:
            s_str = geo.split('+')[0]
            w, h = map(int, s_str.split('x'))
            if w > 200 and h > 200:
                p_str = "+" + geo.split('+', 1)[1] if '+' in geo else ""
                self.dm.window_cfg[str(self.current_tab)] = s_str
                self.dm.window_cfg["position"] = p_str
        except: pass
        
        self.current_tab = self.notebook.index("current")
        self.dm.window_cfg["last_tab"] = self.current_tab
        new_size = self.dm.window_cfg.get(str(self.current_tab), "450x650")
        
        try:
            nw, nh = map(int, new_size.split('x'))
            if nw < 200 or nh < 200: new_size = "450x650"
        except: new_size = "450x650"

        if self.dm.window_cfg.get("position"): self.root.geometry(f"{new_size}{self.dm.window_cfg['position']}")
        else: self.root.geometry(new_size)

    def on_close(self):
        # Save History
        current_hist = self.history_list.get(0, tk.END)
        self.dm.save_history(list(current_hist))

        # Save Current Settings
        self.dm.save_last_settings(self.get_settings())

        if self.root.state() == 'iconic':
            self.dm.save_win_data()
            try: keyboard.unhook_all()
            except: pass
            self.root.destroy()
            return

        geo = self.root.geometry()
        try:
            s = geo.split("+")[0]
            w, h = map(int, s.split("x"))
            if w > 200 and h > 200:
                p = "+" + geo.split("+", 1)[1] if "+" in geo else ""
                self.dm.window_cfg[str(self.current_tab)] = s
                if p: self.dm.window_cfg["position"] = p
        except: pass
        
        self.dm.save_win_data()
        try: keyboard.unhook_all()
        except: pass
        self.root.destroy()

    def reroll(self):
        if self.processing_action: return
        self.processing_action = True
        try:
            self.process_word(self.last_input, reroll=True)
        finally:
            self.root.after(300, lambda: setattr(self, 'processing_action', False))
    
    def ban_last(self):
        if self.processing_action: return
        self.processing_action = True
        try:
            if self.target_word: 
                self.dm.add_blacklist(self.target_word)
                self.dm.remove_used(self.target_word)
                self.refresh_aux_lists()
                self.was_smart_active = False
                if self.ban_reroll_var.get():
                    self.process_word(self.last_input, reroll=True)
        finally:
            self.root.after(500, lambda: setattr(self, 'processing_action', False))

    def unban_last_hotkey(self):
        if self.processing_action: return
        self.processing_action = True
        try:
            if self.target_word and self.target_word in self.dm.blacklist:
                self.dm.remove_blacklist(self.target_word)
                # Removed adding back to used/db for hotkey too
                self.refresh_aux_lists()
                self.status_lbl.config(text="Unbanned", fg=THEMES[self.current_theme]["success"])
        finally:
            self.root.after(300, lambda: setattr(self, 'processing_action', False))

    def toggle_smart_hotkey(self):
        if self.processing_action: return
        self.processing_action = True
        self.toggle_smart_input()
        self.root.after(300, lambda: setattr(self, 'processing_action', False))
            
    def stop_typing(self): 
        if self.stop_action_smart.get():
            self.was_smart_active = False 
            self.gui_queue.put((self.disable_smart_input, []))
        
        if self.stop_action_typing.get():
            self.stop_flag = True
        
        self.unhook_step_key()
            
    def on_enter(self, e): 
        self.root.focus_set()
        self.was_smart_active = False 
        if self.smart_input_active: self.disable_smart_input()
        self.process_word(self.entry_var.get())
        
    def on_focus_in(self, e): 
        self.unhook_step_key()
    def on_focus_out(self, e): self.root.after(100, self.update_binds)
    
    def start_key_bind(self, var):
        self.root.focus()
        var.set("Press...")
        self.root.update()
        def wait_for_key():
            event = keyboard.read_event()
            while event.event_type != 'down': event = keyboard.read_event()
            self.gui_queue.put((self.finish_bind, [var, event.name.lower()]))
        threading.Thread(target=wait_for_key, daemon=True).start()

    def finish_bind(self, var, key_name):
        var.set(key_name)
        self.update_binds()
        
    def update_binds(self):
        try: 
            keyboard.unhook_key(self.reroll_key)
            keyboard.unhook_key(self.smart_key)
            keyboard.unhook_key(self.stop_key)
            keyboard.unhook_key(self.ban_key)
            keyboard.unhook_key(self.unban_key)
        except: pass
        
        self.step_key = self.step_key_var.get().lower()
        self.reroll_key = self.reroll_key_var.get().lower()
        self.smart_key = self.smart_key_var.get().lower()
        self.stop_key = self.stop_key_var.get().lower()
        self.ban_key = self.ban_key_var.get().lower()
        self.unban_key = self.unban_key_var.get().lower()
        
        try:
            if self.reroll_key: keyboard.add_hotkey(self.reroll_key, self.reroll)
            if self.smart_key: keyboard.add_hotkey(self.smart_key, self.toggle_smart_hotkey)
            if self.stop_key: keyboard.add_hotkey(self.stop_key, self.stop_typing)
            if self.ban_key: keyboard.add_hotkey(self.ban_key, self.ban_last)
            if self.unban_key: keyboard.add_hotkey(self.unban_key, self.unban_last_hotkey)
        except: pass

        if self.active_step_hook and self.target_word:
            self.unhook_step_key()
            self.hook_step_key()
        else:
            self.unhook_step_key()

    def hook_step_key(self):
        if not self.manual_step_var.get(): return
        if not self.step_key: return
        if self.active_step_hook: return 

        try:
            self.active_step_hook = keyboard.add_hotkey(self.step_key, self.step_type, suppress=True)
        except: pass

    def unhook_step_key(self):
        if self.active_step_hook:
            try: keyboard.remove_hotkey(self.active_step_hook)
            except: pass
            self.active_step_hook = None
        try: keyboard.unhook_key(self.step_key)
        except: pass

    def rename_profile(self):
        current = self.profile_var.get()
        if not current: return
        new_name = simpledialog.askstring("Rename", f"Rename '{current}' to:", parent=self.root)
        if new_name and new_name != current:
            self.dm.profiles[new_name] = self.dm.profiles[current]
            del self.dm.profiles[current]
            self.dm.save_profile_data()
            self.refresh_profile_list()
            self.profile_var.set(new_name)

    def load_profile(self, e):
        name = self.profile_var.get()
        if name in self.dm.profiles:
            self.apply_dict_settings(self.dm.profiles[name])
            self.status_lbl.config(text=f"Loaded {name}", fg=THEMES[self.current_theme]["success"])

    def apply_dict_settings(self, p):
        # Helper to safely load dictionary settings into vars
        # ADDED: Logic for saving Toggles (Skip, Auto Type, etc)
        self.human_var.set(p.get("human", True))
        
        # New persistent variables
        self.skip_var.set(p.get("skip", True))
        self.auto_type_var.set(p.get("atype", True))
        self.auto_enter_var.set(p.get("aenter", True))
        self.save_db_var.set(p.get("savedb", False))
        self.manual_step_var.set(p.get("mstep", True))
        
        self.len_min_var.set(p.get("min", 1))
        self.len_max_var.set(p.get("max", 30))
        self.strat_var.set(p.get("strat", "Random"))
        self.lat_min_var.set(p.get("lm", "50"))
        self.lat_max_var.set(p.get("lx", "150"))
        
        self.start_delay_min_var.set(p.get("sd_min", "250"))
        self.start_delay_max_var.set(p.get("sd_max", "400"))
        self.reroll_delay_min_var.set(p.get("rd_min", "500"))
        self.reroll_delay_max_var.set(p.get("rd_max", "800"))
        self.len_delay_min_var.set(p.get("ld_min", "10"))
        self.len_delay_max_var.set(p.get("ld_max", "30"))
        self.erase_speed_min_var.set(p.get("es_min", "20"))
        self.erase_speed_max_var.set(p.get("es_max", "50"))
        self.realization_min_var.set(p.get("rl_min", "150"))
        self.realization_max_var.set(p.get("rl_max", "400"))
        self.err_delay_min_var.set(p.get("edm", "1"))
        self.err_delay_max_var.set(p.get("edx", "3"))
        
        self.error_mode_var.set(p.get("erm", "Interval"))
        self.err_chance_val.set(p.get("erc", "4"))
        self.err_int_min.set(p.get("eim", "15"))
        self.err_int_max.set(p.get("eix", "30"))
        
        self.p1_var.set(p.get("p1", "Long & Killer"))
        self.p2_var.set(p.get("p2", "Longest"))
        self.p3_var.set(p.get("p3", "Killer"))

        self.rr_p1_var.set(p.get("rr_p1", "Same Mode"))
        self.rr_p2_var.set(p.get("rr_p2", "Same Mode"))
        self.rr_p3_var.set(p.get("rr_p3", "Same Mode"))

        self.step_key_var.set(p.get("sk", "z"))
        self.reroll_key_var.set(p.get("rk", "f4"))
        self.smart_key_var.set(p.get("smk", "f2"))
        self.stop_key_var.set(p.get("stk", "esc"))
        self.ban_key_var.set(p.get("bnk", ""))
        self.unban_key_var.set(p.get("ubk", ""))
        self.stop_action_typing.set(p.get("sat", True))
        self.stop_action_smart.set(p.get("sas", False))
        self.ban_reroll_var.set(p.get("brr", True)) 
        self.update_binds()

    def get_settings(self):
        return {
            "human": self.human_var.get(), 
            
            # ADDED: Persistence for Checkboxes
            "skip": self.skip_var.get(),
            "atype": self.auto_type_var.get(),
            "aenter": self.auto_enter_var.get(),
            "savedb": self.save_db_var.get(),
            "mstep": self.manual_step_var.get(),
            
            "min": self.len_min_var.get(), "max": self.len_max_var.get(),
            "strat": self.strat_var.get(), "lm": self.lat_min_var.get(), "lx": self.lat_max_var.get(),
            "sd_min": self.start_delay_min_var.get(), "sd_max": self.start_delay_max_var.get(),
            "rd_min": self.reroll_delay_min_var.get(), "rd_max": self.reroll_delay_max_var.get(),
            "ld_min": self.len_delay_min_var.get(), "ld_max": self.len_delay_max_var.get(),
            "es_min": self.erase_speed_min_var.get(), "es_max": self.erase_speed_max_var.get(),
            "rl_min": self.realization_min_var.get(), "rl_max": self.realization_max_var.get(),
            "edm": self.err_delay_min_var.get(), "edx": self.err_delay_max_var.get(),
            
            "erm": self.error_mode_var.get(), "erc": self.err_chance_val.get(),
            "eim": self.err_int_min.get(), "eix": self.err_int_max.get(),
            
            "p1": self.p1_var.get(), "p2": self.p2_var.get(), "p3": self.p3_var.get(),
            
            "rr_p1": self.rr_p1_var.get(), "rr_p2": self.rr_p2_var.get(), "rr_p3": self.rr_p3_var.get(),

            "sk": self.step_key_var.get(), "rk": self.reroll_key_var.get(),
            "smk": self.smart_key_var.get(), "stk": self.stop_key_var.get(), "bnk": self.ban_key_var.get(), "ubk": self.unban_key_var.get(),
            "sat": self.stop_action_typing.get(), "sas": self.stop_action_smart.get(),
            "brr": self.ban_reroll_var.get() 
        }
    def add_profile(self):
        n = simpledialog.askstring("Profile", "Name:", parent=self.root)
        if n: 
            self.dm.profiles[n] = self.get_settings()
            self.dm.save_profile_data()
            self.refresh_profile_list()
            self.profile_var.set(n)
            
    def save_profile(self):
        n = self.profile_var.get()
        if n: 
            if messagebox.askyesno("Save Profile", f"Overwrite profile '{n}' with current settings?"):
                self.dm.profiles[n] = self.get_settings()
                self.dm.save_profile_data()
                self.status_lbl.config(text="Saved", fg=THEMES[self.current_theme]["success"])
        else:
             messagebox.showwarning("Save Profile", "No profile selected/loaded.")

    def delete_profile(self):
        n = self.profile_var.get()
        if n and messagebox.askyesno("Delete", f"Delete {n}?"): 
            del self.dm.profiles[n]
            self.dm.save_profile_data()
            self.refresh_profile_list()
            
    def refresh_profile_list(self): 
        self.refresh_aux_lists()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = BotGUI(root)
        root.mainloop()
    except Exception as e:
        input(f"CRASH: {e}\n{traceback.format_exc()}")
