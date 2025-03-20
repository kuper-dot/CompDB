const { app, BrowserWindow } = require("electron");
const path = require("path");
const express = require("express");
const cors = require("cors");
const mysql = require("mysql2");

// Create Express backend
const backend = express();
backend.use(cors());
backend.use(express.json());

// MySQL Connection
const db = mysql.createConnection({
    host: "192.168.0.113",
    user: "test",
    password: "123",
    database: "compDB",
    port: 3306
});

db.connect(err => {
    if (err) {
        console.error("Database connection error:", err);
    } else {
        console.log("Connected to MySQL");
    }
});

// API Endpoint to Fetch Teams
backend.get("/teams", (req, res) => {
    db.query("SELECT id, name, comp_id, score FROM teams", (err, results) => {
        if (err) return res.status(500).send(err);
        res.json(results);
    });
});

// API Endpoint to Add a Team
backend.post("/add-team", (req, res) => {
    const { name } = req.body;
    if (!name) return res.status(400).send("Team name required");

    db.query("INSERT INTO teams (name, comp_id, created_at, score) VALUES (?, 1, NOW(), 0)", [name], (err, results) => {
        if (err) return res.status(500).send(err);
        res.json({ message: "Team added", id: results.insertId });
    });
});

// Start Backend Server
backend.listen(3000, () => console.log("Backend running on http://localhost:3000"));

// Electron Main Window
let mainWindow;
app.whenReady().then(() => {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true
        }
    });
    mainWindow.loadFile("index.html");
});
