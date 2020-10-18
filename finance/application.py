import os
import requests

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
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
	#look up the current user
	users = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
	stocks = db.execute("SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])
	quotes = {}
	for stock in stocks:
		quotes[stock["symbol"]] = lookup(stock["symbol"])

	cash_remaining = users[0]["cash"]
	total = cash_remaining
	return render_template("index.html", quotes=quotes, stocks=stocks, total=total, cash_remaining=cash_remaining)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
	"""Buy shares of stock"""
	symbol = request.form.get("symbol")
	shares = request.form.get("shares")
	if request.method == "POST":
		#call lookup func to lookup a stock's current price
		data = lookup(symbol)
		if int(shares) <= 0:
			return apology("shares must be a positive number")
		elif symbol == " " or data == None  :
			return apology("Enter a vaild symbol")
		#select how much cash the user currently has in users 
		cash = db.execute("SELECT cash FROM users WHERE id = :id",
						id=session["user_id"])
		user_id = session["user_id"] 
		price = data["price"]
		cash = cash[0]["cash"] - price * float(shares)
		
		db.execute("update users set cash = :cash  where id = :id ", cash = cash , id = user_id)
		db.execute("INSERT INTO transactions (user_id, symbol, shares, price_per_share) VALUES(:user_id, :symbol, :shares, :price)",
				   user_id=session["user_id"],
				   symbol=symbol,
				   shares=shares,
				   price=price)
		return redirect(url_for("index"))
	else:
		return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
	"""Return true if username available, else false, in JSON format"""
	return jsonify("TODO")


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
		rows = db.execute("SELECT * FROM users WHERE username = :username",
						  username=request.form.get("username"))

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
	symbol = request.form.get("symbol")
	if request.method == "POST":
		data = lookup(symbol)
		return render_template("quoted.html", data=data)
	return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
	"""Register user"""
	username = request.form.get("username")
	password = request.form.get("password")
	confirmation = request.form.get("confirmation password")
	if request.method == "POST":
		if not username :
			return apology("must provide username", 403)

		# Ensure password was submitted
		elif not password:
			return apology("must provide password", 403)
		# Ensure confirmation password was submitted
		elif not confirmation:
			return apology("must provide confirmation password", 403)
		elif confirmation != password:
			return apology("must password equal confirmation password", 403)
		db.execute("insert into users (username, hash) values (:username, :hash )",
								 username = username, hash = generate_password_hash(password) )
		print(username, password.encode(), generate_password_hash(password))

		return render_template("register.html")
	else: 
		return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
	"""Sell shares of stock"""
	shares = db.execute("select shares from purchases where user_id = :user_id", user_id = session["user_id"])
	symbol = request.form.get("symbol")
	if request.method == "POST":
		#call lookup func to lookup a stock's current price
		data = lookup(symbol)
		if data == None :
			return apology("invalid symbol")
		try:
			shares = int(request.form.get("shares"))
		except:
			return apology("shares must be a positive integer", 400)

		if shares <= 0:
			return apology("can't sell less than or 0 shares", 400)

		stock = db.execute("SELECT SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id AND symbol = :symbol GROUP BY symbol",
						   user_id=session["user_id"], symbol=request.form.get("symbol"))

		if len(stock) != 1 or stock[0]["total_shares"] <= 0 or stock[0]["total_shares"] < shares:
			return apology("you can't sell less than 0 or more than you own", 400)
		
		#select how much cash the user currently has in users 
		cash = db.execute("SELECT cash FROM users WHERE id = :id ",
						id=session["user_id"])

		price = data["price"]
		cash = cash[0]["cash"] + (float(shares) * price)
		
		db.execute("update users set cash = :cash  where id = :id", cash = cash , id = session["user_id"])
	

		# Book keeping (TODO: should be wrapped with a transaction)
		db.execute("INSERT INTO transactions (user_id, symbol, shares, price_per_share) VALUES(:user_id, :symbol, :shares, :price)",
				   user_id=session["user_id"],
				   symbol=symbol,
				   shares=-shares,
				   price=price)

		return redirect(url_for("index"))
	else:
		stocks = db.execute(
			"SELECT symbol, SUM(shares) as total_shares FROM transactions WHERE user_id = :user_id GROUP BY symbol HAVING total_shares > 0", user_id=session["user_id"])

		return render_template("sell.html", stocks=stocks)


def errorhandler(e):
	"""Handle error"""
	if not isinstance(e, HTTPException):
		e = InternalServerError()
	return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
	app.errorhandler(code)(errorhandler)
