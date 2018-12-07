#Goodreads API key: h6t5UWEmwHp7la5Ec3kRFw

import os

from flask import Flask, session, render_template, request, redirect, url_for, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    else:

        username = request.form.get("username")
        password = request.form.get("password")
        id = db.execute("SELECT id FROM users WHERE username = :username and password = :password", {"username": username, "password": password}).fetchone()
        if id == None:
            return render_template("index.html", error="Incorrect username or password, please try again")
        else:
            print(id[0])
            session["user_id"] = id[0]
            return redirect(url_for("search"))


@app.route("/search", methods=["GET","POST"])
def search():
    # Make sure user is logged in
    try:
        session["user_id"]
    except KeyError:
        return redirect(url_for("index"))

    if request.method == "GET":
        return render_template("search.html")
    else:
        search = request.form.get("search")
        # Concatenate search w/ wildcards
        search = "%"+search+"%"
        # Select search results
        results = db.execute("SELECT * FROM books WHERE isbn LIKE :search OR author LIKE :search OR title LIKE :search", {"search": search}).fetchall()
        if not results:
            return render_template("search.html", error="No books matched your search")
        else:
            return render_template("search.html", results=results)

@app.route("/book/<string:isbn>", methods=["GET", "POST"])
def book(isbn):
    # Make sure user is logged in
    try:
        user_id = session["user_id"]
    except KeyError:
        return redirect(url_for("index"))

    # Get information from goodreads API
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "h6t5UWEmwHp7la5Ec3kRFw", "isbns": isbn})
    res=res.json()
    average_rating = res['books'][0]['average_rating']
    ratings_count = res['books'][0]['work_ratings_count']

    # Select book information
    info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchall()

    # Select reviews for book
    reviews = db.execute("SELECT review, rating FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchall()

    if request.method == "GET":
        if not res or not info:
            return redirect(url_for("search"))

        return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating)
    else:
        # Denies users review if they have already reviewed the book
        if db.execute("SELECT FROM reviews WHERE user_id = :user_id AND isbn = :isbn", {"user_id": user_id, "isbn":isbn }).fetchall():
            return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating,
                error="You have already submitted a review for this book")
        else:

            rating = request.form.get("inlineRadioOptions")
            review = request.form.get("review")

            if not rating or not review:
                return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating,
                    error="Please complete the form")

            db.execute("INSERT INTO reviews (rating, review, user_id, isbn) VALUES (:rating, :review, :user_id, :isbn)", {"rating": rating, "review": review, "user_id": user_id, "isbn": isbn})
            db.commit()

            reviews = db.execute("SELECT review, rating FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchall()
            return render_template("book.html", reviews=reviews, isbn=isbn, info=info, ratings_count=ratings_count, average_rating=average_rating)

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    else:

        # Extract data from HTML forms
        username = request.form.get("username")
        password = request.form.get("password")
        verifypassword = request.form.get("verifypassword")

        # Make sure username and password exist
        if len(username) == 0:
            return render_template("register.html", error="Please input a username")
        elif len(password) == 0:
            return render_template("register.html", error="Please input a password")
        # Search table for username, if username exists, return an error
        elif db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount!=0:
            return render_template("register.html", error="Username already exists! Pick a new one")
        # Make sure password is verified correctly
        elif verifypassword != password:
            return render_template("register.html", error="Your passwords do not match! Please try again")
        # Make sure username contains no spaces
        elif " " in username or " " in password:
            return render_template("register.html", error="Username/password must not contain spaces")
        # If username doesn't exist, enter it into the db
        else:

            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",
                {"username": username, "password": password})
            db.commit()
            id = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone()
            session["user_id"] = id[0]
            return render_template("index.html", message="Sucessfully Registered!")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/api/<string:isbn>")
def api(isbn):

    # Query data from SQL tables
    book_info=db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchall()

    if not book_info:
        abort(404)

    review_info=db.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE isbn=:isbn", {"isbn":isbn}).fetchall()

    # Store data in variables
    title = book_info[0][2]
    author = book_info[0][3]
    year = book_info[0][4]
    isbn = isbn
    review_count = review_info[0][1]
    average_score = review_info[0][0]

    # Create dict for json.dumps()
    json_info = {"title": title, "author": author, "year": year, "isbn": isbn, "review_count": review_count, "average_score": average_score}

    # return JSON data
    return jsonify(json_info)
