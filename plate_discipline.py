import json
import os
import uuid
from datetime import datetime
import copy

class PlateDisciplineCalculator:
    def __init__(self, data_file='data.json'):
        self.data_file = data_file
        self.data = self.load_data()
        self.data = self.load_data()
        self.current_game = None
        self.history = []

    def load_data(self):
        if not os.path.exists(self.data_file):
            return {"games": [], "players": []}
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"games": [], "players": []}

    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_player_list(self):
        return sorted(self.data.get("players", []))

    def add_player(self, name):
        if name not in self.data["players"]:
            self.data["players"].append(name)
            self.save_data()

    def start_new_game(self, home_team, away_team, home_lineup, away_lineup, home_pitcher, away_pitcher, season=""):
        if len(home_lineup) != 9:
            raise ValueError(f"Home lineup must have exactly 9 players. Current: {len(home_lineup)}")
        if len(away_lineup) != 9:
            raise ValueError(f"Away lineup must have exactly 9 players. Current: {len(away_lineup)}")

        game_id = str(uuid.uuid4())
        
        self.current_game = {
            "id": game_id,
            "season": season,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "teams": {
                "home": {
                    "name": home_team,
                    "lineup": home_lineup,
                    "pitcher": home_pitcher
                },
                "away": {
                    "name": away_team,
                    "lineup": away_lineup,
                    "pitcher": away_pitcher
                }
            },
            "state": {
                "inning": 1,
                "is_top": True, # True = Top (Away bats), False = Bottom (Home bats)
                "outs": 0,
                "balls": 0,
                "strikes": 0,
                "current_batter_idx": {"home": 0, "away": 0},
                "score": {"home": 0, "away": 0}
            },
            "pitches": []
        }
        
        self.history = [] # Reset history for new game
        
        # Register all players
        for p in home_lineup + away_lineup:
            self.add_player(p)
        self.add_player(home_pitcher)
        self.add_player(away_pitcher)

        self.data["games"].append(self.current_game)
        self.save_data()
        return self.current_game
    
    def get_known_players(self):
        """Return a sorted list of all players ever registered."""
        return sorted(self.data.get("players", []))

    def save_lineup(self, name, players, team_name="", pitcher_name=""):
        """Save a named lineup with optional team and pitcher info."""
        if "saved_lineups" not in self.data:
            self.data["saved_lineups"] = {}
        
        self.data["saved_lineups"][name] = {
            "players": players,
            "team": team_name,
            "pitcher": pitcher_name
        }
        self.save_data()

    def delete_lineup(self, name):
        """Delete a saved lineup."""
        if "saved_lineups" in self.data and name in self.data["saved_lineups"]:
            del self.data["saved_lineups"][name]
            self.save_data()

    def get_saved_lineups(self):
        """Return dict of saved lineups."""
        return self.data.get("saved_lineups", {})

    def get_game_state(self):
        if not self.current_game:
            return None
        
        state = self.current_game["state"]
        teams = self.current_game["teams"]
        
        is_top = state["is_top"]
        batting_team_key = "away" if is_top else "home"
        pitching_team_key = "home" if is_top else "away"
        
        batter_idx = state["current_batter_idx"][batting_team_key]
        lineup = teams[batting_team_key]["lineup"]
        current_batter = lineup[batter_idx % len(lineup)]
        current_pitcher = teams[pitching_team_key]["pitcher"]
        
        return {
            "inning": state["inning"],
            "is_top": is_top,
            "outs": state["outs"],
            "balls": state["balls"],
            "strikes": state["strikes"],
            "batter": current_batter,
            "pitcher": current_pitcher,
            "batting_team": teams[batting_team_key]["name"],
            "pitching_team": teams[pitching_team_key]["name"],
            "score": state["score"]
        }

    def get_game_list(self):
        """Return list of (id, date, home_team, away_team, score_h, score_a, season) for all games."""
        games = []
        for g in self.data["games"]:
            s = g["state"]["score"]
            h_name = g["teams"]["home"]["name"]
            a_name = g["teams"]["away"]["name"]
            title = f"{h_name} vs {a_name}"
            games.append({
                "id": g["id"],
                "date": g["date"],
                "season": g.get("season", ""),
                "title": title,
                "score_home": s["home"],
                "score_away": s["away"]
            })
        return games

    def get_season_list(self):
        """Return a sorted list of unique seasons found in games."""
        seasons = set()
        for g in self.data["games"]:
            seasons.add(g.get("season", "").strip())
        return sorted([s for s in seasons if s])

    def delete_game(self, game_id):
        self.data["games"] = [g for g in self.data["games"] if g["id"] != game_id]
        if self.current_game and self.current_game["id"] == game_id:
            self.current_game = None
        self.save_data()

    def load_game(self, game_id):
        """Load an existing game and set it as current."""
        found = None
        for g in self.data["games"]:
            if g["id"] == game_id:
                found = g
                break
        
        if found:
            self.current_game = found
            self.history = [] # Reset history regarding of previous state
            return True
        return False

    def _save_state(self):
        """Push current state to history."""
        if self.current_game:
            self.history.append(copy.deepcopy(self.current_game))

    def undo(self):
        """Revert to previous state."""
        if not self.history:
            return False
        
        self.current_game = self.history.pop()
        
        # Update the game in the main data list to match the reverted state
        for i, g in enumerate(self.data["games"]):
            if g["id"] == self.current_game["id"]:
                self.data["games"][i] = self.current_game
                break
                
        self.save_data()
        return True

    def log_pitch(self, zone, result, is_first_pitch):
        if not self.current_game:
            raise ValueError("No active game")
        
        self._save_state()
        
        # Raw state for updates
        
        # Raw state for updates
        raw_state = self.current_game["state"]
        
        # Derived state for logging (batter name, pitcher name, etc.)
        derived_state = self.get_game_state()
        
        # Capture state BEFORE result processing for metrics like PutAway%
        pre_balls = raw_state["balls"]
        pre_strikes = raw_state["strikes"]
        
        pitch_data = {
            "batter": derived_state["batter"],
            "pitcher": derived_state["pitcher"],
            "zone": zone,
            "result": result,
            "is_first_pitch": is_first_pitch,
            "inning": raw_state["inning"],
            "is_top": raw_state["is_top"],
            "balls_before": pre_balls,     # NEW for v6.0
            "strikes_before": pre_strikes  # NEW for v6.0
        }
        self.current_game["pitches"].append(pitch_data)
        
        # Update Counts
        self._update_counts(result, raw_state)
        
        self.save_data()

    def _update_counts(self, result, state_info):
        """Internal logic to update balls, strikes, outs, innings."""
        s = self.current_game["state"]
        
        if result == "Ball":
            s["balls"] += 1
            if s["balls"] >= 4:
                self._next_batter() # Walk
        
        elif result in ["Called Strike", "Swinging Strike"]:
            if s["strikes"] < 2:
                s["strikes"] += 1
            else:
                self._record_out() # Strikeout
        
        elif result == "Foul":
            if s["strikes"] < 2:
                s["strikes"] += 1
            # Foul with 2 strikes stays at 2 strikes
        
        elif result == "Dead Ball":
            self._next_batter()

        elif "In Play" in result:
            if "(Out)" in result:
                self._record_out()
            else:
                self._next_batter() # Assume Safe/Hit/Error if not explicitly Out 

    # Explicit methods for Outs and Advances to be called by GUI
    def record_out_explicit(self):
        """Call this when a batter makes an out in play."""
        self._record_out()

    def record_safe_explicit(self):
        """Call this when a batter reaches base in play."""
        self._next_batter()

    def _next_batter(self):
        """Reset count and move to next batter in lineup."""
        s = self.current_game["state"]
        s["balls"] = 0
        s["strikes"] = 0
        
        team_key = "away" if s["is_top"] else "home"
        s["current_batter_idx"][team_key] += 1
        
        self.save_data()

    def record_runner_out(self):
        """Manually record an out (caught stealing, pick-off, etc.). 
        Does not advance to next batter even if it's the 3rd out."""
        if not self.current_game: return
        self._save_state()
        
        s = self.current_game["state"]
        s["outs"] += 1
        
        if s["outs"] >= 3:
            self._switch_sides()
        else:
            self.save_data()

    def _record_out(self):
        """Increment outs. Switch sides if 3 outs."""
        s = self.current_game["state"]
        s["outs"] += 1
        s["balls"] = 0
        s["strikes"] = 0
        
        # Batter index increments even on an out
        team_key = "away" if s["is_top"] else "home"
        s["current_batter_idx"][team_key] += 1

        if s["outs"] >= 3:
            self._switch_sides()
            
        self.save_data()

    def _switch_sides(self):
        s = self.current_game["state"]
        s["outs"] = 0
        s["balls"] = 0
        s["strikes"] = 0
        
        if s["is_top"]:
            s["is_top"] = False # Go to Bottom
        else:
            s["is_top"] = True # Go to Top of Next Inning
            s["inning"] += 1

    def substitute_batter(self, new_batter_name):
        """Replace the current batter in the lineup with a new player (Pinch Hitter)."""
        if not self.current_game:
            return
            
        self._save_state()

        s = self.current_game["state"]
        # Identify current team
        team_key = "away" if s["is_top"] else "home"
        
        # Get current lineup index
        idx = s["current_batter_idx"][team_key]
        lineup = self.current_game["teams"][team_key]["lineup"]
        
        # Replace player at current index (modulo length)
        # Note: In real baseball, the player is replaced in the lineup slot permanently for the game.
        slot_idx = idx % len(lineup)
        lineup[slot_idx] = new_batter_name
        
        self.add_player(new_batter_name)
        self.save_data()

    def change_pitcher(self, new_pitcher_name):
        """Update the current pitcher for the fielding team."""
        if not self.current_game:
            return
        
        self._save_state()
            
        s = self.current_game["state"]
        # If top, away is batting, home is pitching.
        pitching_team_key = "home" if s["is_top"] else "away"
        
        self.current_game["teams"][pitching_team_key]["pitcher"] = new_pitcher_name
        self.add_player(new_pitcher_name)
        self.save_data()

    def get_aggregate_stats(self, role_filter=None, season_filter=None):
        """
        Calculate stats.
        role_filter: 'batter' (returns stats where player was batter), 'pitcher' (where player was pitcher), or None (all).
        season_filter: if params provided, filter only games with matching season string.
        """
        stats = {}
        
        for g in self.data["games"]:
            # Check Season Filter
            if season_filter:
                g_season = g.get("season", "")
                if g_season != season_filter:
                    continue

            for p in g["pitches"]:
                # Determine targets
                targets = []
                if role_filter == "batter":
                    targets.append(p["batter"])
                elif role_filter == "pitcher":
                    targets.append(p["pitcher"])
                else:
                    targets.append(p["batter"])
                    targets.append(p["pitcher"])

                for player in targets:
                    if player not in stats:
                        stats[player] = {
                            "PA": 0,
                            "Pitches": 0,
                            "Swing": 0, "Contact": 0,
                            "O-Swing": 0, "O-Pitch": 0,
                            "Z-Swing": 0, "Z-Pitch": 0,
                            "Z-Contact": 0, "O-Contact": 0,
                            "FirstPitch": 0, "FirstStrike": 0,
                            "SwingingStrike": 0, "CalledStrike": 0,
                            "TwoStrikePitches": 0, "Strikeouts": 0
                        }
                    
                    s = stats[player]
                    s["Pitches"] += 1
                    
                    is_in_zone = (p["zone"] == "In")
                    result = p["result"]
                    
                    # Swing Definition
                    is_swing = result in ["Swinging Strike", "Foul", "In Play (Safe)", "In Play (Out)"]
                    is_contact = result in ["Foul", "In Play (Safe)", "In Play (Out)"]
                    
                    if is_swing: s["Swing"] += 1
                    if is_contact: s["Contact"] += 1
                    
                    if is_in_zone:
                        s["Z-Pitch"] += 1
                        if is_swing:
                            s["Z-Swing"] += 1
                            if is_contact: s["Z-Contact"] += 1
                    else:
                        s["O-Pitch"] += 1
                        if is_swing:
                            s["O-Swing"] += 1
                            if is_contact: s["O-Contact"] += 1

                    # First Pitch Strike
                    if p.get("is_first_pitch", False):
                        s["FirstPitch"] += 1
                        if result != "Ball":
                            s["FirstStrike"] += 1
                    
                    # Whiff, CSW components
                    if result == "Swinging Strike":
                        s["SwingingStrike"] += 1
                    if result == "Called Strike":
                        s["CalledStrike"] += 1
                        
                    # PA Calculation & PutAway
                    # Use 'strikes_before', 'balls_before' if available (v6.0+)
                    strikes_before = p.get("strikes_before", 0)
                    balls_before = p.get("balls_before", 0)
                    
                    is_pa = False
                    if "In Play" in result:
                        is_pa = True
                    elif result == "Dead Ball":
                        is_pa = True # HBP
                    elif result == "Ball" and balls_before == 3:
                        is_pa = True # Walk
                    elif (result == "Called Strike" or result == "Swinging Strike") and strikes_before == 2:
                        is_pa = True # Strikeout
                        
                    if is_pa:
                        s["PA"] += 1

                    # PutAway (Strikeout on 2 strikes)
                    if strikes_before == 2:
                        s["TwoStrikePitches"] += 1
                        if result in ["Swinging Strike", "Called Strike"]:
                            s["Strikeouts"] += 1

        final_stats = {}
        def pct(n, d): return (n / d * 100) if d > 0 else 0.0

        for name, d in stats.items():
            final_stats[name] = {
                "PA": d["PA"], 
                "Pitches": d["Pitches"],
                "Swing%": pct(d["Swing"], d["Pitches"]),
                "O-Swing%": pct(d["O-Swing"], d["O-Pitch"]),
                "Z-Swing%": pct(d["Z-Swing"], d["Z-Pitch"]),
                "Contact%": pct(d["Contact"], d["Swing"]),
                "O-Contact%": pct(d["O-Contact"], d["O-Swing"]),
                "Z-Contact%": pct(d["Z-Contact"], d["Z-Swing"]),
                "Zone%": pct(d["Z-Pitch"], d["Pitches"]),
                "F-Strike%": pct(d["FirstStrike"], d["FirstPitch"]),
                "Whiff%": pct(d["SwingingStrike"], d["Swing"]),
                "Put Away%": pct(d["Strikeouts"], d["TwoStrikePitches"]),
                "SwStr%": pct(d["SwingingStrike"], d["Pitches"]),
                "CStr%": pct(d["CalledStrike"], d["Pitches"]),
                "CSW%": pct(d["SwingingStrike"] + d["CalledStrike"], d["Pitches"])
            }
            
        return final_stats
