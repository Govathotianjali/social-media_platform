import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_NAME = "social_media.db"


@app.after_request
def apply_cors_policies(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def bootstrap_database():
    with sqlite3.connect(DB_NAME) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL
            )
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(username) REFERENCES users(username)
            )
        """
        )
    print("Database framework synchronized successfully.")


@app.route("/api/register", methods=["POST"])
def register_user():
    data = request.get_json() or {}
    username = data.get("username", "").strip().lower()
    display_name = data.get("display_name", "").strip()

    if not username or not display_name:
        return (
            jsonify({"status": "error", "message": "All fields are required."}),
            400,
        )

    try:
        with sqlite3.connect(DB_NAME) as connection:
            connection.execute(
                "INSERT INTO users (username, display_name) VALUES (?, ?)",
                (username, display_name),
            )
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Account created successfully!",
                }
            ),
            201,
        )
    except sqlite3.IntegrityError:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Username handle is already taken.",
                }
            ),
            400,
        )


@app.route("/api/posts", methods=["POST", "GET"])
def handle_posts():
    if request.method == "POST":
        data = request.get_json() or {}
        username = data.get("username", "").strip().lower()
        content = data.get("content", "").strip()

        if not username or not content:
            return (
                jsonify(
                    {"status": "error", "message": "Content cannot be empty."}
                ),
                400,
            )

        timestamp = datetime.now().strftime("%I:%M %p • %b %d, %Y")
        with sqlite3.connect(DB_NAME) as connection:
            connection.execute(
                "INSERT INTO posts (username, content, timestamp) VALUES (?, ?, ?)",
                (username, content, timestamp),
            )
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Post published to the feed!",
                }
            ),
            201,
        )

    with sqlite3.connect(DB_NAME) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT posts.content, posts.timestamp, posts.username, users.display_name 
            FROM posts 
            INNER JOIN users ON posts.username = users.username 
            ORDER BY posts.id DESC
        """
        )
        feed_array = [dict(row) for row in cursor.fetchall()]

    return jsonify(feed_array), 200


if __name__ == "__main__":
    bootstrap_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
