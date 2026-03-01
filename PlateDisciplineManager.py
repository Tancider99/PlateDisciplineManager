import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from plate_discipline import PlateDisciplineCalculator

class LineupEditor(ttk.Frame):
    def __init__(self, parent, calculator, team_entry=None, pitcher_entry=None):
        super().__init__(parent)
        self.calculator = calculator
        self.team_entry = team_entry
        self.pitcher_entry = pitcher_entry
        self.players = []
        
        # Controls
        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", pady=2)
        
        self.add_var = tk.StringVar()
        # Simple entry for now, or Combobox if we had a large list
        self.entry = ttk.Entry(ctrl, textvariable=self.add_var)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda e: self.add_player())
        
        ttk.Button(ctrl, text="+", width=3, command=self.add_player).pack(side="left", padx=2)
        
        # List
        list_f = ttk.Frame(self)
        list_f.pack(fill="both", expand=True)
        
        self.listbox = tk.Listbox(list_f, height=10)
        self.listbox.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(list_f, orient="vertical", command=self.listbox.yview)
        sb.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=sb.set)
        
        # List Buttons
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=2)
        
        ttk.Button(btns, text="Up", command=self.move_up).pack(side="left", expand=True)
        ttk.Button(btns, text="Down", command=self.move_down).pack(side="left", expand=True)
        ttk.Button(btns, text="Del", command=self.remove_player).pack(side="left", expand=True)
        
        # Persistence
        persist = ttk.Frame(self)
        persist.pack(fill="x", pady=5)
        ttk.Button(persist, text="Save", command=self.save_preset).pack(side="left", expand=True)
        ttk.Button(persist, text="Load", command=self.load_preset).pack(side="left", expand=True)
        
        # Count label
        self.count_lbl = ttk.Label(self, text="Count: 0/9", font=("Segoe UI", 9))
        self.count_lbl.pack(anchor="e")

    def refresh_list(self):
        self.listbox.delete(0, "end")
        for p in self.players:
            self.listbox.insert("end", p)
        
        c = len(self.players)
        self.count_lbl.config(text=f"Count: {c}/9", foreground="red" if c != 9 else "green")

    def add_player(self):
        name = self.add_var.get().strip()
        if name:
            self.players.append(name)
            self.add_var.set("")
            self.refresh_list()
            self.entry.focus()

    def remove_player(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            del self.players[idx]
            self.refresh_list()

    def move_up(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            if idx > 0:
                self.players[idx], self.players[idx-1] = self.players[idx-1], self.players[idx]
                self.refresh_list()
                self.listbox.selection_set(idx-1)

    def move_down(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            if idx < len(self.players) - 1:
                self.players[idx], self.players[idx+1] = self.players[idx+1], self.players[idx]
                self.refresh_list()
                self.listbox.selection_set(idx+1)
    
    def save_preset(self):
        if not self.players: return
        
        # Get Team/Pitcher if available
        t_val = self.team_entry.get() if self.team_entry else ""
        p_val = self.pitcher_entry.get() if self.pitcher_entry else ""
        
        name = simpledialog.askstring("Save Lineup", "Enter name for this lineup:")
        if name:
            self.calculator.save_lineup(name, self.players, t_val, p_val)
            messagebox.showinfo("Saved", f"Lineup '{name}' saved.")

    def load_preset(self):
        saved = self.calculator.get_saved_lineups()
        if not saved:
            messagebox.showinfo("Info", "No saved lineups found.")
            return
            
        names = list(saved.keys())
        
        # Custom Dialog for selection
        dialog = tk.Toplevel(self)
        dialog.title("Load Lineup")
        dialog.geometry("300x400")
        
        ttk.Label(dialog, text="Select a lineup to load:").pack(pady=5)
        
        frame_list = ttk.Frame(dialog)
        frame_list.pack(fill="both", expand=True, padx=10)
        
        lb = tk.Listbox(frame_list)
        lb.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(frame_list, orient="vertical", command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.config(yscrollcommand=sb.set)

        for n in names:
            lb.insert("end", n)
            
        def select():
            sel = lb.curselection()
            if sel:
                name = lb.get(sel[0])
                data = saved[name]
                
                # Handle old format (list) vs new format (dict)
                if isinstance(data, list):
                    self.players = list(data)
                elif isinstance(data, dict):
                    self.players = list(data["players"])
                    if self.team_entry: 
                        self.team_entry.delete(0, "end")
                        self.team_entry.insert(0, data.get("team", ""))
                    if self.pitcher_entry:
                        self.pitcher_entry.delete(0, "end")
                        self.pitcher_entry.insert(0, data.get("pitcher", ""))
                
                self.refresh_list()
                dialog.destroy()
                
        def delete_selected():
            sel = lb.curselection()
            if not sel: return
            name = lb.get(sel[0])
            if messagebox.askyesno("Confirm Delete", f"Delete lineup '{name}'?"):
                self.calculator.delete_lineup(name)
                lb.delete(sel[0])
                # Remove from local list to avoid re-selecting
                
        btn_f = ttk.Frame(dialog)
        btn_f.pack(fill="x", pady=10)
        
        ttk.Button(btn_f, text="Load", command=select).pack(side="left", expand=True, padx=5)
        ttk.Button(btn_f, text="Delete", command=delete_selected).pack(side="left", expand=True, padx=5)

    def get_lineup(self):
        return self.players

class CountDisplay(tk.Canvas):
    def __init__(self, parent, **kwargs):
        # Default size
        width = kwargs.pop('width', 220)
        height = kwargs.pop('height', 100)
        super().__init__(parent, width=width, height=height, bg="white", highlightthickness=0, **kwargs)
        
        self.colors = {
            "B": "#2f9e44", # Green
            "S": "#fcc419", # Yellow/Gold
            "O": "#e03131", # Red
            "off": "#e9ecef" # Light gray for 'off' state
        }
        
        self.radius = 12
        self.spacing = 30
        self.margin_left = 40
        
        self.draw_labels()
        self.set_count(0, 0, 0)

    def draw_labels(self):
        # Draw B, S, O labels
        font = ("Segoe UI", 14, "bold")
        self.create_text(20, 25, text="B", fill="#495057", font=font)
        self.create_text(20, 55, text="S", fill="#495057", font=font)
        self.create_text(20, 85, text="O", fill="#495057", font=font)

    def set_count(self, balls, strikes, outs):
        self.delete("indicator")
        
        # Balls (up to 3)
        for i in range(3):
            color = self.colors["B"] if i < balls else self.colors["off"]
            self._draw_circle(self.margin_left + i * self.spacing, 25, color)
            
        # Strikes (up to 2)
        for i in range(2):
            color = self.colors["S"] if i < strikes else self.colors["off"]
            self._draw_circle(self.margin_left + i * self.spacing, 55, color)
            
        # Outs (up to 2)
        for i in range(2):
            color = self.colors["O"] if i < outs else self.colors["off"]
            self._draw_circle(self.margin_left + i * self.spacing, 85, color)

    def _draw_circle(self, x, y, color):
        self.create_oval(
            x - self.radius, y - self.radius,
            x + self.radius, y + self.radius,
            fill=color, outline="#adb5bd", width=1, tags="indicator"
        )

class PlateDisciplineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Plate Discipline Manager")
        self.root.geometry("600x900")
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        self.calculator = PlateDisciplineCalculator()
        
        # State Variables
        self.status_var = tk.StringVar(value="Waiting...")
        self.count_var = tk.StringVar(value="B:0 S:0 O:0")
        self.batter_var = tk.StringVar(value="")
        self.pitcher_var = tk.StringVar(value="")
        self.info_var = tk.StringVar(value="")
        
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        self.show_main_menu()

    def configure_styles(self):
        # NPB Style / Professional
        bg_white = "#FFFFFF"
        bg_panel = "#F1F3F5"
        text_dark = "#212529"
        
        self.root.configure(bg=bg_white)
        self.style.configure("TFrame", background=bg_white)
        self.style.configure("TLabel", background=bg_white, foreground=text_dark, font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI", 24, "bold"))
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 16))
        self.style.configure("Status.TLabel", font=("Segoe UI", 14), background=bg_panel)

        self.style.configure("TButton", font=("Segoe UI", 11), padding=6)
        
        # Action Buttons
        self.style.configure("Ball.TButton", background="#ddfbe6", foreground="#1864ab", font=("Segoe UI", 12, "bold")) 
        self.style.configure("Strike.TButton", background="#ffe3e3", foreground="#c92a2a", font=("Segoe UI", 12, "bold")) 
        self.style.configure("InPlay.TButton", background="#e7f5ff", foreground="#1864ab", font=("Segoe UI", 12, "bold")) 
        self.style.configure("Yellow.TButton", background="#fff9db", foreground="#e67700", font=("Segoe UI", 12, "bold")) 

    def clear_frame(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # --- Screens ---

    def show_main_menu(self):
        self.clear_frame()
        frame = ttk.Frame(self.main_container)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="Plate Discipline Manager", style="Header.TLabel").pack(pady=30)
        
        ttk.Button(frame, text="New Game", command=self.show_new_game, width=25).pack(pady=10)
        ttk.Button(frame, text="Stats Dashboard", command=self.show_dashboard, width=25).pack(pady=10)
        ttk.Button(frame, text="Manage Games", command=self.show_game_list, width=25).pack(pady=10)
        ttk.Button(frame, text="Exit", command=self.root.quit, width=25).pack(pady=10)

    def show_new_game(self):
        self.clear_frame()
        frame = ttk.Frame(self.main_container, padding=20)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Game Setup", style="Header.TLabel").pack(pady=(0,10))
        
        # Season Input
        season_f = ttk.Frame(frame)
        season_f.pack(fill="x", pady=5)
        ttk.Label(season_f, text="Season:").pack(side="left")
        self.season_entry = ttk.Entry(season_f)
        self.season_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.season_entry.insert(0, "2026オープン戦") # Default

        # Grid layout for 2 teams
        grid = ttk.Frame(frame)
        grid.pack(fill="both", expand=True)
        
        # Home Team
        home_f = ttk.LabelFrame(grid, text="Home Team (Bottom Inning)", padding=10)
        home_f.grid(row=0, column=0, sticky="nsew", padx=5)
        
        ttk.Label(home_f, text="Team Name:").pack(anchor="w")
        self.home_name = ttk.Entry(home_f)
        self.home_name.pack(fill="x")
        
        ttk.Label(home_f, text="Starting Pitcher:").pack(anchor="w")
        self.home_pitcher = ttk.Entry(home_f)
        self.home_pitcher.pack(fill="x")
        
        ttk.Label(home_f, text="Lineup (Must be 9):").pack(anchor="w", pady=(5,0))
        self.home_lineup_editor = LineupEditor(home_f, self.calculator, self.home_name, self.home_pitcher)
        self.home_lineup_editor.pack(fill="both", expand=True)

        # Away Team
        away_f = ttk.LabelFrame(grid, text="Away Team (Top Inning)", padding=10)
        away_f.grid(row=0, column=1, sticky="nsew", padx=5)
        
        ttk.Label(away_f, text="Team Name:").pack(anchor="w")
        self.away_name = ttk.Entry(away_f)
        self.away_name.pack(fill="x")
        
        ttk.Label(away_f, text="Starting Pitcher:").pack(anchor="w")
        self.away_pitcher = ttk.Entry(away_f)
        self.away_pitcher.pack(fill="x")
        
        ttk.Label(away_f, text="Lineup (Must be 9):").pack(anchor="w", pady=(5,0))
        self.away_lineup_editor = LineupEditor(away_f, self.calculator, self.away_name, self.away_pitcher)
        self.away_lineup_editor.pack(fill="both", expand=True)
        
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)
        
        # Start Button
        btn_f = ttk.Frame(frame, padding=10)
        btn_f.pack(fill="x")
        ttk.Button(btn_f, text="Start Game", command=self.start_game, width=20).pack()
        ttk.Button(btn_f, text="Cancel", command=self.show_main_menu).pack()

    def show_game_list(self):
        self.clear_frame()
        
        h = ttk.Frame(self.main_container, padding=10)
        h.pack(fill="x")
        ttk.Button(h, text="< Back", command=self.show_main_menu).pack(side="left")
        ttk.Label(h, text="Manage Games", style="Header.TLabel").pack(side="left", padx=20)
        
        list_f = ttk.Frame(self.main_container, padding=10)
        list_f.pack(fill="both", expand=True)
        
        cols = ["Date", "Season", "Title", "Score"]
        tree = ttk.Treeview(list_f, columns=cols, show="headings", selectmode="browse")
        tree.heading("Date", text="Date")
        tree.heading("Season", text="Season")
        tree.heading("Title", text="Matchup")
        tree.heading("Score", text="Score (H-A)")
        
        tree.column("Date", width=150)
        tree.column("Season", width=150)
        tree.column("Title", width=300)
        tree.column("Score", width=100)
        
        tree.pack(side="left", fill="both", expand=True)
        
        sb = ttk.Scrollbar(list_f, orient="vertical", command=tree.yview)
        sb.pack(side="right", fill="y")
        tree.config(yscrollcommand=sb.set)
        
        # Populate
        games = self.calculator.get_game_list()
        for g in games:
            score_str = f"{g['score_home']} - {g['score_away']}"
            tree.insert("", "end", iid=g['id'], values=(g['date'], g['season'], g['title'], score_str))
            
        # Actions
        btn_f = ttk.Frame(self.main_container, padding=10)
        btn_f.pack(fill="x")
        
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            game_id = sel[0]
            if messagebox.askyesno("Confirm", "Delete this game?"):
                self.calculator.delete_game(game_id)
                tree.delete(game_id)
        
        def resume_selected():
            sel = tree.selection()
            if not sel: return
            game_id = sel[0]
            if self.calculator.load_game(game_id):
                self.show_game_input()
            else:
                messagebox.showerror("Error", "Failed to load game.")

        ttk.Button(btn_f, text="Resume/Edit", command=resume_selected).pack(side="left")        
        ttk.Button(btn_f, text="Delete Game", command=delete_selected).pack(side="right")

    def show_game_input(self):
        self.clear_frame()
        
        # Header (Scoreboard) - Reduce padding
        header = ttk.Frame(self.main_container, padding=5)
        header.pack(fill="x")
        
        info_l = ttk.Label(header, textvariable=self.info_var, style="SubHeader.TLabel", justify="center")
        info_l.pack()
        
        matchup = ttk.Frame(header)
        matchup.pack(fill="x", pady=2)
        
        ttk.Label(matchup, text="Pitching:", font=("Segoe UI", 10)).pack(side="left")
        ttk.Label(matchup, textvariable=self.pitcher_var, font=("Segoe UI", 12, "bold")).pack(side="left", padx=5)
        
        ttk.Label(matchup, textvariable=self.batter_var, font=("Segoe UI", 12, "bold")).pack(side="right", padx=5)
        ttk.Label(matchup, text="Batting:", font=("Segoe UI", 10)).pack(side="right")
        
        # Count
        count_f = ttk.Frame(self.main_container, padding=5)
        count_f.pack(fill="x")
        
        # Centering the canvas
        inner_count = ttk.Frame(count_f)
        inner_count.pack(expand=True)
        self.count_display = CountDisplay(inner_count)
        self.count_display.pack()

        self.update_header() # Initial populate after widgets created

        # Input Grid (Split Zone)
        grid = ttk.Frame(self.main_container, padding=5)
        grid.pack(fill="both", expand=True)
        
        # Configure Grid
        grid.columnconfigure(0, weight=1) # Out Zone
        grid.columnconfigure(1, weight=1) # In Zone
        grid.rowconfigure(1, weight=1) 
        
        # Headers
        lbl_out = ttk.Label(grid, text="OUT OF ZONE", font=("Segoe UI", 14, "bold"), foreground="white", background="#e03131", padding=10, anchor="center")
        lbl_out.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        
        lbl_in = ttk.Label(grid, text="IN ZONE", font=("Segoe UI", 14, "bold"), foreground="white", background="#1971c2", padding=10, anchor="center")
        lbl_in.grid(row=0, column=1, sticky="ew", padx=1, pady=1)
        
        # Panels
        p_out = ttk.Frame(grid)
        p_out.grid(row=1, column=0, sticky="nsew")
        
        p_in = ttk.Frame(grid)
        p_in.grid(row=1, column=1, sticky="nsew")
        
        # Layout Helper - Expanded vertically with small margin
        def add_btn(parent, txt, style, cmd):
            # ipady for internal height, pady=1 for small margin
            b = ttk.Button(parent, text=txt, style=style, command=cmd)
            b.pack(fill="both", expand=True, pady=1, padx=2) 
            
        # Out Zone Buttons
        add_btn(p_out, "Ball", "Ball.TButton", lambda: self.log("Ball", False))
        add_btn(p_out, "Swing (Miss)", "Yellow.TButton", lambda: self.log("Swinging Strike", False))
        add_btn(p_out, "Foul", "Yellow.TButton", lambda: self.log("Foul", False))
        add_btn(p_out, "Dead Ball", "Ball.TButton", lambda: self.log("Dead Ball", False))
        add_btn(p_out, "Hit/Safe", "InPlay.TButton", lambda: self.log("In Play (Safe)", False))
        add_btn(p_out, "Out", "Strike.TButton", lambda: self.log("In Play (Out)", False))
        
        # In Zone Buttons
        add_btn(p_in, "Called Strike", "Yellow.TButton", lambda: self.log("Called Strike", True))
        add_btn(p_in, "Swing (Miss)", "Yellow.TButton", lambda: self.log("Swinging Strike", True))
        add_btn(p_in, "Foul", "Yellow.TButton", lambda: self.log("Foul", True))
        add_btn(p_in, "Hit/Safe", "InPlay.TButton", lambda: self.log("In Play (Safe)", True))
        add_btn(p_in, "Out", "Strike.TButton", lambda: self.log("In Play (Out)", True))

        # Game Controls
        ctrl = ttk.Frame(self.main_container, padding=5)
        ctrl.pack(fill="x")
        
        ttk.Button(ctrl, text="Change Batter (PH)", command=self.change_batter).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ctrl, text="Change Pitcher", command=self.change_pitcher).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ctrl, text="Runner Out", command=self.runner_out).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ctrl, text="Undo", command=self.undo_last_action).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(ctrl, text="End Game", command=self.show_main_menu).pack(side="right", expand=True, fill="x", padx=2)

    def undo_last_action(self):
        if self.calculator.undo():
            self.update_game_ui_state()
        else:
            messagebox.showinfo("Info", "Nothing to undo.")

    def show_dashboard(self):
        self.clear_frame()
        
        # Header
        h = ttk.Frame(self.main_container, padding=10)
        h.pack(fill="x")
        ttk.Button(h, text="< Back", command=self.show_main_menu).pack(side="left")
        ttk.Label(h, text="Player Statistics", style="Header.TLabel").pack(side="left", padx=20)
        
        ttk.Label(h, text="Player Statistics", style="Header.TLabel").pack(side="left", padx=20)
        
        # Season Filter
        filter_f = ttk.Frame(h)
        filter_f.pack(side="right")
        ttk.Label(filter_f, text="Season:").pack(side="left")
        
        self.season_var = tk.StringVar(value="All Seasons")
        seasons = ["All Seasons"] + self.calculator.get_season_list()
        cb = ttk.Combobox(filter_f, textvariable=self.season_var, values=seasons, state="readonly")
        cb.pack(side="left", padx=5)
        cb.bind("<<ComboboxSelected>>", lambda e: self.update_dashboard_stats())
        
        # Notebook for Tabs
        nb = ttk.Notebook(self.main_container)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        
        tab_batter = ttk.Frame(nb)
        tab_pitcher = ttk.Frame(nb)
        
        nb.add(tab_batter, text="Batter Stats")
        nb.add(tab_pitcher, text="Pitcher Stats")
        
        # Columns (Updated v6.0)
        cols = [
            "Player", "PA", "Pitches", 
            "Swing%", "O-Swing%", "Z-Swing%", 
            "Contact%", "O-Contact%", "Z-Contact%", 
            "Zone%", "F-Strike%", "Whiff%", 
            "Put Away%", "SwStr%", "CStr%", "CSW%"
        ]
        
        def create_table(parent, role):
            tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="extended")
            
            # Sort Logic
            def sort_column(col, reverse):
                l = [(tree.set(k, col), k) for k in tree.get_children('')]
                
                def convert(val):
                    try:
                        return float(val.replace("%", "").strip())
                    except ValueError:
                        return val
                
                l.sort(key=lambda t: convert(t[0]), reverse=reverse)
                
                for index, (val, k) in enumerate(l):
                    tree.move(k, '', index)
                
                tree.heading(col, command=lambda: sort_column(col, not reverse))

            # Setup Columns
            for c in cols:
                tree.heading(c, text=c, command=lambda _c=c: sort_column(_c, True)) # Default Descending
                w = 100 if c == "Player" else 60
                tree.column(c, width=w, anchor="center" if c!="Player" else "w")
            
            # Scrollbars
            vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            tree.grid(row=0, column=0, sticky="nsew")
            vsb.grid(row=0, column=1, sticky="ns")
            hsb.grid(row=1, column=0, sticky="ew")
            
            parent.grid_rowconfigure(0, weight=1)
            parent.grid_columnconfigure(0, weight=1)
            
            # Populate
            stats = self.calculator.get_aggregate_stats(role)
            for name, s in stats.items():
                vals = [name]
                # Helper to format %
                def f(k): return s[k] if isinstance(s[k], str) else f"{s[k]:.1f}%"
                
                vals.append(s["PA"])
                vals.append(s["Pitches"])
                vals.append(f("Swing%"))
                vals.append(f("O-Swing%"))
                vals.append(f("Z-Swing%"))
                vals.append(f("Contact%"))
                vals.append(f("O-Contact%"))
                vals.append(f("Z-Contact%"))
                vals.append(f("Zone%"))
                vals.append(f("F-Strike%"))
                vals.append(f("Whiff%"))
                vals.append(f("Put Away%"))
                vals.append(f("SwStr%"))
                vals.append(f("CStr%"))
                vals.append(f("CSW%"))
                
                tree.insert("", "end", values=vals)
            
            # Right-click Context Menu for Copy
            menu = tk.Menu(tree, tearoff=0)
            
            def copy_selected():
                sel = tree.selection()
                if not sel: return
                
                all_text = []
                for item_id in sel:
                    item = tree.item(item_id)
                    values = item["values"]
                    lines = []
                    player_name = values[0]
                    for i, col_name in enumerate(cols):
                        lines.append(f"{col_name}: {values[i]}")
                    all_text.append("\n".join(lines))
                
                text = "\n\n---\n\n".join(all_text)
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                messagebox.showinfo("Copied", f"{len(sel)} player stats copied to clipboard.")
            
            def copy_selected_tsv():
                sel = tree.selection()
                if not sel: return
                
                # Tab-separated for pasting into spreadsheets
                header = "\t".join(cols)
                rows = [header]
                
                for item_id in sel:
                    item = tree.item(item_id)
                    values = item["values"]
                    row = "\t".join(str(v) for v in values)
                    rows.append(row)
                
                text = "\n".join(rows)
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                messagebox.showinfo("Copied", f"{len(sel)} player stats copied (TSV format).")
            
            menu.add_command(label="Copy Stats (Text)", command=copy_selected)
            menu.add_command(label="Copy Stats (TSV)", command=copy_selected_tsv)
            
            def show_menu(event):
                # Select the row under cursor ONLY if it's not already part of a multi-selection
                row_id = tree.identify_row(event.y)
                if row_id:
                    if row_id not in tree.selection():
                        tree.selection_set(row_id)
                    menu.post(event.x_root, event.y_root)
            
            tree.bind("<Button-3>", show_menu)
            
            return tree

        
        # Store trees for update
        self.stats_trees = {
            "batter": create_table(tab_batter, "batter"),
            "pitcher": create_table(tab_pitcher, "pitcher")
        }
        
        self.update_dashboard_stats()

    def update_dashboard_stats(self):
        season = self.season_var.get()
        season_filter = None if season == "All Seasons" else season
        
        for role, tree in self.stats_trees.items():
            # Clear current
            for item in tree.get_children():
                tree.delete(item)
                
            stats = self.calculator.get_aggregate_stats(role, season_filter)
            
            for player, d in stats.items():
                 # Helper to format %
                def f(k): return d[k] if isinstance(d[k], str) else f"{d[k]:.1f}%"
                
                vals = (
                    player, d["PA"], d["Pitches"],
                    f("Swing%"), f("O-Swing%"), f("Z-Swing%"),
                    f("Contact%"), f("O-Contact%"), f("Z-Contact%"),
                    f("Zone%"), f("F-Strike%"), f("Whiff%"),
                    f("Put Away%"), f("SwStr%"), f("CStr%"), f("CSW%")
                )
                tree.insert("", "end", values=vals)

    # ... Logic methods ... (unchanged)

    def start_game(self):
        hn = self.home_name.get()
        an = self.away_name.get()
        hp = self.home_pitcher.get()
        ap = self.away_pitcher.get()
        season = self.season_entry.get()
        
        hl = self.home_lineup_editor.get_lineup()
        al = self.away_lineup_editor.get_lineup()
        
        if not (hn and an and hp and ap):
             messagebox.showwarning("Error", "Please fill team names and pitchers.")
             return
             
        try:
            self.calculator.start_new_game(hn, an, hl, al, hp, ap, season)
            self.update_game_ui_state()
            self.show_game_input()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def update_game_ui_state(self):
        s = self.calculator.get_game_state()
        if not s: return

        top_bot = "Top" if s['is_top'] else "Bot"
        self.info_var.set(f"Inning {s['inning']} {top_bot} | Outs: {s['outs']}")
        
        # Update Visual Count
        if hasattr(self, 'count_display') and self.count_display.winfo_exists():
            self.count_display.set_count(s['balls'], s['strikes'], s['outs'])
        
        self.pitcher_var.set(s['pitcher'])
        self.batter_var.set(s['batter'])

    def update_header(self):
        self.update_game_ui_state()

    def log(self, result, in_zone=False):
        s = self.calculator.get_game_state()
        # Auto-detect first pitch: balls=0, strikes=0
        is_first = (s['balls'] == 0 and s['strikes'] == 0)
        
        zone = "In" if in_zone else "Out"
        self.calculator.log_pitch(zone, result, is_first)
        self.update_game_ui_state()
    
    def change_batter(self):
        new_b = simpledialog.askstring("Change Batter", "Enter new batter name (PH):")
        if new_b:
            self.calculator.substitute_batter(new_b)
            self.update_game_ui_state()

    def runner_out(self):
        self.calculator.record_runner_out()
        self.update_game_ui_state()

    def change_pitcher(self):
        new_p = simpledialog.askstring("Change Pitcher", "Enter new pitcher name:")
        if new_p:
            self.calculator.change_pitcher(new_p)
            self.update_game_ui_state()

if __name__ == "__main__":
    import sys, os
    root = tk.Tk()
    # Set window icon
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(base_path, 'PlateDisciplineManager.ico')
    if os.path.exists(ico_path):
        root.iconbitmap(ico_path)
    app = PlateDisciplineApp(root)
    # Resize window as requested
    root.geometry("900x900") 
    root.mainloop()
