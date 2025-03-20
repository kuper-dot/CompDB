from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget, QLabel, QMessageBox
import sys
import mysql.connector

def connect_db():
    try:
        return mysql.connector.connect(
            host="192.168.0.113",
            port=3306,
            user="test",
            password="123",
            database="compDB"
        )
    except mysql.connector.Error as e:
        QMessageBox.critical(None, "Database Connection Error", str(e))
        return None

class CompetitionDBApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Competition DB Manager")
        self.setGeometry(100, 100, 800, 500)
        
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.team_tab = QWidget()
        self.score_tab = QWidget()
        
        self.tabs.addTab(self.team_tab, "Teams")
        self.tabs.addTab(self.score_tab, "Scores")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        self.init_team_tab()
        self.init_score_tab()
    
    def init_team_tab(self):
        layout = QVBoxLayout()
        
        self.team_input = QLineEdit()
        self.team_input.setPlaceholderText("Enter team name")
        layout.addWidget(self.team_input)
        
        self.add_team_btn = QPushButton("Add Team")
        self.add_team_btn.clicked.connect(self.add_team)
        layout.addWidget(self.add_team_btn)
        
        self.load_team_btn = QPushButton("Load Teams")
        self.load_team_btn.clicked.connect(self.fetch_teams)
        layout.addWidget(self.load_team_btn)
        
        self.team_table = QTableWidget()
        self.team_table.setColumnCount(4)
        self.team_table.setHorizontalHeaderLabels(["ID", "Name", "Comp ID", "Score"])
        layout.addWidget(self.team_table)
        
        self.team_tab.setLayout(layout)
    
    def init_score_tab(self):
        layout = QVBoxLayout()
        
        self.load_scores_btn = QPushButton("Load Scores")
        self.load_scores_btn.clicked.connect(self.fetch_scores)
        layout.addWidget(self.load_scores_btn)
        
        self.score_table = QTableWidget()
        self.score_table.setColumnCount(6)
        self.score_table.setHorizontalHeaderLabels(["Team ID", "Player ID", "Game ID", "Points", "Created At", "Comment"])
        layout.addWidget(self.score_table)
        
        self.score_tab.setLayout(layout)
    
    def fetch_teams(self):
        conn = connect_db()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, comp_id, score FROM teams")
            rows = cursor.fetchall()
            conn.close()
            
            self.team_table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, data in enumerate(row):
                    self.team_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
    
    def add_team(self):
        team_name = self.team_input.text().strip()
        if not team_name:
            QMessageBox.warning(self, "Input Error", "Please enter a team name.")
            return
        
        conn = connect_db()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO teams (name, comp_id, created_at, score) VALUES (%s, 1, NOW(), 0)", (team_name,))
            conn.commit()
            conn.close()
            self.fetch_teams()
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))
    
    def fetch_scores(self):
        conn = connect_db()
        if conn is None:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT team_id, player_id, game_id, points, created_at, comment FROM total_scores_logq")
            rows = cursor.fetchall()
            conn.close()
            
            self.score_table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, data in enumerate(row):
                    self.score_table.setItem(row_idx, col_idx, QTableWidgetItem(str(data)))
        except mysql.connector.Error as e:
            QMessageBox.critical(self, "Database Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompetitionDBApp()
    window.show()
    sys.exit(app.exec())
