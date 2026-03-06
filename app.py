import os
import json
import smtplib
from email.message import EmailMessage
import google.generativeai as genai
from urllib import error as urllib_error
from urllib import request as urllib_request

import pandas as pd
from logistics_runner import LogisticsRunner
from flask import (
    Flask, render_template,
    request, redirect,
    url_for, flash, jsonify, g
)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import (
    LoginManager, UserMixin,
    login_user, logout_user,
    login_required, current_user
)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import secrets
from datetime import datetime

from dotenv import load_dotenv

# ----------------- LOAD ENV -----------------
load_dotenv()


def env_first(*keys, default=None):
    for key in keys:
        raw_value = os.getenv(key)
        if raw_value is None:
            continue
        value = raw_value.strip()
        if value:
            return value
    return default


def env_bool(*keys, default=False):
    value = env_first(*keys)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(*keys, default=0):
    value = env_first(*keys)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


app_env = env_first("APP_ENV", "FLASK_ENV", default="development").strip().lower()
is_production = app_env == "production"
debug_mode = env_bool("FLASK_DEBUG", default=False)
if is_production:
    debug_mode = False

app = Flask(__name__)
app.secret_key = env_first("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is required")

# ----------------- DATABASE CONFIG -----------------
def normalize_database_uri(uri):
    if not uri:
        return uri
    # Railway often provides mysql://..., but SQLAlchemy needs mysql+pymysql://...
    if uri.startswith("mysql://"):
        return "mysql+pymysql://" + uri[len("mysql://"):]
    return uri


database_uri = normalize_database_uri(env_first("SQLALCHEMY_DATABASE_URI", "DATABASE_URL"))
if not database_uri:
    database_uri = normalize_database_uri(env_first("MYSQL_PUBLIC_URL", "MYSQL_URL"))

if not database_uri:
    # Prefer Railway-style keys first because MYSQL_HOST can be "db" from local compose.
    db_user = env_first("MYSQLUSER", "MYSQL_USER")
    db_password = env_first("MYSQLPASSWORD", "MYSQL_PASSWORD")
    db_host = env_first("MYSQLHOST", "MYSQL_HOST")
    db_port = env_first("MYSQLPORT", "MYSQL_PORT", default="3306")
    db_name = env_first("MYSQLDATABASE", "MYSQL_DATABASE")

    if is_production and db_host == "db":
        raise RuntimeError(
            "Invalid database host 'db' for production. "
            "Set SQLALCHEMY_DATABASE_URI, MYSQL_PUBLIC_URL, MYSQL_URL, "
            "or MYSQLHOST to your Railway database host."
        )

    missing = [
        name for name, value in (
            ("MYSQLUSER/MYSQL_USER", db_user),
            ("MYSQLPASSWORD/MYSQL_PASSWORD", db_password),
            ("MYSQLHOST/MYSQL_HOST", db_host),
            ("MYSQLDATABASE/MYSQL_DATABASE", db_name),
        ) if not value
    ]
    if missing:
        raise RuntimeError(f"Missing database environment variables: {', '.join(missing)}")

    database_uri = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

base_url = env_first("BASE_URL")
if not base_url:
    railway_domain = env_first("RAILWAY_PUBLIC_DOMAIN")
    if railway_domain:
        base_url = railway_domain.strip()
        if not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"
    else:
        base_url = "http://localhost:5000"
base_url = base_url.rstrip("/")

