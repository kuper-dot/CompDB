import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector

class LoginDialog(simpledialog.Dialog):
    """Dialog for user login to the database."""
    def __init__(self, parent):
        self.credentials = None
        super().__init__(parent, title="Login to Database")

    def body(self, master):
        """Create input fields for database credentials."""
        tk.Label(master, text="Host:").grid(row=0, column=0, sticky="w")
        self.host_input = tk.Entry(master)
        self.host_input.insert(0, "192.168.0.113")  # Default host
        self.host_input.grid(row=0, column=1)

        tk.Label(master, text="Port:").grid(row=1, column=0, sticky="w")
        self.port_input = tk.Entry(master)
        self.port_input.insert(0, "3306")  # Default port
        self.port_input.grid(row=1, column=1)

        tk.Label(master, text="Username:").grid(row=2, column=0, sticky="w")
        self.user_input = tk.Entry(master)
        self.user_input.grid(row=2, column=1)

        tk.Label(master, text="Password:").grid(row=3, column=0, sticky="w")
        self.password_input = tk.Entry(master, show="*")
        self.password_input.grid(row=3, column=1)

    def apply(self):
        """Save credentials and validate them."""
        self.credentials = {
            "host": self.host_input.get(),
            "port": int(self.port_input.get()),
            "user": self.user_input.get(),
            "password": self.password_input.get()
        }
        if not self.validate_credentials():
            self.credentials = None  # Reset credentials if validation fails
            self.focus_set()  # Keep the dialog open and refocus on it

    def validate_credentials(self):
        """Validate database credentials by attempting a connection."""
        try:
            conn = mysql.connector.connect(
                host=self.credentials["host"],
                port=self.credentials["port"],
                user=self.credentials["user"],
                password=self.credentials["password"]
            )
            conn.close()
            return True
        except mysql.connector.Error as e:
            messagebox.showerror("Login Error", f"Failed to connect to the database: {e}")
            return False

def connect_db(credentials):
    """Establish a connection to the database using the provided credentials."""
    try:
        return mysql.connector.connect(
            host=credentials["host"],
            port=credentials["port"],
            user=credentials["user"],
            password=credentials["password"],
            database="compDB"
        )
    except mysql.connector.Error as e:
        messagebox.showerror("Database Connection Error", str(e))
        return None

