from flask import Flask, flash, render_template, redirect, request, session, jsonify
from flask_session import Session
from cs50 import SQL
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta, date

from helpers import login_required, usd, days_between


# config app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# config SQL database
db = SQL("sqlite:///assets.db")


# hompage route
@app.route("/")
def index():

    # If user not logged in
    if not session.get("user_id"):
        return render_template("index2.html")


    else:
        """Update till current day and show general information of items for user"""

        # Update the today variable
        today = str(date.today())

        # Query for item list
        items = db.execute("SELECT * FROM items WHERE user_id = ?", session['user_id'])

        for item in items:

            # Get info from database
            bought = item['bought']
            price = item['price']
            depr_per_month = item['depreciation_per_month']

            # Calculate the changing variable in database
            used = int((days_between(bought, today))/30)
            book_value = round(float(price) - (depr_per_month * used), 2)
            savings = depr_per_month * used

            # Check if the item lifetime is expired or not
            expire = days_between(item['should_replace'], today)

            # If expired, set book_value and depr per month to 0
            if expire >= 0:
                depr_per_month = 0
                book_value = 0
                savings = price

            # Update the variable
            db.execute("UPDATE items SET used = ?, depreciation_per_month = ?, book_value = ?, savings_should_have = ? WHERE id = ? AND user_id = ?",
                        used, depr_per_month, book_value, savings, item['id'], session['user_id'])


        # Calculate variable in user table
        new_items = db.execute("SELECT * FROM items WHERE user_id = ?", session['user_id'])
        quantity = len(new_items)
        total_savings = 0
        total_depr = 0
        items_repl = 0
        all_items_maint = 0

        for item in new_items:

            # sum up total savings need to replace items
            total_savings += item['savings_should_have']

            # sum up depreciation per month of all items
            total_depr += item['depreciation_per_month']

            # sum up items maintenance cost per month for all items
            all_items_maint += item['maint']

            # calculate how many items need to be replace in 30 days
            if int(days_between(today, item['should_replace'])) <= 30:
                items_repl += 1

        # round up total_savings:
        total_savings = round(total_savings, 2)

        # round up total_depr:
        total_depr = round(total_depr, 2)

        # round up all_items_maint:
        all_items_maint = round(all_items_maint, 2)

        # add both maintenace cost and depreciation cost per month
        monthly_total = round(total_depr + all_items_maint, 2)

        # Update data into user table
        db.execute("UPDATE users SET item_quantity = ?, monthly_total = ?, all_items_maint = ?, total_depr = ?, total_savings = ?, items_repl = ? WHERE id = ?",
                    quantity, monthly_total, all_items_maint, total_depr, total_savings, items_repl, session['user_id'])

        # Query data from user table
        user = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])

        # Return information to index
        return render_template("index.html", user=user)



# login route
@app.route("/login", methods=["GET", "POST"])
def login():

    # if user reached route by POST (as by submitting form)
    if request.method == "POST":

        name = request.form.get("username")
        password = request.form.get("password")

        # Check if user filled in the form
        if not name:
            return render_template("error.html", message="Missing username")

        if not password:
            return render_template("error.html", message="Missing password")

        # Check username in database and password is corrected
        check = db.execute("SELECT * FROM users WHERE username = ?", name)

        if len(check) != 1 or not check_password_hash(check[0]['hash'], password):
            return render_template("error.html", message="Invalid Username or Password")

        # If everything correct, remember the user and redirect to main page
        session['user_id'] = check[0]['id']
        session['username'] = check[0]['username']

        # Inform that the user login successfully
        flash("Logged in successfully!")

        # Redirect user to homepage
        return redirect("/")

    # if user reached route via GET (by click link or being redirected)
    else:
        return render_template("login.html")