app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 280,
}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["REMEMBER_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = env_bool("SESSION_COOKIE_SECURE", default=is_production)
app.config["REMEMBER_COOKIE_SECURE"] = env_bool("REMEMBER_COOKIE_SECURE", default=is_production)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Add security headers to prevent caching
@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


login_manager = LoginManager(app)
login_manager.login_view = "form2"

serializer = URLSafeTimedSerializer(app.secret_key)

# ----------------- MAIL CONFIG -----------------
app.config["MAIL_SERVER"] = env_first("MAIL_SERVER", default="smtp.gmail.com")
app.config["MAIL_PORT"] = env_int("MAIL_PORT", default=587)
app.config["MAIL_USE_TLS"] = env_bool("MAIL_USE_TLS", default=True)
app.config["MAIL_USE_SSL"] = env_bool("MAIL_USE_SSL", default=False)
app.config["MAIL_USERNAME"] = env_first("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = env_first("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = env_first("MAIL_DEFAULT_SENDER", "MAIL_USERNAME")
app.config["MAIL_TIMEOUT"] = env_int("MAIL_TIMEOUT", default=8)
app.config["EMAIL_BACKEND"] = env_first("EMAIL_BACKEND")
app.config["RESEND_API_KEY"] = env_first("RESEND_API_KEY")
app.config["RESEND_API_BASE"] = env_first("RESEND_API_BASE", default="https://api.resend.com")
app.config["RESEND_FROM_EMAIL"] = env_first(
    "RESEND_FROM_EMAIL",
    "MAIL_DEFAULT_SENDER",
    "MAIL_USERNAME",
)

if not app.config["EMAIL_BACKEND"]:
    app.config["EMAIL_BACKEND"] = "resend" if app.config["RESEND_API_KEY"] else "smtp"
else:
    app.config["EMAIL_BACKEND"] = app.config["EMAIL_BACKEND"].strip().lower()

if app.config["MAIL_USE_TLS"] and app.config["MAIL_USE_SSL"]:
    raise RuntimeError("MAIL_USE_TLS and MAIL_USE_SSL cannot both be enabled")


def send_reset_email(recipient_email, reset_link):
    subject = "Password Reset Request"
    text_body = (
        "Hi,\n\n"
        "We received a request to reset your password.\n\n"
        "Use this link within 15 minutes:\n"
        f"{reset_link}\n\n"
        "If you didn't request this, ignore this email."
    )
    html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #1f2937;">
                <p>Hi,</p>
                <p>We received a request to reset your password.</p>
                <p>This link is valid for 15 minutes.</p>
                <p style="margin: 24px 0;">
                    <a
                        href="{reset_link}"
                        style="
                            display: inline-block;
                            padding: 12px 24px;
                            background-color: #1d4ed8;
                            color: #ffffff;
                            text-decoration: none;
                            border-radius: 4px;
                            border: 1px solid #1e40af;
                            font-weight: bold;
                        "
                    >
                        Reset Password
                    </a>
                </p>
                <p style="font-size: 14px; color: #4b5563;">
                    If the button does not work, paste this link in your browser:
                    <br>
                    <a href="{reset_link}" style="color: #1d4ed8;">{reset_link}</a>
                </p>
                <p>If you didn't request this, ignore this email.</p>
            </body>
        </html>
    """

    backend = app.config["EMAIL_BACKEND"]
    if backend == "resend":
        send_reset_email_via_resend(recipient_email, subject, text_body, html_body)
        return
    if backend == "smtp":
        send_reset_email_via_smtp(recipient_email, subject, text_body, html_body)
        return
    raise RuntimeError("Unsupported EMAIL_BACKEND. Use 'smtp' or 'resend'.")


def send_reset_email_via_smtp(recipient_email, subject, text_body, html_body):
    sender = app.config["MAIL_DEFAULT_SENDER"] or app.config["MAIL_USERNAME"]
    if not sender:
        raise RuntimeError("MAIL_DEFAULT_SENDER or MAIL_USERNAME is required")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    if app.config["MAIL_USE_SSL"]:
        with smtplib.SMTP_SSL(
            app.config["MAIL_SERVER"],
            app.config["MAIL_PORT"],
            timeout=app.config["MAIL_TIMEOUT"],
        ) as smtp_conn:
            if app.config["MAIL_USERNAME"] and app.config["MAIL_PASSWORD"]:
                smtp_conn.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            smtp_conn.send_message(message)
    else:
        with smtplib.SMTP(
            app.config["MAIL_SERVER"],
            app.config["MAIL_PORT"],
            timeout=app.config["MAIL_TIMEOUT"],
        ) as smtp_conn:
            smtp_conn.ehlo()
            if app.config["MAIL_USE_TLS"]:
                smtp_conn.starttls()
                smtp_conn.ehlo()
            if app.config["MAIL_USERNAME"] and app.config["MAIL_PASSWORD"]:
                smtp_conn.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            smtp_conn.send_message(message)


def send_reset_email_via_resend(recipient_email, subject, text_body, html_body):
    api_key = app.config["RESEND_API_KEY"]
    sender = app.config["RESEND_FROM_EMAIL"] or app.config["MAIL_DEFAULT_SENDER"] or app.config["MAIL_USERNAME"]
    if not api_key:
        raise RuntimeError("RESEND_API_KEY is required when EMAIL_BACKEND=resend")
    if not sender:
        raise RuntimeError("RESEND_FROM_EMAIL or MAIL_DEFAULT_SENDER is required")

    payload = {
        "from": sender,
        "to": [recipient_email],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }
    request_body = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(
        url=f"{app.config['RESEND_API_BASE'].rstrip('/')}/emails",
        data=request_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib_request.urlopen(request, timeout=app.config["MAIL_TIMEOUT"]) as response:
            status = getattr(response, "status", response.getcode())
            if status >= 400:
                raise RuntimeError(f"Resend API failed with status {status}")
    except urllib_error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend API HTTP {exc.code}: {error_body[:240]}") from exc
    except urllib_error.URLError as exc:
        raise RuntimeError(f"Resend API network error: {exc.reason}") from exc


def is_email_service_configured():
    backend = app.config["EMAIL_BACKEND"]
    if backend == "smtp":
        return bool(app.config["MAIL_USERNAME"] and app.config["MAIL_PASSWORD"])
    if backend == "resend":
        sender = app.config["RESEND_FROM_EMAIL"] or app.config["MAIL_DEFAULT_SENDER"] or app.config["MAIL_USERNAME"]
        return bool(app.config["RESEND_API_KEY"] and sender)
    return False




# ----------------- USER MODEL -----------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    keys = db.relationship('APIKey', backref='user', lazy=True, cascade="all, delete-orphan")

    def __init__(self, full_name, email, password_hash):
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash

    def get_id(self):
        return self.id

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False


class APIKey(db.Model):
    __tablename__ = 'api_keys'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, user_id):
        self.user_id = user_id
        self.key = secrets.token_hex(32)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ----------------- SINGLE FORM ROUTE -----------------
@app.route("/", methods=["GET", "POST"])
def form2():
    if request.method == "POST":
        action = request.form.get("action", "").strip().lower()
        if action not in {"register", "login", "forgot"}:
            flash("Invalid request.", "danger")
            return redirect(url_for("form2"))

        # ----------------- REGISTER -----------------
        if action == "register":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()
            confirm_password = request.form.get("confirmPassword", "").strip()

            if not name or not email or not password or not confirm_password:
                flash("Name, email, password, and confirm password are required.", "danger")
                return redirect(url_for("form2"))

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return redirect(url_for("form2"))

            existing_user = User.query.filter_by(email=email).first()

            if existing_user:
                flash("Account already exists. Please login or reset password.", "warning")
                return redirect(url_for("form2"))

            hashed = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = User(full_name=name, email=email, password_hash=hashed)
            db.session.add(new_user)
            db.session.commit()

            flash("Account created successfully! Please login.", "success")

        # ----------------- LOGIN -----------------
        elif action == "login":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "").strip()

            if not email or not password:
                flash("Email and password are required.", "danger")
                return redirect(url_for("form2"))

            user = User.query.filter_by(email=email).first()

            if user and bcrypt.check_password_hash(user.password_hash, password):
                login_user(user)
                flash(f"Welcome, {user.full_name}!", "success")
                return redirect(url_for("dashboard"))

            flash("Invalid credentials", "danger")

        # ----------------- FORGOT PASSWORD -----------------
        elif action == "forgot":
            email = request.form.get("email", "").strip().lower()

            if not email:
                flash("Email is required.", "danger")
                return redirect(url_for("form2"))

            user = User.query.filter_by(email=email).first()

            if not user:
                flash("No account found with this email.", "danger")
                return redirect(url_for("form2"))

            token = serializer.dumps(email, salt="reset-password")
            reset_link = f"{base_url}/reset/{token}"

            if not is_email_service_configured():
                flash("Email service is not configured. Contact support.", "danger")
                return redirect(url_for("form2"))

            user.reset_token = token
            db.session.commit()

            try:
                send_reset_email(email, reset_link)
            except Exception as e:
                app.logger.exception(
                    "Failed to send reset email to %s via %s",
                    email,
                    app.config["EMAIL_BACKEND"],
                )
                try:
                    user.reset_token = None
                    db.session.commit()
                except Exception:
                    app.logger.exception("Failed to clear reset token for %s after mail error", email)

                flash(f"Could not send reset email. The mail server reported an error: {e}", "danger")
                return redirect(url_for("form2"))

            flash("Password reset link sent to your email!", "info")

        return redirect(url_for("form2"))

    section = request.args.get("next", "register")
    if section not in {"register", "login", "forgot"}:
        section = "register"
    return render_template("form2.html", section=section)

# ----------------- DASHBOARD -----------------
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", current_user=current_user)


@app.route("/api-keys", methods=["GET", "POST"])
@login_required
def api_keys():
    if request.method == "POST":
        new_key = APIKey(user_id=current_user.id)
        db.session.add(new_key)
        db.session.commit()
        flash(f"New API Key generated: {new_key.key}", "success")
        return redirect(url_for("api_keys"))

    keys = APIKey.query.filter_by(user_id=current_user.id).order_by(APIKey.created_at.desc()).all()
    return render_template("api_keys.html", current_user=current_user, keys=keys)


@app.route("/api-keys/<int:key_id>/delete", methods=["POST"])
@login_required
def delete_api_key(key_id):
    key_to_delete = APIKey.query.get_or_404(key_id)
    if key_to_delete.user_id != current_user.id:
        flash("You do not have permission to delete this key.", "danger")
        return redirect(url_for("api_keys"))
    
    db.session.delete(key_to_delete)
    db.session.commit()
    flash("API Key deleted successfully.", "success")
    return redirect(url_for("api_keys"))


# ----------------- API ROUTES -----------------
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header is missing or invalid'}), 401
        
        api_key_str = auth_header.split(' ')[1]
        api_key = APIKey.query.filter_by(key=api_key_str).first()
        
        if not api_key:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Update the last used timestamp
        api_key.last_used_at = datetime.utcnow()
        db.session.commit()
        
        # Pass the user associated with the key to the route
        g.api_user = api_key.user
        return f(*args, **kwargs)
    return decorated_function

@app.route("/api/analyze", methods=["POST"])
@require_api_key
def api_analyze():
    if 'dataset' not in request.files:
        return jsonify({'error': 'No dataset file provided'}), 400
    
    file = request.files['dataset']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.csv'):
        try:
                df = pd.read_csv(file)

                # Pass the DataFrame to the runner
                runner = LogisticsRunner(data=df)
                results = runner.run_experiment()

                # Clean up results for JSON serialization
                if 'training_history' in results:
                    for key, value in results['training_history'].items():
                        results['training_history'][key] = [float(v) for v in value]
                
                return jsonify({
                    'message': 'Analysis successful',
                    **results
                }), 200
        except Exception as e:
                app.logger.error(f"API Analysis Error: {e}")
                return jsonify({'error': 'An error occurred during analysis', 'details': str(e)}), 500

    return jsonify({'error': 'Invalid file type. Please upload a .csv file'}), 400


# ----------------- CHATBOT ROUTES -----------------

@app.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html")

@app.route("/ask", methods=["POST"])
@login_required
def ask():
    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    # --- Real AI Response (Phase 2) ---
    try:
        # Configure the generative AI library with the API key
        gemini_api_key = env_first("GEMINI_API_KEY")
        if not gemini_api_key:
            return jsonify({"error": "GEMINI_API_KEY is not configured on the server."}), 500
        
        genai.configure(api_key=gemini_api_key)
        
        # Create the model
        model_name = 'gemini-pro-latest'
        app.logger.info(f"Attempting to use Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        # Send the message and get the response
        response = model.generate_content(user_message)
        
        bot_response = response.text

    except Exception as e:
        app.logger.error(f"Gemini API Error: {e}")
        bot_response = "Sorry, I'm having trouble connecting to my brain right now."
    # --------------------------------

    return jsonify({"response": bot_response})





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
    except (SignatureExpired, BadSignature):
        flash("Invalid or expired token", "danger")
        return redirect(url_for("form2"))

    user = User.query.filter_by(email=email, reset_token=token).first()

    if not user:
        flash("Invalid or already-used token", "danger")
        return redirect(url_for("form2"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirmPassword", "").strip()

        if not password or not confirm_password:
            flash("Both password fields are required.", "danger")
            return redirect(request.url)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(request.url)

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        user.password_hash = hashed
        user.reset_token = None
        db.session.commit()

        flash("Password updated successfully!", "success")
        return redirect(url_for("form2"))

    return render_template("reset.html")


# ----------------- ANALYSIS ROUTE -----------------
@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if 'dataset' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['dataset']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        try:
                df = pd.read_csv(file)
                
                # Prepare a preview of the dataframe for the frontend
                # Convert to a dictionary for JSON serialization
                data_preview = df.head(100).to_dict(orient='records')

                # Initialize and run the logistics pipeline
                runner = LogisticsRunner(data=df)
                results = runner.run_experiment()
                results['data_preview'] = data_preview

                # Clean up results for JSON serialization
                if 'training_history' in results:
                    for key, value in results['training_history'].items():
                        results['training_history'][key] = [float(v) for v in value]

                return jsonify(results)

        except Exception as e:
                app.logger.error(f"Analysis failed: {e}")
                return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type. Please upload a CSV."}), 400


# ----------------- RUN -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(env_first("PORT", default="5000")), debug=debug_mode)