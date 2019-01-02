# Description

This application is a small book lookup site that uses goodreads API, Flask, and SQL. It also uses a SQL database to keep track of users, their reviews, etc..

application.py contains several routes. Most routes are restricted if the user is not logged in. User login credentials are stored in session["user_id"].

HTML templates use jinja to extend layout.html.

There are various error checking mechanisms in order to ensure users provide correct login credentials, valid searches, correct routes, etc.

Additionally, books were imported to the SQL database using Import.py
Import.py uses csv.reader() to iterate over every column and row in the file, importing into the database as it runs.
