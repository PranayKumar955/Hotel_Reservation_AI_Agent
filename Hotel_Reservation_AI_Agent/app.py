import os
import sqlite3
import secrets
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, abort

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-development-secret")
DATABASE = os.path.join(os.path.dirname(__file__), "hotel.db")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin@123")  # Change before deployment!

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            room_type TEXT NOT NULL,
            price REAL NOT NULL CHECK(price >= 0),
            capacity INTEGER NOT NULL CHECK(capacity > 0),
            description TEXT NOT NULL DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_ref TEXT NOT NULL UNIQUE,
            guest_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            room_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT NOT NULL,
            guests INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Confirmed',
            created_at TEXT NOT NULL,
            FOREIGN KEY(room_id) REFERENCES rooms(id)
        );
        """)
        count = db.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO rooms(room_number, room_type, price, capacity, description) VALUES(?,?,?,?,?)",
                [
                    ("101", "Standard", 1800, 2, "Comfortable room with Wi-Fi and attached bathroom."),
                    ("102", "Standard", 1800, 2, "Cozy room for solo travellers or couples."),
                    ("201", "Deluxe", 2800, 3, "Spacious room with air conditioning and breakfast."),
                    ("202", "Deluxe", 2800, 3, "Deluxe room with workspace and city view."),
                    ("301", "Family Suite", 4500, 5, "Large suite suitable for families."),
                ],
            )

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

def valid_dates(check_in, check_out):
    try:
        start = date.fromisoformat(check_in)
        end = date.fromisoformat(check_out)
        return start >= date.today() and end > start
    except (TypeError, ValueError):
        return False

def available_rooms(check_in, check_out, guests=1):
    sql = """
    SELECT r.* FROM rooms r
    WHERE r.active = 1 AND r.capacity >= ?
    AND NOT EXISTS (
        SELECT 1 FROM bookings b
        WHERE b.room_id = r.id AND b.status = 'Confirmed'
          AND b.check_in < ? AND b.check_out > ?
    )
    ORDER BY r.price ASC
    """
    with get_db() as db:
        return db.execute(sql, (guests, check_out, check_in)).fetchall()

@app.route("/")
def index():
    with get_db() as db:
        rooms = db.execute("SELECT * FROM rooms WHERE active=1 ORDER BY price").fetchall()
    return render_template("index.html", rooms=rooms, today=date.today().isoformat())

@app.route("/availability", methods=["GET", "POST"])
def availability():
    rooms = []
    check_in = request.values.get("check_in", "")
    check_out = request.values.get("check_out", "")
    guests = request.values.get("guests", "1")
    searched = request.method == "POST" or bool(check_in and check_out)
    if searched:
        try:
            guest_count = int(guests)
            if guest_count < 1 or guest_count > 20:
                raise ValueError()
        except ValueError:
            flash("Please enter a valid number of guests.", "error")
            return render_template("availability.html", rooms=[], check_in=check_in, check_out=check_out, guests=guests, today=date.today().isoformat())
        if not valid_dates(check_in, check_out):
            flash("Choose a check-in date today or later and a check-out date after check-in.", "error")
        else:
            rooms = available_rooms(check_in, check_out, guest_count)
            if not rooms:
                flash("No rooms are available for those dates and guest count.", "info")
    return render_template("availability.html", rooms=rooms, check_in=check_in, check_out=check_out, guests=guests, today=date.today().isoformat())

@app.route("/book/<int:room_id>", methods=["GET", "POST"])
def book(room_id):
    with get_db() as db:
        room = db.execute("SELECT * FROM rooms WHERE id=? AND active=1", (room_id,)).fetchone()
    if not room:
        abort(404)
    check_in = request.values.get("check_in", "")
    check_out = request.values.get("check_out", "")
    guests = request.values.get("guests", "1")
    if request.method == "POST":
        name = request.form.get("guest_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        try:
            guest_count = int(guests)
        except ValueError:
            guest_count = 0
        if not name or not email or not phone:
            flash("Please fill in your name, email, and phone.", "error")
        elif not valid_dates(check_in, check_out):
            flash("Dates are invalid. Check-out must be after check-in, and check-in cannot be in the past.", "error")
        elif guest_count < 1 or guest_count > room["capacity"]:
            flash(f"This room supports 1 to {room['capacity']} guests.", "error")
        else:
            # Re-check availability at submission time to avoid booking a room already reserved.
            rooms_now = {r["id"] for r in available_rooms(check_in, check_out, guest_count)}
            if room_id not in rooms_now:
                flash("Sorry, this room is no longer available for those dates. Search again.", "error")
                return redirect(url_for("availability"))
            nights = (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days
            ref = "HRA-" + secrets.token_hex(4).upper()
            with get_db() as db:
                db.execute("""INSERT INTO bookings
                    (booking_ref, guest_name, email, phone, room_id, check_in, check_out, guests, total_price, status, created_at)
                    VALUES(?,?,?,?,?,?,?,?,?,'Confirmed',?)""",
                    (ref, name, email, phone, room_id, check_in, check_out, guest_count,
                     nights * room["price"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            return render_template("confirmation.html", ref=ref, name=name, room=room, check_in=check_in, check_out=check_out, guests=guest_count, total=nights*room["price"], nights=nights)
    return render_template("book.html", room=room, check_in=check_in, check_out=check_out, guests=guests, today=date.today().isoformat())

@app.route("/booking-status", methods=["GET", "POST"])
def booking_status():
    booking = None
    if request.method == "POST":
        ref = request.form.get("booking_ref", "").strip().upper()
        email = request.form.get("email", "").strip().lower()
        with get_db() as db:
            booking = db.execute("""SELECT b.*, r.room_number, r.room_type
                FROM bookings b JOIN rooms r ON r.id=b.room_id
                WHERE b.booking_ref=? AND lower(b.email)=?""", (ref, email)).fetchone()
        if not booking:
            flash("No booking found for that reference and email.", "error")
    return render_template("booking_status.html", booking=booking)

@app.route("/cancel-booking", methods=["POST"])
def cancel_booking():
    ref = request.form.get("booking_ref", "").strip().upper()
    email = request.form.get("email", "").strip().lower()
    with get_db() as db:
        result = db.execute("""UPDATE bookings SET status='Cancelled'
            WHERE booking_ref=? AND lower(email)=? AND status='Confirmed'""", (ref, email))
    if result.rowcount:
        flash("Your booking has been cancelled.", "success")
    else:
        flash("Booking could not be cancelled. Check details or contact the hotel.", "error")
    return redirect(url_for("booking_status"))

def chatbot_reply(message):
    msg = message.lower()
    if any(word in msg for word in ["hello", "hi", "hey", "good morning", "good evening"]):
        return "Hello! Welcome to HotelEase. I can help with room prices, availability, bookings, cancellation, and check-in information."
    if any(word in msg for word in ["price", "cost", "rate", "how much"]):
        with get_db() as db:
            rows = db.execute("SELECT room_type, MIN(price) AS price FROM rooms WHERE active=1 GROUP BY room_type ORDER BY price").fetchall()
        return "Current room rates per night: " + "; ".join(f"{r['room_type']}: ₹{r['price']:.0f}" for r in rows) + ". Taxes or extra services may change the final bill."
    if any(word in msg for word in ["available", "availability", "vacant", "book a room"]):
        return "To check live availability, open the Room Availability page and enter your check-in date, check-out date, and number of guests. The system checks existing confirmed bookings."
    if any(word in msg for word in ["cancel", "cancellation"]):
        return "Open Booking Status, enter your booking reference and the email used for the reservation, then choose Cancel Booking if the reservation is confirmed."
    if any(word in msg for word in ["booking status", "reservation status", "my booking", "confirmation"]):
        return "Use the Booking Status page with your booking reference (for example, HRA-1A2B3C4D) and the email used to book."
    if any(word in msg for word in ["check in", "check-in", "checkout", "check-out", "time"]):
        return "Standard check-in is 12:00 PM and check-out is 11:00 AM. Please contact the hotel for early check-in or late check-out."
    if any(word in msg for word in ["wifi", "wi-fi", "breakfast", "ac", "air conditioning", "facility", "amenities"]):
        return "Room facilities vary by room type. Our Deluxe rooms include air conditioning and breakfast; all listed rooms include Wi-Fi. Check the room descriptions for details."
    if any(word in msg for word in ["thank"]):
        return "You're welcome! Let me know if you need help with a reservation."
    return "I can help with room prices, room availability, booking status, cancellation, facilities, and check-in/check-out times. For a live booking, use the pages in the navigation menu."

@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()[:500]
    if not message:
        return jsonify({"reply": "Please type a question."}), 400
    return jsonify({"reply": chatbot_reply(message)})

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password, ADMIN_PASSWORD):
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    with get_db() as db:
        stats = {
            "rooms": db.execute("SELECT COUNT(*) FROM rooms WHERE active=1").fetchone()[0],
            "bookings": db.execute("SELECT COUNT(*) FROM bookings").fetchone()[0],
            "confirmed": db.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'").fetchone()[0],
            "revenue": db.execute("SELECT COALESCE(SUM(total_price),0) FROM bookings WHERE status='Confirmed'").fetchone()[0],
        }
        bookings = db.execute("""SELECT b.*, r.room_number, r.room_type FROM bookings b
            JOIN rooms r ON r.id=b.room_id ORDER BY b.id DESC LIMIT 100""").fetchall()
        rooms = db.execute("SELECT * FROM rooms ORDER BY room_number").fetchall()
    return render_template("admin_dashboard.html", stats=stats, bookings=bookings, rooms=rooms)

@app.route("/admin/rooms", methods=["POST"])
@admin_required
def admin_add_room():
    room_number = request.form.get("room_number", "").strip()
    room_type = request.form.get("room_type", "").strip()
    description = request.form.get("description", "").strip()
    try:
        price = float(request.form.get("price", ""))
        capacity = int(request.form.get("capacity", ""))
        if not room_number or not room_type or price < 0 or capacity < 1:
            raise ValueError()
        with get_db() as db:
            db.execute("INSERT INTO rooms(room_number, room_type, price, capacity, description) VALUES(?,?,?,?,?)",
                       (room_number, room_type, price, capacity, description))
        flash("Room added successfully.", "success")
    except sqlite3.IntegrityError:
        flash("That room number already exists.", "error")
    except ValueError:
        flash("Enter a valid room number, room type, non-negative price, and capacity.", "error")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/rooms/<int:room_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_room(room_id):
    with get_db() as db:
        db.execute("UPDATE rooms SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?", (room_id,))
    flash("Room availability updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/bookings/<int:booking_id>/cancel", methods=["POST"])
@admin_required
def admin_cancel_booking(booking_id):
    with get_db() as db:
        db.execute("UPDATE bookings SET status='Cancelled' WHERE id=? AND status='Confirmed'", (booking_id,))
    flash("Booking status updated.", "success")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

init_db()

if __name__ == "__main__":
    app.run(debug=True)
