from flask import Flask, render_template, request, redirect, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-secret-key"
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            role TEXT,
            verified INTEGER DEFAULT 1,
            otp TEXT
        )
    """)

    # Classrooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    # Subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

    # Timetable table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            classroom_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            time TEXT NOT NULL,
            FOREIGN KEY (classroom_id) REFERENCES classrooms(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# AUTHENTICATION
# ============================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter username and password.")
            return render_template("index.html")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session["user"] = username
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            return redirect("/dashboard")

        flash("Invalid username or password.")

    return render_template("index.html")


# ============================================================
# SIGNUP
# ============================================================

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "student").strip()

        if not username or not password:
            flash("Username and password are required.")
            return render_template("signup.html")

        password_hash = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (username, password, email, role)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                password_hash,
                email,
                role
            ))

            conn.commit()

            flash("Account created successfully! Login now.")
            return redirect("/")

        except sqlite3.IntegrityError:

            flash("Username already exists.")

        finally:

            conn.close()

    return render_template("signup.html")


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    return render_template("dashboard.html")


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ============================================================
# CLASSROOM API
# ============================================================

@app.route("/api/classrooms", methods=["GET", "POST"])
def classrooms():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    try:

        if request.method == "POST":

            data = request.get_json(silent=True) or {}

            name = data.get("name", "").strip()

            if not name:
                return jsonify({
                    "error": "Classroom name is required"
                }), 400

            cursor.execute(
                "INSERT INTO classrooms (name) VALUES (?)",
                (name,)
            )

            conn.commit()

            return jsonify({
                "message": "Classroom added successfully"
            }), 201

        rows = cursor.execute(
            "SELECT * FROM classrooms ORDER BY id"
        ).fetchall()

        return jsonify([
            dict(row) for row in rows
        ])

    finally:

        conn.close()


# ============================================================
# SUBJECT API
# ============================================================

@app.route("/api/subjects", methods=["GET", "POST"])
def subjects():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    try:

        if request.method == "POST":

            data = request.get_json(silent=True) or {}

            name = data.get("name", "").strip()

            if not name:
                return jsonify({
                    "error": "Subject name is required"
                }), 400

            cursor.execute(
                "INSERT INTO subjects (name) VALUES (?)",
                (name,)
            )

            conn.commit()

            return jsonify({
                "message": "Subject added successfully"
            }), 201

        rows = cursor.execute(
            "SELECT * FROM subjects ORDER BY id"
        ).fetchall()

        return jsonify([
            dict(row) for row in rows
        ])

    finally:

        conn.close()


# ============================================================
# TIMETABLE API
# ============================================================

@app.route("/api/timetable", methods=["GET", "POST"])
def timetable():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    try:

        # ----------------------------------------------------
        # ADD TIMETABLE ENTRY
        # ----------------------------------------------------

        if request.method == "POST":

            data = request.get_json(silent=True) or {}

            classroom_id = data.get("classroom_id")
            subject_id = data.get("subject_id")
            day = data.get("day", "").strip()
            time = data.get("time", "").strip()

            if not classroom_id or not subject_id or not day or not time:

                return jsonify({
                    "error": "All timetable fields are required"
                }), 400

            # Check classroom
            classroom = cursor.execute(
                "SELECT * FROM classrooms WHERE id = ?",
                (classroom_id,)
            ).fetchone()

            if not classroom:

                return jsonify({
                    "error": "Classroom does not exist"
                }), 404

            # Check subject
            subject = cursor.execute(
                "SELECT * FROM subjects WHERE id = ?",
                (subject_id,)
            ).fetchone()

            if not subject:

                return jsonify({
                    "error": "Subject does not exist"
                }), 404

            # Check if classroom already booked
            existing = cursor.execute("""
                SELECT *
                FROM timetable
                WHERE classroom_id = ?
                AND day = ?
                AND time = ?
            """, (
                classroom_id,
                day,
                time
            )).fetchone()

            if existing:

                return jsonify({
                    "error": "Classroom is already booked at this time"
                }), 400

            # Insert timetable
            cursor.execute("""
                INSERT INTO timetable
                (classroom_id, subject_id, day, time)
                VALUES (?, ?, ?, ?)
            """, (
                classroom_id,
                subject_id,
                day,
                time
            ))

            conn.commit()

            return jsonify({
                "message": "Timetable scheduled successfully"
            }), 201

        # ----------------------------------------------------
        # GET TIMETABLE
        # ----------------------------------------------------

        rows = cursor.execute("""
            SELECT
                t.id,
                t.classroom_id,
                t.subject_id,
                c.name AS classroom,
                s.name AS subject,
                t.day,
                t.time
            FROM timetable t
            JOIN classrooms c
                ON t.classroom_id = c.id
            JOIN subjects s
                ON t.subject_id = s.id
            ORDER BY
                t.classroom_id,
                t.day,
                t.time
        """).fetchall()

        return jsonify([
            dict(row) for row in rows
        ])

    finally:

        conn.close()


# ============================================================
# AUTOMATIC / AI TIMETABLE GENERATOR
# ============================================================

@app.route("/api/auto_schedule", methods=["POST"])
def auto_schedule():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}

    classroom_id = data.get("classroom_id")
    days = data.get("days")
    times = data.get("times")
    subject_ids = data.get("subjects")

    if not classroom_id:
        return jsonify({
            "error": "Classroom ID is required"
        }), 400

    if not days or not times or not subject_ids:
        return jsonify({
            "error": "Days, times and subjects are required"
        }), 400

    conn = get_db()
    cursor = conn.cursor()

    try:

        # Check classroom
        classroom = cursor.execute(
            "SELECT * FROM classrooms WHERE id = ?",
            (classroom_id,)
        ).fetchone()

        if not classroom:

            return jsonify({
                "error": "Classroom does not exist"
            }), 404

        # Clear old timetable for this classroom
        cursor.execute(
            "DELETE FROM timetable WHERE classroom_id = ?",
            (classroom_id,)
        )

        for day in days:

            used_subjects = []

            for time in times:

                # Subjects not already used on this day
                available = [
                    subject_id
                    for subject_id in subject_ids
                    if subject_id not in used_subjects
                ]

                # If all subjects were already used,
                # allow them again
                if not available:
                    available = subject_ids

                subject_id = random.choice(available)

                used_subjects.append(subject_id)

                cursor.execute("""
                    INSERT INTO timetable
                    (classroom_id, subject_id, day, time)
                    VALUES (?, ?, ?, ?)
                """, (
                    classroom_id,
                    subject_id,
                    day.strip(),
                    time.strip()
                ))

        conn.commit()

        return jsonify({
            "message": "AI timetable generated successfully"
        })

    finally:

        conn.close()


# ============================================================
# AUTOMATIC TIMETABLE GENERATOR FOR ALL CLASSROOMS
# ============================================================

@app.route("/api/auto_generate", methods=["POST"])
def auto_generate():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cursor = conn.cursor()

    try:

        # Get all classrooms
        classrooms = cursor.execute(
            "SELECT * FROM classrooms"
        ).fetchall()

        # Get all subjects
        subjects = cursor.execute(
            "SELECT * FROM subjects"
        ).fetchall()

        if not classrooms:

            return jsonify({
                "error": "Add classrooms first"
            }), 400

        if not subjects:

            return jsonify({
                "error": "Add subjects first"
            }), 400

        # Days
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday"
        ]

        # Time slots
        times = [
            "10:00",
            "11:00",
            "12:00"
        ]

        # Clear previous timetable
        cursor.execute("DELETE FROM timetable")

        # Generate timetable
        for classroom in classrooms:

            for day in days:

                used_subjects = []

                for time in times:

                    # Subjects not used today
                    available = [
                        subject
                        for subject in subjects
                        if subject["id"] not in used_subjects
                    ]

                    # If there are no unused subjects,
                    # reset the list
                    if not available:
                        available = subjects

                    # Select random subject
                    subject = random.choice(available)

                    used_subjects.append(subject["id"])

                    cursor.execute("""
                        INSERT INTO timetable
                        (classroom_id, subject_id, day, time)
                        VALUES (?, ?, ?, ?)
                    """, (
                        classroom["id"],
                        subject["id"],
                        day,
                        time
                    ))

        conn.commit()

        return jsonify({
            "message": "AI timetable generated automatically"
        })

    finally:

        conn.close()


# ============================================================
# DELETE ALL TIMETABLE DATA
# ============================================================

@app.route("/api/delete_all", methods=["POST"])
def delete_all():

    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()

    try:

        conn.execute("DELETE FROM timetable")
        conn.commit()

        return jsonify({
            "message": "All timetable data deleted successfully"
        })

    finally:

        conn.close()


# ============================================================
# PAGES
# ============================================================

@app.route("/add")
def add_page():

    if "user" not in session:
        return redirect("/")

    return render_template("add.html")


@app.route("/timetable_page")
def timetable_page():

    if "user" not in session:
        return redirect("/")

    return render_template("timetable.html")


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({
        "error": "Page not found"
    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({
        "error": "Internal server error"
    }), 500


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )