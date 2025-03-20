import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host="192.168.0.113",
        port=3306,
        user="test",
        password="123",
        database="compDB"
    )

def fetch_teams():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, comp_id, score FROM teams")
        rows = cursor.fetchall()
        conn.close()

        for i in team_table.get_children():
            team_table.delete(i)

        for row in rows:
            team_table.insert("", "end", values=row)
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))

def add_team():
    team_name = team_entry.get()
    if not team_name:
        messagebox.showwarning("Input Error", "Please enter a team name")
        return
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teams (name, comp_id, created_at, score) VALUES (%s, 1, NOW(), 0)", (team_name,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Team added successfully!")
        fetch_teams()
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))

def fetch_scores():
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT team_id, player_id, game_id, points, created_at, comment FROM total_scores_log")
        rows = cursor.fetchall()
        conn.close()

        for i in score_table.get_children():
            score_table.delete(i)

        for row in rows:
            score_table.insert("", "end", values=row)
    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))

root = tk.Tk()
root.title("Competition DB Manager")
root.geometry("800x500")

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

# Teams Tab
team_frame = ttk.Frame(notebook)
notebook.add(team_frame, text="Teams")

tk.Label(team_frame, text="Team Name:").pack()
team_entry = tk.Entry(team_frame)
team_entry.pack()

tk.Button(team_frame, text="Add Team", command=add_team).pack()
tk.Button(team_frame, text="Load Teams", command=fetch_teams).pack()

team_columns = ("id", "name", "comp_id", "score")
team_table = ttk.Treeview(team_frame, columns=team_columns, show="headings")

for col in team_columns:
    team_table.heading(col, text=col.upper())
    team_table.column(col, width=100, anchor="center")

team_table.pack(fill="both", expand=True)

# Scores Tab
score_frame = ttk.Frame(notebook)
notebook.add(score_frame, text="Scores")

tk.Button(score_frame, text="Load Scores", command=fetch_scores).pack()

score_columns = ("team_id", "player_id", "game_id", "points", "created_at", "comment")
score_table = ttk.Treeview(score_frame, columns=score_columns, show="headings")

for col in score_columns:
    score_table.heading(col, text=col.upper())
    score_table.column(col, width=120, anchor="center")

score_table.pack(fill="both", expand=True)

root.mainloop()