# register route
@app.route("/register", methods=["GET", "POST"])
def register():

    # if user reached route by POST (as by submitting form)
    if request.method == "POST":

        name = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        # check if user filled the form
        if not name:
            return render_template("error.html", message="Missing Username")

        if not password:
            return render_template("error.html", message="Missing password")

        if not confirm:
            return render_template("error.html", message="You have to confirm password")

        if password != confirm:
            return render_template("error.html", message="Passwords don't match")

        # Check if user exist in database
        check = db.execute("SELECT * FROM users WHERE username = ?", name)

        if len(check) > 0:
            return render_template("error.html", message="Username already exist")

        # If no error, add user information into database
        db.execute("INSERT INTO users(username, hash) VALUES (?, ?)", name, generate_password_hash(password))


        # log the user in
        user = db.execute("SELECT * FROM users WHERE username = ?", name)
        session['user_id'] = user[0]['id']
        session['username'] = user[0]['username']

        # Inform that the user registered successfully
        flash("You are registered!")

        return redirect("/")

    # if user reached route by GET (by clicking link or being redirected)
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/change_pass", methods=["GET", "POST"])
@login_required
def change_pass():

    # user reached route via POST (as by submiting form)
    if request.method == "POST":

        # set variable names
        password = request.form.get("password")
        new = request.form.get("new")
        confirm = request.form.get("confirm")

        check = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])

        # Check user input validation
        if not password:
            return render_template("error.html", message="Missing password")

        if not new:
            return render_template("error.html", message="Missing new password")

        if not confirm:
            return render_template("error.html", message="You have to confirm new password")

        if new != confirm:
            return render_template("error.html", message="Passwords don't match")

        if not check_password_hash(check[0]['hash'], password):
            return render_template("error.html", message="Invalid password")

        # if nothing wrong, change the user password
        db.execute("UPDATE users SET hash = ? WHERE id = ?", generate_password_hash(new), session['user_id'])

        # Inform successfully
        flash("Password changed!")

        return redirect("/")

    # user reached route via GET (by click link)
    else:
        return render_template("change_pass.html")


