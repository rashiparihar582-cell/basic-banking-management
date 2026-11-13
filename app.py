
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

app.secret_key = "securebank_demo_secret_key"
# Database file location
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank.db")
def login_required(function):
    from functools import wraps

    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("home"))

        return function(*args, **kwargs)

    return wrapper

# Connect to SQLite database
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database tables
def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL
        )
    """)

    # Create account only if it does not already exist
    account = conn.execute(
        "SELECT id FROM accounts WHERE id = 1"
    ).fetchone()

    if account is None:
        conn.execute(
            "INSERT INTO accounts (id, balance) VALUES (?, ?)",
            (1, 50000)
        )

    conn.commit()
    conn.close()


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "student" and password == "bank123":
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        else:
            return render_template(
                "login.html",
                error="Invalid username or password!"
            )

    return render_template("login.html")



@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()

    account = conn.execute(
        "SELECT balance FROM accounts WHERE id = 1"
    ).fetchone()

    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        balance=account["balance"],
        transactions=transactions,
        error=request.args.get("error")
    )


@app.route("/deposit", methods=["POST"])
@login_required
def deposit():
    try:
        amount = int(request.form.get("amount", ""))
    except (ValueError, TypeError):
        return redirect(url_for("dashboard", error="Enter a valid amount!"))

    if amount <= 0:
        return redirect(url_for("dashboard", error="Amount must be greater than zero!"))

    conn = get_db()

    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = 1",
        (amount,)
    )

    conn.execute(
        "INSERT INTO transactions (date, type, amount) VALUES (?, ?, ?)",
        (datetime.now().strftime("%d-%m-%Y"), "Deposit", amount)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/withdraw", methods=["POST"])
@login_required
def withdraw():
    try:
        amount = int(request.form.get("amount", ""))
    except (ValueError, TypeError):
        return redirect(url_for("dashboard", error="Enter a valid amount!"))

    if amount <= 0:
        return redirect(url_for("dashboard", error="Amount must be greater than zero!"))

    conn = get_db()

    account = conn.execute(
        "SELECT balance FROM accounts WHERE id = 1"
    ).fetchone()

    if amount > account["balance"]:
        conn.close()
        return redirect(url_for("dashboard", error="Insufficient balance!"))

    conn.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id = 1",
        (amount,)
    )

    conn.execute(
        "INSERT INTO transactions (date, type, amount) VALUES (?, ?, ?)",
        (datetime.now().strftime("%d-%m-%Y"), "Withdrawal", amount)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
