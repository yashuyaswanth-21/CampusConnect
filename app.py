
import os
import sqlite3
from functools import wraps
from pathlib import Path
from datetime import datetime

import click
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, abort
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "development-key-change-before-deployment"
)

DB_PATH = Path(__file__).with_name("campusconnect.db")


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect_db() as conn:
        # Existing campus posts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                location TEXT DEFAULT '',
                contact TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)

        # New accounts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student'
                    CHECK (role IN ('student', 'admin')),
                created_at TEXT NOT NULL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM posts"
        ).fetchone()[0]

        if count == 0:
            now = datetime.now().strftime("%d %b %Y")
            samples = [
                (
                    "Notice",
                    "Internal assessment schedule released",
                    "Check with your department for the latest internal assessment timetable.",
                    "Academic Block",
                    "College Office",
                    now
                ),
                (
                    "Event",
                    "Campus Innovation Day",
                    "Showcase your projects, prototypes, and creative ideas. All departments are welcome.",
                    "Main Auditorium",
                    "Student Council",
                    now
                ),
                (
                    "Lost & Found",
                    "Found: Blue water bottle",
                    "A blue water bottle was found near the library entrance.",
                    "Central Library",
                    "Campus Help Desk",
                    now
                ),
            ]

            conn.executemany("""
                INSERT INTO posts
                (category, title, description, location, contact, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, samples)


# Authentication and permission helpers

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            abort(403)

        return view(*args, **kwargs)
    return wrapped_view


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if len(username) > 40 or len(email) > 120:
            flash("Username or email is too long.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("The passwords do not match.", "error")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        try:
            with connect_db() as conn:
                conn.execute("""
                    INSERT INTO users
                    (username, email, password_hash, role, created_at)
                    VALUES (?, ?, ?, 'student', ?)
                """, (
                    username,
                    email,
                    password_hash,
                    datetime.now().strftime("%d %b %Y")
                ))
        except sqlite3.IntegrityError:
            flash("That username or email is already registered.", "error")
            return redirect(url_for("register"))

        flash("Account created! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with connect_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()

        if user is None or not check_password_hash(
            user["password_hash"], password
        ):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        flash(f"Welcome, {user['username']}!", "success")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have logged out.", "success")
    return redirect(url_for("index"))


# Main campus dashboard

@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "All")

    allowed_categories = {"All", "Notice", "Event", "Lost & Found"}
    if category not in allowed_categories:
        category = "All"

    with connect_db() as conn:
        sql = "SELECT * FROM posts"
        conditions = []
        params = []

        if category != "All":
            conditions.append("category = ?")
            params.append(category)

        if search:
            conditions.append("""
                (title LIKE ? OR description LIKE ?
                OR location LIKE ? OR contact LIKE ?)
            """)
            params.extend([f"%{search}%"] * 4)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY id DESC"
        rows = conn.execute(sql, params).fetchall()

        counts = {
            "all": conn.execute(
                "SELECT COUNT(*) FROM posts"
            ).fetchone()[0],
            "notice": conn.execute(
                "SELECT COUNT(*) FROM posts WHERE category='Notice'"
            ).fetchone()[0],
            "event": conn.execute(
                "SELECT COUNT(*) FROM posts WHERE category='Event'"
            ).fetchone()[0],
            "lost": conn.execute(
                "SELECT COUNT(*) FROM posts WHERE category='Lost & Found'"
            ).fetchone()[0],
        }

    return render_template(
        "index.html",
        posts=rows,
        search=search,
        category=category,
        counts=counts
    )
@app.route("/admin")
@admin_required
def admin_dashboard():
    with connect_db() as conn:
        total_users = conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        total_posts = conn.execute(
            "SELECT COUNT(*) FROM posts"
        ).fetchone()[0]

        total_students = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'student'"
        ).fetchone()[0]

        total_admins = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin'"
        ).fetchone()[0]

        category_counts = conn.execute("""
            SELECT category, COUNT(*) AS total
            FROM posts
            GROUP BY category
            ORDER BY category
        """).fetchall()

        users = conn.execute("""
            SELECT id, username, email, role, created_at
            FROM users
            ORDER BY id DESC
        """).fetchall()

        recent_posts = conn.execute("""
            SELECT id, title, category, location, created_at
            FROM posts
            ORDER BY id DESC
            LIMIT 10
        """).fetchall()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_posts=total_posts,
        total_students=total_students,
        total_admins=total_admins,
        category_counts=category_counts,
        users=users,
        recent_posts=recent_posts
    )

@app.route("/add", methods=["POST"])
@login_required
def add_post():
    category = request.form.get("category", "").strip()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    location = request.form.get("location", "").strip()
    contact = request.form.get("contact", "").strip()

    allowed = {"Notice", "Event", "Lost & Found"}

    if (
        category not in allowed
        or not title
        or not description
        or len(title) > 100
        or len(description) > 600
        or len(location) > 100
        or len(contact) > 100
    ):
        flash("Please check your post details.", "error")
        return redirect(url_for("index"))

    created_at = datetime.now().strftime("%d %b %Y")

    with connect_db() as conn:
        conn.execute("""
            INSERT INTO posts
            (category, title, description, location, contact, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category, title, description, location, contact, created_at))

    flash("Your post was added successfully!", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:post_id>", methods=["POST"])
@admin_required
def delete_post(post_id):
    with connect_db() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))

    flash("Post deleted.", "success")
    return redirect(url_for("index"))


# Run this once from the terminal to create an administrator.
@app.cli.command("create-admin")
def create_admin():
    """Create an administrator account interactively."""
    init_db()

    username = click.prompt("Admin username").strip()
    email = click.prompt("Admin email").strip().lower()
    password = click.prompt(
        "Admin password", hide_input=True, confirmation_prompt=True
    )

    if not username or not email or len(password) < 8:
        click.echo("Username/email cannot be empty; password needs 8 characters.")
        return

    try:
        with connect_db() as conn:
            conn.execute("""
                INSERT INTO users
                (username, email, password_hash, role, created_at)
                VALUES (?, ?, ?, 'admin', ?)
            """, (
                username,
                email,
                generate_password_hash(password),
                datetime.now().strftime("%d %b %Y")
            ))
        click.echo("Administrator account created successfully.")
    except sqlite3.IntegrityError:
        click.echo("That username or email is already registered.")


@app.errorhandler(403)
def forbidden(error):
    return (
        "<h1>403 - Access denied</h1>"
        "<p>Only administrators can perform this action.</p>"
        '<p><a href="/">Return to CampusConnect</a></p>',
        403
    )


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