class CompetitionDBApp(tk.Tk):
    """Main application for managing competition data."""
    def __init__(self, db_credentials):
        super().__init__()
        self.db_credentials = db_credentials
        self.selected_competition_id = None  # Track the selected competition
        self.title("Competition DB Manager")
        self.geometry("1000x600")  # Set window size

        # Create tabs for different sections
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(expand=1, fill="both")

        self.team_tab = ttk.Frame(self.tabs)
        self.score_tab = ttk.Frame(self.tabs)
        self.games_tab = ttk.Frame(self.tabs)
        self.players_tab = ttk.Frame(self.tabs)
        self.competitions_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.team_tab, text="Teams")
        self.tabs.add(self.score_tab, text="Scores")
        self.tabs.add(self.games_tab, text="Games")
        self.tabs.add(self.players_tab, text="Players")
        self.tabs.add(self.competitions_tab, text="Competitions")

        # Initialize UI components
        self.init_competition_selector()
        self.init_team_tab()
        self.init_score_tab()
        self.init_games_tab()
        self.init_players_tab()
        self.init_competitions_tab()

        self.clear_competition_filter()  # Load all data on startup

    def init_competition_selector(self):
        """Create a dropdown to select a competition and a button to clear the filter."""
        frame = ttk.Frame(self)
        frame.pack(fill="x", pady=5)

        tk.Label(frame, text="Select Competition:").pack(side="left", padx=5)
        self.competition_dropdown = ttk.Combobox(frame, state="readonly", width=40)
        self.competition_dropdown.pack(side="left", padx=5)
        self.competition_dropdown.bind("<<ComboboxSelected>>", self.on_competition_selected)

        self.refresh_competition_list()

        self.clear_filter_btn = ttk.Button(frame, text="Clear Filter", command=self.clear_competition_filter)
        self.clear_filter_btn.pack(side="left", padx=5)

    def refresh_competition_list(self):
        """Populate the competition dropdown with data from the database."""
        conn = connect_db(self.db_credentials)
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM competitions")
            competitions = cursor.fetchall()
            conn.close()
            self.competition_dropdown["values"] = [f"{comp[0]} - {comp[1]}" for comp in competitions]

    def clear_competition_filter(self):
        """Clear the competition filter and display all data."""
        self.selected_competition_id = None
        self.competition_dropdown.set("")  # Clear the dropdown selection
        self.fetch_all_data()

    def fetch_all_data(self):
        """Fetch and refresh data for all tabs."""
        if self.selected_competition_id:
            self.fetch_teams()
            self.fetch_scores()
            self.fetch_games()
            self.fetch_players()
        else:
            self.load_all_data()

    def load_all_data(self):
        """Load all data for all tabs when no competition is selected."""
        conn = connect_db(self.db_credentials)
        if conn:
            try:
                cursor = conn.cursor()

                # Fetch all teams
                cursor.execute("""
                    SELECT teams.id, teams.name, competitions.name AS competition_name, teams.score
                    FROM teams
                    JOIN competitions ON teams.comp_id = competitions.id
                """)
                rows = cursor.fetchall()
                for row in self.team_table.get_children():
                    self.team_table.delete(row)
                for row in rows:
                    self.team_table.insert("", "end", values=row)

                # Fetch all scores
                cursor.execute("""
                    SELECT 
                        COALESCE(teams.name, 'N/A') AS team_name,
                        COALESCE(players.name, 'N/A') AS player_name,
                        games.name AS game_name,
                        competitions.name AS competition_name,
                        total_scores_log.points,
                        total_scores_log.comment
                    FROM total_scores_log
                    LEFT JOIN teams ON total_scores_log.team_id = teams.id
                    LEFT JOIN players ON total_scores_log.player_id = players.id
                    JOIN games ON total_scores_log.game_id = games.id
                    JOIN competitions ON games.comp_id = competitions.id
                """)
                rows = cursor.fetchall()
                for row in self.score_table.get_children():
                    self.score_table.delete(row)
                for row in rows:
                    self.score_table.insert("", "end", values=row)

                # Fetch all games
                cursor.execute("""
                    SELECT games.id, competitions.name AS competition_name, games.name, 
                           games.team_game, games.date_played, games.created_at
                    FROM games
                    JOIN competitions ON games.comp_id = competitions.id
                """)
                rows = cursor.fetchall()
                for row in self.games_table.get_children():
                    self.games_table.delete(row)
                for row in rows:
                    row = list(row)
                    row[3] = "Yes" if row[3] else "No"  # Convert team_game boolean to "Yes" or "No"
                    self.games_table.insert("", "end", values=row)

                # Fetch all players
                cursor.execute("""
                    SELECT players.id, teams.name AS team_name, players.name AS player_name, players.created_at
                    FROM players
                    LEFT JOIN teams ON players.team_id = teams.id
                """)
                rows = cursor.fetchall()
                for row in self.players_table.get_children():
                    self.players_table.delete(row)
                for row in rows:
                    self.players_table.insert("", "end", values=row)

                conn.close()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

    def on_competition_selected(self, event):
        """Handle competition selection from the dropdown."""
        selected = self.competition_dropdown.get()
        if selected:
            self.selected_competition_id = int(selected.split(" - ")[0])  # Extract competition ID
            self.fetch_all_data()

    def init_team_tab(self):
        """Initialize the Teams tab with input fields and a table."""
        frame = ttk.Frame(self.team_tab)
        frame.pack(fill="both", expand=True)

        self.team_input = ttk.Entry(frame)
        self.team_input.pack(pady=5)

        self.add_team_btn = ttk.Button(frame, text="Add Team", command=self.add_team)
        self.add_team_btn.pack(pady=5)

        self.delete_team_btn = ttk.Button(frame, text="Delete Team", command=self.delete_team)
        self.delete_team_btn.pack(pady=5)

        self.team_table = ttk.Treeview(frame, columns=("ID", "Name", "Comp ID", "Score"), show="headings")
        self.team_table.heading("ID", text="ID")
        self.team_table.heading("Name", text="Name")
        self.team_table.heading("Comp ID", text="Competition Name")
        self.team_table.heading("Score", text="Score")
        self.team_table.pack(fill="both", expand=True)

    def delete_team(self):
        """Delete the selected team from the database."""
        selected_item = self.team_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a team to delete.")
            return

        team_id = self.team_table.item(selected_item, "values")[0]
        conn = connect_db(self.db_credentials)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM teams WHERE id = %s", (team_id,))
                conn.commit()
                conn.close()
                self.fetch_all_data()  # Automatically refresh data
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

    def init_score_tab(self):
        """Initialize the Scores tab with input fields and a table."""
        frame = ttk.Frame(self.score_tab)
        frame.pack(fill="both", expand=True)

        self.load_scores_btn = ttk.Button(frame, text="Load Scores", command=self.fetch_scores)
        self.load_scores_btn.pack(pady=5)

        self.add_score_btn = ttk.Button(frame, text="Add Score", command=self.add_score)
        self.add_score_btn.pack(pady=5)

        self.delete_score_btn = ttk.Button(frame, text="Delete Score", command=self.delete_score)
        self.delete_score_btn.pack(pady=5)

        self.score_table = ttk.Treeview(frame, columns=("Team Name", "Player Name", "Game Name", "Competition Name", "Points", "Comment"), show="headings")
        self.score_table.heading("Team Name", text="Team Name")
        self.score_table.heading("Player Name", text="Player Name")
        self.score_table.heading("Game Name", text="Game Name")
        self.score_table.heading("Competition Name", text="Competition Name")
        self.score_table.heading("Points", text="Points")
        self.score_table.heading("Comment", text="Comment")
        self.score_table.pack(fill="both", expand=True)

        # Adjust column widths to ensure all fields are visible
        self.score_table.column("Team Name", width=150)
        self.score_table.column("Player Name", width=150)
        self.score_table.column("Game Name", width=150)
        self.score_table.column("Competition Name", width=150)
        self.score_table.column("Points", width=100)
        self.score_table.column("Comment", width=250)

    def delete_score(self):
        """Delete the selected score from the database."""
        selected_item = self.score_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a score to delete.")
            return

        score_id = self.score_table.item(selected_item, "values")[0]
        conn = connect_db(self.db_credentials)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM total_scores_log WHERE id = %s", (score_id,))
                conn.commit()
                conn.close()
                self.fetch_all_data()  # Automatically refresh data
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

    def init_games_tab(self):
        """Initialize the Games tab with input fields and a table."""
        frame = ttk.Frame(self.games_tab)
        frame.pack(fill="both", expand=True)

        self.load_games_btn = ttk.Button(frame, text="Load Games", command=self.fetch_games)
        self.load_games_btn.pack(pady=5)

        self.add_game_btn = ttk.Button(frame, text="Add Game", command=self.add_game)
        self.add_game_btn.pack(pady=5)

        self.delete_game_btn = ttk.Button(frame, text="Delete Game", command=self.delete_game)
        self.delete_game_btn.pack(pady=5)

        self.games_table = ttk.Treeview(frame, columns=("ID", "Competition Name", "Name", "Team Game", "Date Played", "Created At"), show="headings")
        self.games_table.heading("ID", text="ID")
        self.games_table.heading("Competition Name", text="Competition Name")
        self.games_table.heading("Name", text="Name")
        self.games_table.heading("Team Game", text="Team Game")
        self.games_table.heading("Date Played", text="Date Played")
        self.games_table.heading("Created At", text="Created At")
        self.games_table.pack(fill="both", expand=True)

    def delete_game(self):
        """Delete the selected game from the database."""
        selected_item = self.games_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a game to delete.")
            return

        game_id = self.games_table.item(selected_item, "values")[0]
        conn = connect_db(self.db_credentials)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM games WHERE id = %s", (game_id,))
                conn.commit()
                conn.close()
                self.fetch_all_data()  # Automatically refresh data
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

    def init_players_tab(self):
        """Initialize the Players tab with input fields and a table."""
        frame = ttk.Frame(self.players_tab)
        frame.pack(fill="both", expand=True)

        self.load_players_btn = ttk.Button(frame, text="Load Players", command=self.fetch_players)
        self.load_players_btn.pack(pady=5)

        self.add_player_btn = ttk.Button(frame, text="Add Player", command=self.add_player)
        self.add_player_btn.pack(pady=5)

        self.delete_player_btn = ttk.Button(frame, text="Delete Player", command=self.delete_player)
        self.delete_player_btn.pack(pady=5)

        self.players_table = ttk.Treeview(frame, columns=("ID", "Team Name", "Player Name", "Created At"), show="headings")
        self.players_table.heading("ID", text="ID")
        self.players_table.heading("Team Name", text="Team Name")
        self.players_table.heading("Player Name", text="Player Name")
        self.players_table.heading("Created At", text="Created At")
        self.players_table.pack(fill="both", expand=True)

    def delete_player(self):
        """Delete the selected player from the database."""
        selected_item = self.players_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a player to delete.")
            return

        player_id = self.players_table.item(selected_item, "values")[0]
        conn = connect_db(self.db_credentials)
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM players WHERE id = %s", (player_id,))
                conn.commit()
                conn.close()
                self.fetch_all_data()  # Automatically refresh data
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

    def init_competitions_tab(self):
        """Initialize the Competitions tab with input fields and a table."""
        frame = ttk.Frame(self.competitions_tab)
        frame.pack(fill="both", expand=True)

        self.load_competitions_btn = ttk.Button(frame, text="Load Competitions", command=self.fetch_competitions)
        self.load_competitions_btn.pack(pady=5)

        self.add_competition_btn = ttk.Button(frame, text="Add Competition", command=self.add_competition)
        self.add_competition_btn.pack(pady=5)

        self.delete_competition_btn = ttk.Button(frame, text="Delete Competition", command=self.delete_competition)
        self.delete_competition_btn.pack(pady=5)

        self.competitions_table = ttk.Treeview(frame, columns=("ID", "Name", "Start Date", "End Date", "Created At"), show="headings")
        self.competitions_table.heading("ID", text="ID")
        self.competitions_table.heading("Name", text="Name")
        self.competitions_table.heading("Start Date", text="Start Date")
        self.competitions_table.heading("End Date", text="End Date")
        self.competitions_table.heading("Created At", text="Created At")
        self.competitions_table.pack(fill="both", expand=True)

    def delete_competition(self):
        """Delete the selected competition from the database."""
        selected_item = self.competitions_table.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a competition to delete.")
            return

        competition_id = self.competitions_table.item(selected_item, "values")[0]
        conn = connect_db(self.db_credentials)
        if conn:
            try:
                cursor = conn.cursor()

                # Check if the competition is referenced in other tables
                cursor.execute("""
                    SELECT COUNT(*) FROM teams WHERE comp_id = %s
                """, (competition_id,))
                team_count = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM games WHERE comp_id = %s
                """, (competition_id,))
                game_count = cursor.fetchone()[0]

                if team_count > 0 or game_count > 0:
                    messagebox.showerror(
                        "Delete Error",
                        "This competition cannot be deleted because it is referenced in other tables (Teams or Games)."
                    )
                    conn.close()
                    return

                # Proceed with deletion if no references exist
                cursor.execute("DELETE FROM competitions WHERE id = %s", (competition_id,))
                conn.commit()
                conn.close()
                self.fetch_all_data()  # Automatically refresh data
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

    def fetch_teams(self):
        """Fetch and display teams for the selected competition."""
        conn = connect_db(self.db_credentials)
        if conn is None or self.selected_competition_id is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT teams.id, teams.name, competitions.name AS competition_name, teams.score
                FROM teams
                JOIN competitions ON teams.comp_id = competitions.id
                WHERE competitions.id = %s
            """, (self.selected_competition_id,))
            rows = cursor.fetchall()
            conn.close()

            for row in self.team_table.get_children():
                self.team_table.delete(row)
            for row in rows:
                self.team_table.insert("", "end", values=row)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    def add_team(self):
        """Add a new team to the database."""
        def submit_team():
            team_name = team_name_input.get().strip()
            selected_comp = competition_dropdown.get()

            if not team_name or not selected_comp:
                messagebox.showwarning("Input Error", "Team Name and Competition are required.")
                return

            comp_id = int(selected_comp.split(" - ")[0])  # Extract competition ID

            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO teams (name, comp_id, created_at, score) VALUES (%s, %s, NOW(), 0)", (team_name, comp_id))
                conn.commit()
                conn.close()
                team_window.destroy()
                self.fetch_teams()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        team_window = tk.Toplevel(self)
        team_window.title("Add Team")

        tk.Label(team_window, text="Team Name:").grid(row=0, column=0, sticky="w")
        team_name_input = tk.Entry(team_window)
        team_name_input.grid(row=0, column=1)

        tk.Label(team_window, text="Competition:").grid(row=1, column=0, sticky="w")
        competition_dropdown = ttk.Combobox(team_window, state="readonly", width=40)
        competition_dropdown.grid(row=1, column=1)

        conn = connect_db(self.db_credentials)
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM competitions")
            competitions = cursor.fetchall()
            conn.close()
            competition_dropdown["values"] = [f"{comp[0]} - {comp[1]}" for comp in competitions]

        submit_btn = tk.Button(team_window, text="Submit", command=submit_team)
        submit_btn.grid(row=2, column=0, columnspan=2)

    def fetch_scores(self):
        """Fetch and display scores for the selected competition."""
        conn = connect_db(self.db_credentials)
        if conn is None or self.selected_competition_id is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COALESCE(teams.name, 'N/A') AS team_name,
                    COALESCE(players.name, 'N/A') AS player_name,
                    games.name AS game_name,
                    competitions.name AS competition_name,
                    total_scores_log.points,
                    total_scores_log.comment
                FROM total_scores_log
                LEFT JOIN teams ON total_scores_log.team_id = teams.id
                LEFT JOIN players ON total_scores_log.player_id = players.id
                JOIN games ON total_scores_log.game_id = games.id
                JOIN competitions ON games.comp_id = competitions.id
                WHERE competitions.id = %s
            """, (self.selected_competition_id,))
            rows = cursor.fetchall()
            conn.close()

            for row in self.score_table.get_children():
                self.score_table.delete(row)
            for row in rows:
                self.score_table.insert("", "end", values=row)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    def fetch_games(self):
        """Fetch and display games for the selected competition."""
        conn = connect_db(self.db_credentials)
        if conn is None or self.selected_competition_id is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT games.id, competitions.name AS competition_name, games.name, 
                       games.team_game, games.date_played, games.created_at
                FROM games
                JOIN competitions ON games.comp_id = competitions.id
                WHERE competitions.id = %s
            """, (self.selected_competition_id,))
            rows = cursor.fetchall()
            conn.close()

            for row in self.games_table.get_children():
                self.games_table.delete(row)
            for row in rows:
                row = list(row)
                row[3] = "Yes" if row[3] else "No"  # Convert team_game boolean to "Yes" or "No"
                self.games_table.insert("", "end", values=row)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    def fetch_players(self):
        """Fetch and display players for the selected competition."""
        conn = connect_db(self.db_credentials)
        if conn is None or self.selected_competition_id is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT players.id, teams.name AS team_name, players.name AS player_name, players.created_at
                FROM players
                LEFT JOIN teams ON players.team_id = teams.id
                WHERE teams.comp_id = %s
            """, (self.selected_competition_id,))
            rows = cursor.fetchall()
            conn.close()

            for row in self.players_table.get_children():
                self.players_table.delete(row)
            for row in rows:
                self.players_table.insert("", "end", values=row)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    def fetch_competitions(self):
        """Fetch and display all competitions."""
        conn = connect_db(self.db_credentials)
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, start_date, end_date, created_at
                FROM competitions
            """)
            rows = cursor.fetchall()
            conn.close()

            for row in self.competitions_table.get_children():
                self.competitions_table.delete(row)
            for row in rows:
                self.competitions_table.insert("", "end", values=row)
        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", str(e))

    def add_score(self):
        """Add a new score to the database."""
        def update_team_game_status(event):
            game_name = game_dropdown.get()
            if not game_name:
                return

            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT team_game FROM games WHERE name = %s", (game_name,))
                team_game = cursor.fetchone()
                conn.close()
                if team_game and team_game[0]:
                    team_game_var.set(True)
                    update_team_or_player_dropdown(is_team_game=True)
                else:
                    team_game_var.set(False)
                    update_team_or_player_dropdown(is_team_game=False)
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def update_team_or_player_dropdown(is_team_game):
            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                if is_team_game:
                    cursor.execute("SELECT id, name FROM teams")
                    items = [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]
                else:
                    cursor.execute("""
                        SELECT players.id, players.name, teams.name AS team_name
                        FROM players
                        LEFT JOIN teams ON players.team_id = teams.id
                    """)
                    items = [f"{row[0]} - {row[1]} (Team: {row[2]})" for row in cursor.fetchall()]
                conn.close()
                team_or_player_dropdown["values"] = items
                team_or_player_dropdown.set("")  # Clear selection
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        def submit_score():
            game_name = game_dropdown.get()
            points = points_input.get().strip()
            comment = comment_input.get().strip()
            selected_item = team_or_player_dropdown.get()
            is_team_game = team_game_var.get()

            if not game_name or not points or not selected_item:
                messagebox.showwarning("Input Error", "Game, Points, and Team/Player selection are required.")
                return

            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM games WHERE name = %s", (game_name,))
                game_id = cursor.fetchone()
                if not game_id:
                    messagebox.showerror("Input Error", "Invalid game selected.")
                    return

                selected_id = selected_item.split(" - ")[0]  # Extract ID from dropdown value
                if is_team_game:
                    cursor.execute(
                        "INSERT INTO team_scores_log (team_id, game_id, points, comment, created_at) VALUES (%s, %s, %s, %s, NOW())",
                        (selected_id, game_id[0], points, comment)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO player_scores_log (player_id, game_id, points, comment, created_at) VALUES (%s, %s, %s, %s, NOW())",
                        (selected_id, game_id[0], points, comment)
                    )
                conn.commit()
                conn.close()
                score_window.destroy()
                self.fetch_scores()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        score_window = tk.Toplevel(self)
        score_window.title("Add Score")

        tk.Label(score_window, text="Game:").grid(row=0, column=0, sticky="w")
        game_dropdown = ttk.Combobox(score_window, state="readonly", width=40)  # Increased width
        game_dropdown.grid(row=0, column=1)

        conn = connect_db(self.db_credentials)
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM games")
            games = [row[0] for row in cursor.fetchall()]
            conn.close()
            game_dropdown["values"] = games
            game_dropdown.bind("<<ComboboxSelected>>", update_team_game_status)

        tk.Label(score_window, text="Points:").grid(row=1, column=0, sticky="w")
        points_input = tk.Entry(score_window)
        points_input.grid(row=1, column=1)

        tk.Label(score_window, text="Comment:").grid(row=2, column=0, sticky="w")
        comment_input = tk.Entry(score_window)
        comment_input.grid(row=2, column=1)

        team_game_var = tk.BooleanVar()
        tk.Checkbutton(score_window, text="Team Game", variable=team_game_var, state="disabled").grid(row=3, column=0, columnspan=2)

        tk.Label(score_window, text="Team/Player:").grid(row=4, column=0, sticky="w")
        team_or_player_dropdown = ttk.Combobox(score_window, state="readonly", width=40)  # Increased width
        team_or_player_dropdown.grid(row=4, column=1)

        submit_btn = tk.Button(score_window, text="Submit", command=submit_score)
        submit_btn.grid(row=5, column=0, columnspan=2)

    def add_game(self):
        """Add a new game to the database."""
        def submit_game():
            comp_name = comp_dropdown.get()
            name = name_input.get().strip()
            team_game = team_game_var.get()
            date_played = date_played_input.get().strip()

            if not comp_name or not name:
                messagebox.showwarning("Input Error", "Competition and Game Name are required.")
                return

            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM competitions WHERE name = %s", (comp_name,))
                comp_id = cursor.fetchone()
                if not comp_id:
                    messagebox.showerror("Input Error", "Invalid competition selected.")
                    return
                cursor.execute(
                    "INSERT INTO games (comp_id, name, team_game, date_played, created_at) VALUES (%s, %s, %s, %s, NOW())",
                    (comp_id[0], name, team_game, date_played)
                )
                conn.commit()
                conn.close()
                game_window.destroy()
                self.fetch_games()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        game_window = tk.Toplevel(self)
        game_window.title("Add Game")

        tk.Label(game_window, text="Competition:").grid(row=0, column=0, sticky="w")
        comp_dropdown = ttk.Combobox(game_window, state="readonly")
        comp_dropdown.grid(row=0, column=1)

        conn = connect_db(self.db_credentials)
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM competitions")
            competitions = [row[0] for row in cursor.fetchall()]
            conn.close()
            comp_dropdown["values"] = competitions

        tk.Label(game_window, text="Game Name:").grid(row=1, column=0, sticky="w")
        name_input = tk.Entry(game_window)
        name_input.grid(row=1, column=1)

        team_game_var = tk.BooleanVar()
        tk.Checkbutton(game_window, text="Team Game", variable=team_game_var).grid(row=2, column=0, columnspan=2)

        tk.Label(game_window, text="Date Played (YYYY-MM-DD):").grid(row=3, column=0, sticky="w")
        date_played_input = tk.Entry(game_window)
        date_played_input.grid(row=3, column=1)

        submit_btn = tk.Button(game_window, text="Submit", command=submit_game)
        submit_btn.grid(row=4, column=0, columnspan=2)

    def add_player(self):
        """Add a new player to the database."""
        def submit_player():
            team_name = team_dropdown.get()
            player_name = player_name_input.get().strip()

            if not team_name or not player_name:
                messagebox.showwarning("Input Error", "Team and Player Name are required.")
                return

            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM teams WHERE name = %s", (team_name,))
                team_id = cursor.fetchone()
                if not team_id:
                    messagebox.showerror("Input Error", "Invalid team selected.")
                    return
                cursor.execute("INSERT INTO players (team_id, name, created_at) VALUES (%s, %s, NOW())", (team_id[0], player_name))
                conn.commit()
                conn.close()
                player_window.destroy()
                self.fetch_players()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        player_window = tk.Toplevel(self)
        player_window.title("Add Player")

        tk.Label(player_window, text="Team:").grid(row=0, column=0, sticky="w")
        team_dropdown = ttk.Combobox(player_window, state="readonly")
        team_dropdown.grid(row=0, column=1)

        conn = connect_db(self.db_credentials)
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM teams")
            teams = [row[0] for row in cursor.fetchall()]
            conn.close()
            team_dropdown["values"] = teams

        tk.Label(player_window, text="Player Name:").grid(row=1, column=0, sticky="w")
        player_name_input = tk.Entry(player_window)
        player_name_input.grid(row=1, column=1)

        submit_btn = tk.Button(player_window, text="Submit", command=submit_player)
        submit_btn.grid(row=2, column=0, columnspan=2)

    def add_competition(self):
        """Add a new competition to the database."""
        def submit_competition():
            name = name_input.get().strip()
            start_date = start_date_input.get().strip()
            end_date = end_date_input.get().strip()

            if not name or not start_date or not end_date:
                messagebox.showwarning("Input Error", "All fields are required.")
                return

            conn = connect_db(self.db_credentials)
            if conn is None:
                return
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO competitions (name, start_date, end_date, created_at) VALUES (%s, %s, %s, NOW())",
                    (name, start_date, end_date)
                )
                conn.commit()
                conn.close()
                competition_window.destroy()
                self.refresh_competition_list()  # Refresh the competition list
                self.fetch_competitions()
            except mysql.connector.Error as e:
                messagebox.showerror("Database Error", str(e))

        competition_window = tk.Toplevel(self)
        competition_window.title("Add Competition")

        tk.Label(competition_window, text="Name:").grid(row=0, column=0, sticky="w")
        name_input = tk.Entry(competition_window)
        name_input.grid(row=0, column=1)

        tk.Label(competition_window, text="Start Date (YYYY-MM-DD):").grid(row=1, column=0, sticky="w")
        start_date_input = tk.Entry(competition_window)
        start_date_input.grid(row=1, column=1)

        tk.Label(competition_window, text="End Date (YYYY-MM-DD):").grid(row=2, column=0, sticky="w")
        end_date_input = tk.Entry(competition_window)
        end_date_input.grid(row=2, column=1)

        submit_btn = tk.Button(competition_window, text="Submit", command=submit_competition)
        submit_btn.grid(row=3, column=0, columnspan=2)

if __name__ == "__main__":
    while True:  # Keep showing the login dialog until valid credentials are provided or the user cancels
        login_dialog = LoginDialog(None)  # Pass None as the parent for the dialog
        if login_dialog.credentials:
            app = CompetitionDBApp(login_dialog.credentials)
            app.mainloop()
            break
        elif login_dialog.credentials is None and not messagebox.askretrycancel(
            "Login Failed", "No valid credentials provided. Do you want to retry?"
        ):
            exit()
