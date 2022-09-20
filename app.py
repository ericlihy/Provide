import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from tempfile import mkdtemp
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime
from helpers import apology, login_required, lookup, usd
import firebase_admin
import pyrebase
import json
from functools import wraps
from firebase_admin import credentials, auth
from werkzeug.utils import secure_filename

Global_name = ""

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
UPLOAD_FOLDER = '/downloads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

Session(app)

firebase = pyrebase.initialize_app(json.load(open('fbconfig.json')))

#init firebase
#auth instance
auth = firebase.auth()
#real time database instance
db = firebase.database()
#Data source
storage = firebase.storage()
# Configure CS50 Library to use SQLite database


def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #check for the variable that pyrebase creates
        if not auth.current_user != None:
            return redirect('register.html')
        return f(*args, **kwargs)
    return decorated_function



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Home page


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:

            # Search plans
            if len(request.form.get("search")) > 0:
                print("")
            dataposts = db.child("Subscriptions").get()
            allposts = []
            for post in dataposts.each():
                if request.form.get("search").lower() in post.val()["name"].lower()  or request.form.get("search").lower() in post.val()["description"].lower():
                    allposts.append(post)
            return render_template("index.html", subscriptionplans=allposts)
            # Subscribe viewer
            
        except:
            print("except statement")

            dataposts = db.child("Subscriptions").get()

            posts = []
            form = request.form
            for key in form:
                for plan in dataposts.each():
                    if(plan.key()) == key:
                        posts.append(plan)            
            
            return render_template("subscribeviewer.html", subscriptionplans=posts)
    else:
        try:
            print(session["usr"][-25:-5])
        except:
            print("not logged in")
            return render_template("login.html")
        allposts = []
        dataposts = db.child("Subscriptions").get()
        for post in dataposts.each():
            allposts.append(post)
        return render_template("index.html", subscriptionplans=allposts)
   

@app.route("/myplan", methods= ["POST", "GET"])
def myplan():
    if request.method == "POST":
        return render_template("myplan.html", subscriptionplans=allposts)
    else:
        dataposts = db.child("Users").child(session["usr"][-25:-5]).get()

        myplanposts = []
        for post in dataposts.each():
            if post.val()["myPlan"] == "false":
                myplanposts.append(post.val()["plan"])
        dataposts = db.child("Subscriptions").get()
        sub_posts = []
        for plan in dataposts.each():
                if plan.key() in myplanposts:
                    sub_posts.append(plan)
        return render_template("myplan.html", subscriptionplans=sub_posts)


@app.route("/providing", methods= ["POST", "GET"])
def providing():
    if request.method == "POST":
        return render_template("myplan.html", subscriptionplans=allposts)
    else:
        dataposts = db.child("Subscriptions").get()
        myplanposts = []
        for post in dataposts.each():
            print("Hello")
            if post.val("hidden_user_key") == session["usr"][-25:-5]:   
                myplanposts.append(post.val()["plan"])
        return render_template("providing.html", subscriptionplans=myplanposts)




@app.route("/join/<plan_id>", methods= ["POST"])
def join(plan_id):
    """Show myplan of transactions"""
    plan = {
        "plan": plan_id,
        "myPlan": "false"
    }

    db.child("Users").child(session["usr"][-25:-5]).push(plan)
    dataposts = db.child("Users").child(session["usr"][-25:-5]).get()
    
    myplanposts = []
    for post in dataposts.each():
        if post.val()["myPlan"] == "false":
            myplanposts.append(post.val()["plan"])
    dataposts = db.child("Subscriptions").get()
    sub_posts = []
    providing_posts = []
    for plan in dataposts.each():
            if plan.key() in myplanposts:
                sub_posts.append(plan)
            else:
                providing_posts.append(plan)
    return render_template("myplan.html", subscriptionplans=sub_posts, providingplans=providing_posts)

        
    # Render a page with all the items in the myplan table displayed (and the cash value)

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

        # Ensure username exists and password is correct
        
        # Remember which user has logged in
        #login the user
        print("AAAAAAAAAAAAAAAAAAAAAAAAA")
        Global_name = request.form.get("username")
        print(Global_name)
        user = auth.sign_in_with_email_and_password(request.form.get("username"), request.form.get("password"))
            #set the session
        user_id = user['idToken']
        user_email = request.form.get("username")
        session['usr'] = user_id
        session["email"] = user_email
        
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

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Make sure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400) 

        # Ensure confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation", 400)

        # Check if password and confirmation match up
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)
    
        # Check if username already exists

        # Valid username and password

        # Generate hash for password
        password = generate_password_hash(request.form.get("password"))

        # Update the users table
        auth.create_user_with_email_and_password(request.form.get("username"), request.form.get("password"))
        return render_template("login.html")
    # GET request
    else:
        return render_template("register.html")


# Create page
@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
        hidden_user_key = session["usr"][-25:-5]
        image = request.files['file']
        filename = secure_filename(image.filename)
        image.save(image.filename)
        storage.child(name).put(image.filename)
        print("image: ")
        print(image)
        print(storage.child(name).get_url(None))

        

        subscription = {
        "name": name,
        "price": price,
        "description": description,
        "author": session["email"],
        "username": Global_name,
        "image_url": storage.child(name).get_url(None)
        }
        

        db.child("Subscriptions").push(subscription)

        dataposts = db.child("Subscriptions").get()
        allposts = []
        for post in dataposts.each():
            allposts.append(post)
        return render_template("index.html", subscriptionplans=allposts)
    
    else: 
        return render_template("create.html")

@app.route("/edit", methods=["GET", "POST"])
@isAuthenticated
def edit():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        description = request.form["description"]
 

        subscription = {
        "name": name,
        "price": price,
        "description": description,
        "author": session["email"]
        }
        
        db.child("Subscriptions").push(subscription)

        dataposts = db.child("Subscriptions").get()
        allposts = []
        for post in dataposts.each():
            allposts.append(post)
            return render_template("index.html", subscriptionplans=allposts)
            
        else: 
            return render_template("create.html")
        

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

app.run('0.0.0.0',8080)