@app.route("/add_item", methods=["GET", "POST"])
@login_required
def add_item():

    # If user reached route via POST (as by submiting form)
    if request.method == "POST":

        # define variable
        item = (request.form.get("item_name")).lower()
        price = request.form.get("price")
        bought = request.form.get("bought")
        life = request.form.get("life")
        warranty = request.form.get("warranty")
        brand = (request.form.get("brand")).upper()
        seller = (request.form.get("seller")).upper()
        maint = request.form.get("maint")

        # Check if user enter all required field
        if not item:
            return render_template("error.html", message="Missing item's name")
        if not price:
            return render_template("error.html", message="Missing price")
        if not bought:
            return render_template("error.html", message="Missing bought date")
        if not life:
            return render_template("error.html", message="Missing lifetime of item")

        # If some nonessential information was not filled by user, then automatically fill in for them
        if not brand:
            brand = "Not specified"
        if not seller:
            seller = "Not specified"
        if not maint:
            maint = 0

        # Round up price and maint:
        price = round(float(price), 2)
        maint = round(float(maint), 2)

        # calculate depreciate per month
        depr_per_month = round(float(price)/(int(life)), 2)

        # the date should be replace by the lifetime given by user
        should_replace = (datetime.strptime(bought, '%Y-%m-%d') + timedelta(days=30*int(life))).strftime('%Y-%m-%d')

        # define other variable
        today = str(date.today())

        # number of months used from the bought date
        used = int((days_between(bought, today))/30)


        # calculate book value left after depreciation
        book_value = float(price) - (depr_per_month * used)

        # saving should have
        savings = depr_per_month*used

        # insert new item information to the items table
        db.execute("INSERT INTO items (user_id, item, price, bought, used, should_replace, depreciation_per_month, book_value, savings_should_have, warranty, brand, seller, maint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    session['user_id'], item, price, bought, used, should_replace, depr_per_month, book_value, savings, warranty, brand, seller, maint)

        # Inform successfully
        flash("Item added!")

        # Redirect user back to homepage
        return redirect("/items")

    # If user reached route via GET (as by click link)
    else:
        return render_template("add_item.html")


@app.route("/pre_replace", methods=["POST"])
@login_required
def pre_replace():
    """Let user enter replace mode of their item"""

    # If user reached route via POST (as by submiting form)
    if request.method == "POST":

        id = request.form.get("id")

        # Get item's information from database
        items = db.execute("SELECT * FROM items WHERE id = ?", id)

        # Inform user to confirm replace
        flash("Please confirm the replacement")
        return render_template("replace.html", items=items)


@app.route("/replace_item", methods=["POST"])
@login_required
def replace_item():
    """Allow user to remove the item from item list and change it to history"""

    # If user reached route via POST (as by submiting form from item.html)
    if request.method == "POST":

        # Get info from the form
        id = request.form.get("id")
        reason_replace = request.form.get("reason")
        sold_price = request.form.get("sold")

        # Check user filled in the form
        if not sold_price:
            sold_price = 0

        if not reason_replace:
            reason_replace = "Not specified"

        # Round up sold price
        sold_price = round(float(sold_price), 2)

        if id:

            # Query data from database
            items = db.execute("SELECT * FROM items WHERE id = ?", id)

            # Define variables for converting to history table
            user_id = items[0]['user_id']
            item = items[0]['item']
            price = items[0]['price']
            book_value = items[0]['book_value']
            bought = items[0]['bought']
            sold = str(date.today())
            brand = items[0]['brand']
            seller = items[0]['seller']
            profit = round(float(sold_price) - float(book_value), 2)

            db.execute("INSERT INTO history (user_id, item, price, book_value, sold_price, bought, sold, brand, seller, reason_replace, profit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        user_id, item, price, book_value, sold_price, bought, sold, brand, seller, reason_replace, profit)

            db.execute("DELETE FROM items WHERE id = ?", id)

            # Inform successfully
            flash("Item replaced!")

            return redirect("/history")


@app.route("/history")
@login_required
def history():
    """ Allow user to see history of items replaced """
    items = db.execute("SELECT * FROM history where user_id = ? ORDER BY sold DESC", session['user_id'])
    return render_template("history.html", items=items)


@app.route("/items")
@login_required
def items():
    """Update till current day and show items details"""

    # Update today variable
    today = str(date.today())

    # Query for item list
    items = db.execute("SELECT * FROM items WHERE user_id = ?", session['user_id'])

    for item in items:

        # Get info from database
        bought = item['bought']
        price = item['price']
        depr_per_month = item['depreciation_per_month']

        # Calculate the changing variable in database
        used = int((days_between(bought, today))/30)
        book_value = round(float(price) - (depr_per_month * used), 2)
        savings = round(depr_per_month * used, 2)

        # Check if the item lifetime is expired or not
        expire = days_between(item['should_replace'], today)

        # If expired, set book_value and depr per month to 0
        if expire >= 0:
            depr_per_month = 0
            book_value = 0
            savings = price

        # Update the variable
        db.execute("UPDATE items SET used = ?, depreciation_per_month = ?, book_value = ?, savings_should_have = ? WHERE id = ? AND user_id = ?",
                    used, depr_per_month, book_value, savings, item['id'], session['user_id'])

    new_items = db.execute("SELECT * FROM items WHERE user_id = ? ORDER BY should_replace", session['user_id'])

    return render_template("items.html", items=new_items)


@app.route("/items_repl")
@login_required
def items_repl():
    """Show items need to be replace in 30 days"""

    # Update today variable
    today= str(date.today())

    # Query for item list
    items = db.execute("SELECT * FROM items WHERE user_id = ?", session['user_id'])

    for item in items:

        # Get info from database
        bought = item['bought']
        price = item['price']
        depr_per_month = item['depreciation_per_month']

        # Calculate the changing variable in database
        used = int((days_between(bought, today))/30)
        book_value = round(float(price) - (depr_per_month * used), 2)
        savings = depr_per_month *used

        # Check if the item lifetime is expired or not
        expire = days_between(item['should_replace'], today)

        # If expired, set book_value and depr per month to 0
        if expire >= 0:
            depr_per_month = 0
            book_value = 0
            savings = price

        # Update the variable
        db.execute("UPDATE items SET used = ?, depreciation_per_month = ?, book_value = ?, savings_should_have = ? WHERE id = ? AND user_id = ?",
                    used, depr_per_month, book_value, savings, item['id'], session['user_id'])



    # Select items which need to be replace in 30 days
    items_repl = db.execute("SELECT * FROM items WHERE (JULIANDAY(DATE(should_replace)) - JULIANDAY(DATE('now'))) <= 30 AND user_id = ? ORDER BY should_replace", session['user_id'])

    # Render the template to show items need to be replaced
    return render_template("items_repl.html", items=items_repl)


@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """Let user delete all item's information"""

    # If user reached route via POST (by submitting form)
    if request.method == "POST":
        id = request.form.get("id")

        if id:
            db.execute("DELETE FROM items WHERE id = ?", id)

            # Inform deleting successfully
            flash("Item deleted")

            # Redirect user back to item
            return redirect("/items")


@app.route("/delete_history", methods=["POST"])
@login_required
def delete_history():
    """Let user delete all item's information in history"""

    # If user reached route via POST (by submitting form)
    if request.method == "POST":
        id = request.form.get("id")

        if id:
            db.execute("DELETE FROM history WHERE id = ?", id)

            # Inform deleting successfully
            flash("Item deleted")

            # Redirect user back to item
            return redirect("/history")


@app.route("/pre_edit", methods=["POST"])
@login_required
def pre_edit():
    """Let user enter edit mode of their item's information"""

    # If user reached route via POST (as by submiting form)
    if request.method == "POST":

        id = request.form.get("id")

        # Get item's information from database
        items = db.execute("SELECT * FROM items WHERE id = ?", id)

        return render_template("edit.html", items=items)


@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Let user modify their item's information"""

    # If user reached route via POST (by submiting form)
    if request.method == "POST":

        # define variable
        id = request.form.get("id")
        item = (request.form.get("item_name")).lower()
        price = request.form.get("price")
        bought = request.form.get("bought")
        life = request.form.get("life")
        warranty = request.form.get("warranty")
        brand = (request.form.get("brand")).upper()
        seller = (request.form.get("seller")).upper()
        maint = request.form.get("maint")

        # Get item's information from database
        items = db.execute("SELECT * FROM items WHERE id = ?", id)

        # Get old variable
        old_item = items[0]['item']
        old_price = items[0]['price']
        old_bought = items[0]['bought']
        old_life = int(days_between(old_bought, items[0]['should_replace'])/30)
        old_warranty = items[0]['warranty']
        old_brand = items[0]['brand']
        old_seller = items[0]['seller']
        old_maint = items[0]['maint']

        # check if user enter which field
        if not item:
            item = old_item
        if not price:
            price = old_price
        if not bought:
            bought = old_bought
        if not life:
            life = old_life
        if not warranty:
            warranty = old_warranty
        if not brand:
            brand = old_brand
        if not seller:
            seller = old_seller
        if not maint:
            maint = old_maint

        # Round up price and maint:
        price = round(float(price), 2)
        maint = round(float(maint), 2)

        # calculate depreciate per month
        depr_per_month = round(float(price)/(int(life)), 2)

        # the date should be replace by the lifetime given by user
        should_replace = (datetime.strptime(bought, '%Y-%m-%d') + timedelta(days=30*int(life))).strftime('%Y-%m-%d')

        # define other variable
        today = str(date.today())

        # number of months used from the bought date
        used = int((days_between(bought, today))/30)


        # calculate book value left after depreciation
        book_value = float(price) - (depr_per_month * used)

        # saving should have
        savings = depr_per_month*used

        # update new information to the items table
        db.execute("UPDATE items SET item = ?, price = ?, bought = ?, used = ?, should_replace = ?, depreciation_per_month = ?, book_value = ?, savings_should_have = ?, brand = ?, seller = ?, warranty = ?, maint = ? WHERE id = ? AND user_id = ?",
                    item, price, bought, used, should_replace, depr_per_month, book_value, savings, brand, seller, warranty, maint, id, session['user_id'])

        # Inform successfully
        flash("Item updated!")

        # Redirect user back to homepage
        return redirect("/items")


@app.route("/add_wishlist", methods=["GET", "POST"])
@login_required
def add_wishlist():
    """Let user add item to wishlist"""

    # if user reached route via POST (as by submitting form)
    if request.method == "POST":

        # define variable
        item = (request.form.get("item_name")).lower()
        price = request.form.get("price")
        life = request.form.get("life")
        brand = (request.form.get("brand")).upper()
        seller = (request.form.get("seller")).upper()
        maint = request.form.get("maint")

        # Check if user enter all required field
        if not item:
            return render_template("error.html", message="Missing item's name")
        if not price:
            return render_template("error.html", message="Missing price")
        if not life:
            return render_template("error.html", message="Missing lifetime of item")

        # If some nonessential information was not filled by user, then automatically fill in for them
        if not brand:
            brand = "Not specified"
        if not seller:
            seller = "Not specified"
        if not maint:
            maint = 0

        # Round up price and maint:
        price = round(float(price), 2)
        maint = round(float(maint), 2)

        # calculate depreciate per month
        depr = round(float(price)/(int(life)), 2)

        # calculate monthly_cost

        monthly_cost = maint + depr

        # insert new item information to the items table
        db.execute("INSERT INTO wishlist (user_id, item, price, life, brand, seller, maint, depr, monthly_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    session['user_id'], item, price, life, brand, seller, maint, depr, monthly_cost)

        # Inform successfully
        flash("Item added!")

        # Redirect user back to homepage
        return redirect("/wishlist")

    # if user reached route via GET (by click link)
    else:
        return render_template("add_wishlist.html")


@app.route("/wishlist")
@login_required
def wishlist():
    """Show wishlist items lists"""

    # Query for item list
    items = db.execute("SELECT * FROM wishlist WHERE user_id = ?", session['user_id'])

    return render_template("wishlist.html", items=items)


@app.route("/delete_wishlist", methods=["POST"])
@login_required
def delete_wishlist():
    """Let user delete all item's information in wishlist"""

    # If user reached route via POST (by submitting form)
    if request.method == "POST":
        id = request.form.get("id")

        if id:
            db.execute("DELETE FROM wishlist WHERE id = ?", id)

            # Inform deleting successfully
            flash("Item deleted")

            # Redirect user back to item
            return redirect("/wishlist")


@app.route("/pre_edit_wishlist", methods=["POST"])
@login_required
def pre_edit_wishlist():
    """Let user enter edit mode of their item's information"""

    # If user reached route via POST (as by submiting form)
    if request.method == "POST":

        id = request.form.get("id")

        # Get item's information from database
        items = db.execute("SELECT * FROM wishlist WHERE id = ?", id)

        return render_template("edit_wishlist.html", items=items)


@app.route("/edit_wishlist", methods=["GET", "POST"])
@login_required
def edit_wishlist():
    """Let user modify their item's information in wishlist"""

    # If user reached route via POST (by submiting form)
    if request.method == "POST":

        # define variable
        id = request.form.get("id")
        item = (request.form.get("item_name")).lower()
        price = request.form.get("price")
        life = request.form.get("life")
        brand = (request.form.get("brand")).upper()
        seller = (request.form.get("seller")).upper()
        maint = request.form.get("maint")

        # Get item's information from database
        items = db.execute("SELECT * FROM wishlist WHERE id = ?", id)

        # Get old variable
        old_item = items[0]['item']
        old_price = items[0]['price']
        old_life = items[0]['life']
        old_brand = items[0]['brand']
        old_seller = items[0]['seller']
        old_maint = items[0]['maint']

        # check if user enter which field
        if not item:
            item = old_item
        if not price:
            price = old_price
        if not life:
            life = old_life
        if not brand:
            brand = old_brand
        if not seller:
            seller = old_seller
        if not maint:
            maint = old_maint

        # Round up price and maint:
        price = round(float(price), 2)
        maint = round(float(maint), 2)

        # calculate depreciate per month
        depr = round(float(price)/(int(life)), 2)

        # calculate monthly_cost

        monthly_cost = maint + depr

        # update new information to the items table
        db.execute("UPDATE wishlist SET item = ?, price = ?, life = ?, brand = ?, seller = ?, maint = ?, depr = ?, monthly_cost = ?, WHERE id = ? AND user_id = ?",
                    item, price, life, brand, seller, maint, depr, monthly_cost, id, session['user_id'])

        # Inform successfully
        flash("Item updated!")

        # Redirect user back to homepage
        return redirect("/wishlist")


@app.route("/pre_add_item_from_wishlist", methods=["POST"])
@login_required
def pre_add_item_from_wishlist():
    """Allow user to enter the mode to add item from wishlist to item list"""

    # If user reached route via POST (as by submiting form
    if request.method == "POST":
        id = request.form.get("id")

        # Get information from database
        items = db.execute("SELECT * FROM wishlist WHERE id = ?", id)

        return render_template("add_item_from_wishlist.html", items=items)


@app.route("/add_item_from_wishlist", methods=["POST"])
@login_required
def add_item_from_wishlist():

    # If user reached route via POST (as by submiting form)
    if request.method == "POST":

        # Get info from the form
        id = request.form.get("id")
        warranty = request.form.get("warranty")

        if id:

            # Query data from database
            items = db.execute("SELECT * FROM wishlist WHERE id = ?", id)

            # Define variables for converting to history table
            item = items[0]['item']
            price = items[0]['price']
            life = items[0]['life']
            brand = items[0]['brand']
            seller = items[0]['seller']
            maint = items[0]['maint']
            depr = items[0]['depr']

            # Round up:
            price = round(float(price), 2)
            maint = round(float(maint), 2)
            depr = round(float(depr), 2)

            # define bought date
            bought = str(date.today())

            # the date should be replace by the lifetime given by user
            should_replace = (datetime.strptime(bought, '%Y-%m-%d') + timedelta(days=30*int(life))).strftime('%Y-%m-%d')

            # define other variable
            today = str(date.today())

            # number of months used from the bought date
            used = int((days_between(bought, today))/30)

            # calculate book value left after depreciation
            book_value = float(price) - (depr * used)

            # saving should have
            savings = depr * used

            # insert new item information to the items table
            db.execute("INSERT INTO items (user_id, item, price, bought, used, should_replace, depreciation_per_month, book_value, savings_should_have, warranty, brand, seller, maint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        session['user_id'], item, price, bought, used, should_replace, depr, book_value, savings, warranty, brand, seller, maint)

            # delete item from wishlist
            db.execute("DELETE FROM wishlist WHERE id = ?", id)

            # Inform successfully
            flash("Item added!")

            # Redirect user back to homepage
            return redirect("/items")


"""Allow user to sort table (not implement yet)"""
