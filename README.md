# Project 1

Web Programming with Python and JavaScript

application.py contains several routes. Most routes are restricted if the user is not logged in. User login credentials are stored in session["user_id"].

HTML templates use jinja to extend layout.html.

There are various error checking mechanisms in order to ensure users provide correct login credentials, valid searches, correct routes, etc.

Import.py is much like the example used in the lecture. It uses csv.reader() to iterate over every column and row in the file, importing into the database as it goes.
