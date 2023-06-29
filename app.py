from flask import Flask, render_template, request, session, redirect, flash
from cs50 import SQL
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

app = Flask(__name__)
db = SQL("sqlite:///shoppr.db")

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    if session.get("user_id") == None:
        return redirect("/login")
    user_id = session["user_id"]
    #today = date.today()
    name = db.execute("SELECT username FROM user_data WHERE id = ?", user_id)
    print(name)
    data = db.execute("SELECT SUM(receipts.price) AS price, receipts.date, receipts.user_id FROM products INNER JOIN receipts ON products.id=receipts.product_id WHERE receipts.user_id = ?", user_id)
    today = db.execute("SELECT SUM(receipts.price) AS today FROM receipts WHERE date = ? AND user_id = ?", date.today(), user_id)
    zero = data[0]["price"]
    today_zero = today[0]["today"]
    name = name[0]["username"]

    # get amount of days since first transaction
    earliest = db.execute("SELECT MIN(date) FROM receipts WHERE user_id = ?", user_id)
    if earliest[0]["MIN(date)"] == None:
        return render_template("index.html", data = data, today_zero = today_zero, zero = zero, name = name, days = 0, today = 0)
    d01 = earliest[0]["MIN(date)"]
    format = "%Y-%m-%d"
    
    d0 = datetime.strptime(d01, format)
    d1 = datetime.today()

    delta = d1 - d0
    delta = delta.days
    
    return render_template("index.html", data = data, zero = zero, today_zero = today_zero, days = delta, today = today, name = name)   
    

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":

        # check if name is in database
        user = request.form.get("user")
        password = request.form.get("password")
        user_row = db.execute("SELECT * FROM user_data WHERE username = ?", user)

        # check if password matches
        if len(user_row) != 1 or not check_password_hash(user_row[0]["password"], password):
            flash("Username or password is incorrect")
            return redirect("/login")
        
        session["user_id"] = user_row[0]["id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":

        # add details to the database and redirect to login
        name = request.form.get("user")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # check if name and password were entered
        if not name:
            flash("Please enter a name")
            return redirect("/register")
        if not password:
            flash("Please enter a password")
            return redirect("/register")
        
        # check if user exists
        check = db.execute("SELECT COUNT(*) FROM user_data where username = ?", name)
        if check[0]["COUNT(*)"] != 0:
            flash("username already taken")
            return redirect("/register")
        
        if password == confirm_password:
            hash = generate_password_hash(password)

            # save name and password in the database
            db.execute("INSERT INTO user_data (username, password) VALUES (?, ?)", name, hash)

        else:
            flash("Password does not match")
            return redirect("/register")
        
        # registered sucessfully banner
        flash("Registered!")
        return redirect("/login")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return render_template("login.html")

@app.route("/add_items", methods = ["GET", "POST"])
def add_items():
    if request.method == "POST":
        name = request.form.get("name")
        brand = request.form.get("brand")
        shop = request.form.get("shop")
        price = request.form.get("price")

        print(name, brand, shop, price)

        db.execute("INSERT INTO products (name, brand, shop, price) VALUES (?, ?, ?, ?)", name, brand, shop, price)
        flash("Item added to the database")
        return redirect("/add_items")
    
    items = db.execute("SELECT * FROM products ORDER BY name")
    return render_template("items.html", items = items)

@app.route("/update")
def update():
    id = request.args.get("update")
    price = request.args.get("price_update")
    db.execute("UPDATE products SET price = ? WHERE id = ?",price, id)
    return redirect("/add_items")

@app.route("/add_to_list")
def add_item():
    user_id = session["user_id"]
    product_id = request.args.get("add")
    db.execute("INSERT INTO shopping_list (user_id, product_id) VALUES (?, ?)", user_id, product_id,)
    return redirect("/shopping_list")

@app.route("/search")
def search():
    q = request.args.get("q")
    if q:
        products = db.execute("SELECT * FROM products WHERE name LIKE ?", "%" + q + "%")
    else:
        products = []
    return render_template("search.html", products = products)

@app.route("/shopping_list")
def shopping_list():
    user_id = session["user_id"]
    items = db.execute("SELECT products.id, products.price, products.name, products.brand, products.shop, shopping_list.id, shopping_list.product_id FROM products INNER JOIN shopping_list ON products.id=shopping_list.product_id WHERE user_id = ?", user_id)
    return render_template("shopping_list.html", items = items)

@app.route("/remove")
def remove():
    id = request.args.get("remove")
    db.execute("DELETE from shopping_list WHERE id = ?", id,)
    return redirect("/shopping_list")

@app.route("/bought")
def bought():
    user_id = session["user_id"]

    # shopping list id
    id = request.args.get("bought")

    # get price
    price = request.args.get("price_change")
    print(price)

    # get product using shopping list id
    product_id_dict = db.execute("SELECT product_id FROM shopping_list WHERE id = ?", id)
    for each in product_id_dict:
        db.execute("INSERT INTO receipts (user_id, product_id, price) VALUES (?, ?, ?)", user_id, each['product_id'], price)
        
    db.execute("DELETE from shopping_list WHERE id = ?", id,)
    return redirect("/shopping_list")

@app.route("/")

@app.route("/receipts")
def receipts():
    user_id = session["user_id"]

    # change price if needed

    # get product id's
    receipt_data = db.execute("SELECT receipts.id, receipts.price, receipts.product_id, products.name, products.shop, receipts.date FROM products INNER JOIN receipts ON products.id=receipts.product_id WHERE receipts.user_id = ? ORDER BY receipts.id DESC", user_id)
    return render_template("receipts.html", receipt_data = receipt_data)

@app.route("/delete_record")
def delete_record():
    id = request.args.get("record")
    db.execute("DELETE from receipts WHERE id = ?", id,)
    return redirect("/receipts")
