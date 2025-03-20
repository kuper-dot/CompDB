from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
import mysql.connector

# Database Connection
def connect_db():
    return mysql.connector.connect(
        host="192.168.0.113",
        user="root",
        password="yourpassword",
        database="compDB",
        port=3306
    )

# Main Kivy UI
class CompetitionDBApp(TabbedPanel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # --- Teams Tab ---
        self.teams_tab = TabbedPanelItem(text="Teams")
        self.teams_layout = BoxLayout(orientation="vertical")
        
        # Team input field
        self.team_input = TextInput(hint_text="Enter team name", size_hint=(1, 0.1))
        self.teams_layout.add_widget(self.team_input)
        
        # Add Team Button
        self.add_team_btn = Button(text="Add Team", size_hint=(1, 0.1))
        self.add_team_btn.bind(on_press=self.add_team)
        self.teams_layout.add_widget(self.add_team_btn)

        # Load Teams Button
        self.load_team_btn = Button(text="Load Teams", size_hint=(1, 0.1))
        self.load_team_btn.bind(on_press=self.fetch_teams)
        self.teams_layout.add_widget(self.load_team_btn)

        # Teams Display Grid
        self.teams_grid = GridLayout(cols=4, size_hint=(1, 0.8))
        self.teams_layout.add_widget(self.teams_grid)

        self.teams_tab.add_widget(self.teams_layout)
        self.add_widget(self.teams_tab)

        # --- Scores Tab ---
        self.scores_tab = TabbedPanelItem(text="Scores")
        self.scores_layout = BoxLayout(orientation="vertical")

        # Load Scores Button
        self.load_scores_btn = Button(text="Load Scores", size_hint=(1, 0.1))
        self.load_scores_btn.bind(on_press=self.fetch_scores)
        self.scores_layout.add_widget(self.load_scores_btn)

        # Scores Display Grid
        self.scores_grid = GridLayout(cols=6, size_hint=(1, 0.9))
        self.scores_layout.add_widget(self.scores_grid)

        self.scores_tab.add_widget(self.scores_layout)
        self.add_widget(self.scores_tab)

    def fetch_teams(self, instance):
        self.teams_grid.clear_widgets()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, comp_id, score FROM teams")
        teams = cursor.fetchall()
        conn.close()

        # Add column headers
        headers = ["ID", "Name", "Comp ID", "Score"]
        for header in headers:
            self.teams_grid.add_widget(Label(text=header, bold=True))

        # Add team data
        for team in teams:
            for data in team:
                self.teams_grid.add_widget(Label(text=str(data)))

    def add_team(self, instance):
        team_name = self.team_input.text.strip()
        if not team_name:
            return

        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (name, comp_id, created_at, score) VALUES (%s, 1, NOW(), 0)", (team_name,))
        conn.commit()
        conn.close()
        self.fetch_teams(instance)

    def fetch_scores(self, instance):
        self.scores_grid.clear_widgets()
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT team_id, player_id, game_id, points, created_at, comment FROM total_scores_log")
        scores = cursor.fetchall()
        conn.close()

        # Add column headers
        headers = ["Team ID", "Player ID", "Game ID", "Points", "Created At", "Comment"]
        for header in headers:
            self.scores_grid.add_widget(Label(text=header, bold=True))

        # Add score data
        for score in scores:
            for data in score:
                self.scores_grid.add_widget(Label(text=str(data)))

class CompetitionApp(App):
    def build(self):
        return CompetitionDBApp()

if __name__ == "__main__":
    CompetitionApp().run()
