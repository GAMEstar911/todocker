import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Mail, Message
import MySQLdb.cursors
from dotenv import load_dotenv

# ----------------- LOAD ENV -----------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ----------------- DATABASE CONFIG -----------------
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST", "db")
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DATABASE")

mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "form2"

serializer = URLSafeTimedSerializer(app.secret_key)

# ----------------- MAIL CONFIG -----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_USERNAME")

mail = Mail(app)
app.extensions['mail'].debug = 1

# ----------------- USER MODEL -----------------
class User(UserMixin):
    def __init__(self, id, email, password, name):
        self.id = id
        self.email = email
        self.password = password
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
    user = cursor.fetchone()
    if user:
        return User(user["id"], user["email"], user["password_hash"], user["full_name"])
    return None

# ----------------- SINGLE FORM ROUTE -----------------
@app.route("/", methods=["GET", "POST"])
def form2():
    # --- ONE FINAL VERIFICATION LINE ---
    print(">>> DOCKER WATCH: FILE SYNC IS SUCCESSFUL! <<<")  
    if request.method == "POST":
        action = request.form.get("action")

        # ----------------- REGISTER -----------------
        if action == "register":
            name = request.form["name"].strip()
            email = request.form["email"].strip().lower()
            password = request.form["password"].strip()

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Account already exists. Please login or reset password.", "warning")
                return redirect(url_for("form2"))

            hashed = bcrypt.generate_password_hash(password).decode("utf-8")
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s,%s,%s)",
                (name, email, hashed)
            )
            mysql.connection.commit()
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("form2", next="login"))

        # ----------------- LOGIN -----------------
        elif action == "login":
            email = request.form["email"].strip().lower()
            password = request.form["password"].strip()

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user["password_hash"], password):
                login_user(User(user["id"], user["email"], user["password_hash"], user["full_name"]))
                flash(f"Welcome, {user['full_name']}!", "success")
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials", "danger")
                return redirect(url_for("form2"))

        # ----------------- FORGOT PASSWORD -----------------
        elif action == "forgot":
            email = request.form["email"].strip().lower()
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()

            if not user:
                flash("No account found with this email.", "danger")
                return redirect(url_for("form2"))

            token = serializer.dumps(email, salt="reset-password")
            cursor.execute("UPDATE users SET reset_token=%s WHERE email=%s", (token, email))
            mysql.connection.commit()

            reset_link = f"{os.getenv('BASE_URL')}/reset/{token}"

            msg = Message(
                "Password Reset Request",
                recipients=[email]
            )
            msg.body = f"Hi,\n\nClick the link below to reset your password (valid for 15 minutes):\n{reset_link}\n\nIf you didn't request this, ignore this email."
            
            mail.send(msg)

            flash("Password reset link sent to your email!", "info")
            return redirect(url_for("form2", next="login"))

    section = request.args.get("next", "register")
    return render_template("form2.html", section=section)

# ----------------- DASHBOARD -----------------
@app.route("/dashboard")
@login_required
def dashboard():
    return f"Welcome {current_user.email}! <br><a href='/logout'>Logout</a>"

# ----------------- LOGOUT -----------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("form2"))

# ----------------- RESET PASSWORD -----------------
@app.route("/reset/<token>", methods=["GET", "POST"])
def reset(token):
    try:
        email = serializer.loads(token, salt="reset-password", max_age=900)
    except:
        flash("Invalid or expired token", "danger")
        return redirect(url_for("form2"))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE email=%s AND reset_token=%s", (email, token))
    user = cursor.fetchone()

    if not user:
        flash("Invalid or already-used token", "danger")
        return redirect(url_for("form2"))

    if request.method == "POST":
        password = request.form["password"]
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        cursor.execute(
            "UPDATE users SET password_hash=%s, reset_token=NULL WHERE email=%s",
            (hashed, email)
        )
        mysql.connection.commit()
        flash("Password updated successfully!", "success")
        return redirect(url_for("form2"))

    return render_template("reset.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
