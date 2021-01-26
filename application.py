import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd
app.jinja_env.globals.update(lookup = lookup)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    groups = db.execute("SELECT symbol, SUM(num_shares) AS sum FROM purchases WHERE user_id = ? GROUP BY symbol", session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    cashValue = float(cash[0]["cash"])
    return render_template("index.html", groups=groups, cashValue=cashValue)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        currentTime = datetime.datetime.now()
        symbol = request.form.get("symbol")
        numOfShares = request.form.get("shares")
        bought = lookup(symbol)
        price=bought["price"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cashValue = float(cash[0]["cash"])
        costOfShares = int(numOfShares) * price
        balance = cashValue - costOfShares
        if cashValue < costOfShares:
            return apology("Your balance is too low!")
        else:
            purchase = db.execute("INSERT INTO purchases (user_id, symbol, share_price, num_shares, total_cost, timestamp) VALUES(?, ?, ?, ?, ?, ?)", \
                                session["user_id"], symbol, price, numOfShares, costOfShares, currentTime)
            newBalance = db.execute("UPDATE users SET cash = ? WHERE id = ?", balance, session["user_id"])
            return render_template("bought.html", balance=balance, costOfShares=costOfShares, bought=bought, numOfShares=numOfShares, cash=cash[0]["cash"])
    return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
    if request.method == "POST":
        symbol = request.form.get("symbol")
        quoted = lookup(symbol)
        return render_template("quoted.html", quoted=quoted)
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        hashed = generate_password_hash(request.form.get("password"))
        if check_password_hash(hashed,request.form.get("confirm")):
            register = db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", username, hashed)
            return "<h1> You have regestered </h1>"
        else:
            return apology("Passwords don't match")
        return "<h1>You have registered "+ username + " with password "+ hashed +"</h1>"
    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
