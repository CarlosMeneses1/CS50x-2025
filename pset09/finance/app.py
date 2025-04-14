import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # User reached route via GET (as by clicking a link or by redirect)

    # Looking for the logged-in user's transactions
    user_transactions = db.execute(
        "SELECT symbol, SUM(share) AS share FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(share) > 0", session["user_id"]
    )

    total = 0
    # Lookup the current price of the shares that the logged-in user owns
    for transaction in user_transactions:
        current_price = lookup(transaction["symbol"])["price"]

        transaction["current_price"] = current_price
        transaction["total"] = current_price * transaction["share"]

        total += transaction["total"]

    # Looking for the logged-in user's information
    user_information = db.execute(
        "SELECT * FROM users WHERE id = ?", session["user_id"]
    )

    current_cash = user_information[0]["cash"]
    total += user_information[0]["cash"]

    return render_template("index.html", user_transactions=user_transactions, current_cash=current_cash, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a buy form)
    if request.method == "POST":
        # Get the information needed to validation
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")

        # Ensure all information was submitted
        if not symbol or not shares:
            return apology("Do not leave any blank spaces", 400)

        # Look the symbol information submitted
        quote = lookup(symbol)

        # Check if was submitted a valid symbol
        if not quote:
            return apology("Invalid Symbol", 400)

        if not shares.isdigit():
            return apology("Number of shares must be a positive digit!", 400)

        # Looking for the logged-in user's information
        user = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )

        # Calculate the total buy price
        total_price = (int(shares) * quote["price"])

        # Check if the user has enought money to buy
        if user[0]["cash"] < total_price:
            return apology("Can't afford", 400)

        # Update the available cash of the logged-in user according to the buy made
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?", (user[0]["cash"] - total_price), session["user_id"]
        )

        # Insert new register into 'transactions' table
        db.execute(
            "INSERT INTO transactions (user_id, symbol, share, price, type, date) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            session["user_id"],
            symbol,
            int(shares),
            quote["price"],
            "Buy"
        )

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():

    # Looking for the logged-in user's transactions
    user_transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id = ?", session["user_id"]
    )

    return render_template("history.html", user_transactions=user_transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a lookup form via POST)
    if request.method == "POST":
        # Look the symbol submitted
        quote = lookup(str(request.form.get("symbol")))

        # Check if was submitted a valid symbol
        if not quote:
            return apology("Invalid symbol", 400)

        else:
            return render_template("quoted.html", quote=quote)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a register from via POST)
    if request.method == "POST":
        # Get the information needed to validation
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure all information was submitted
        if not username or not password or not confirmation:
            return apology("Do not leave any blank spaces", 400)

        # Ensure password and confirmation are the same
        if password != confirmation:
            return apology("Password must be the same as Confirmation", 400)

        # Ensure username submitted is unique
        if db.execute("SELECT username FROM users WHERE username = ?", username):
            return apology("Username already taken, try another", 400)

        # Converts the password into its hashed version
        hashed_password = generate_password_hash(password)

        # Insert the valid username submitted
        db.execute(
            "INSERT INTO users (username, hash) VALUES (?, ?)",
            username,
            hashed_password,
        )

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", username
        )

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    # User reached route via GET (as by clicking a link or via rediret)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a sell form via POST)
    if request.method == "POST":
        # Get the information needed to validation
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        # Ensure all information was submitted
        if not symbol or not shares:
            return apology("Do not leave any blank spaces", 400)

        # Looking for the logged-in user's transactions
        user_transactions = db.execute(
            "SELECT symbol, SUM(share) AS share FROM transactions WHERE user_id = ? GROUP BY symbol", session["user_id"]
        )

        # Check if the number of shares that the user want to sell is correct
        for transaction in user_transactions:
            if transaction["symbol"] == symbol and transaction["share"] < shares:
                return apology("Too many shares", 400)

        # Looking for the logged-in user's information
        user_information = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )

        # Look the symbol information submitted
        quote = lookup(symbol)

        # Calculate the sale price
        total_price = quote["price"] * shares

        # Update the available cash of the logged-in user according to the sell made
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            (user_information[0]["cash"] + total_price), session["user_id"]
        )

        # Update the avalaible shares in portfolio
        db.execute(
            "INSERT INTO transactions (user_id, symbol, share, price, type, date) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            session["user_id"],
            symbol,
            (shares * -1),
            quote["price"],
            "Sell"
        )

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user_transactions = db.execute(
            "SELECT symbol, SUM(share) AS share FROM transactions WHERE user_id = ? GROUP BY symbol HAVING SUM(share) > 0", session["user_id"]
        )

        return render_template("sell.html", user_transactions=user_transactions)


@app.route("/cash", methods=["GET", "POST"])
@login_required
def cash():
    """Charge cash into the account"""

    if request.method == "POST":
        # Get the information needed to validation
        cash = request.form.get("cash")

        # Ensure all information was submitted
        if not cash:
            return apology("Do not leave any blank spaces", 400)

        # Ensure submit the correct type of value
        if float(cash) < 1:
            return apology("Cash must be positive value")

        # Looking for the logged-in user's information
        user_information = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )

        update_cash = user_information[0]["cash"] + float(cash)

        # Update the connected user's available cash according to the amount loaded
        db.execute(
            "UPDATE users SET cash = ? WHERE id = ?",
            update_cash, session["user_id"]
        )

        return redirect("/")

    else:
        return render_template("cash.html")
