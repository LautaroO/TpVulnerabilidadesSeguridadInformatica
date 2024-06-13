from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import binascii
import smtplib
import uuid
import yaml
import os
from flask_bcrypt import Bcrypt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["DEBUG"] = True
bcrypt = Bcrypt(app)


# Database connection
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def cleanDB():
    if os.path.exists("database.db"):
        os.remove("database.db")


# Initialize database
def init_db():
    cleanDB()

    conn = get_db_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT,
            password TEXT,
            recovery_token TEXT,
            role TEXT
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT
        )
    """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            post_id INTEGER NOT NULL,
            username TEXT NULL,
            FOREIGN KEY(post_id) REFERENCES posts(id)
        )
    """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO users (
            username,
            email,
            password,
            role)
        VALUES (?,?,?,?)
    """,
        (
            "admin",
            "admin@admin.com",
            bcrypt.generate_password_hash("admin").decode("utf-8"),
            "admin",
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO users (
            username,
            email,
            password,
            role)
        VALUES (?,?,?,?)
    """,
        (
            "user1",
            "user@admin.com",
            bcrypt.generate_password_hash("123456").decode("utf-8"),
            "premium",
        ),
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO users (
            username,
            email,
            password,
            role)
        VALUES (?,?,?,?)
    """,
        (
            "guest",
            "user@admin.com",
            bcrypt.generate_password_hash("123456").decode("utf-8"),
            "guest",
        ),
    )

    conn.execute(
        """
        INSERT INTO posts (title, content)
        VALUES(?, ?)
    """,
        ("Bienvenido al blog!", "Pronto estare subiendo más contenido!"),
    )
    conn.commit()
    conn.close()


def decodeTextFromBase64(base64Text):
    if not isinstance(base64Text, str):
        return encodeTextInBase64("guest")

    try:
        decoded_text = base64.b64decode(base64Text).decode("utf-8")
        return decoded_text
    except (binascii.Error, ValueError, TypeError):
        return None  # En caso de error, devuelve None


def encodeTextInBase64(text):
    try:
        if not text:
            raise ValueError("Input text is empty")
        encoded_text = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        base64.b64decode(encoded_text).decode("utf-8")
        return encoded_text
    except (TypeError, ValueError, base64.binascii.Error) as e:
        print(f"UN ERROR: {e}")
        return getCurrentSession()


def getCurrentSession():
    if "role" not in session or session["role"] != "admin":
        return "guest"
    else:
        return "admin"


@app.context_processor
def utility_processorrs():
    return dict(encode=encodeTextInBase64, decode=decodeTextFromBase64)


@app.route("/")
def index():
    role = getCurrentSession()
    encoded_role = encodeTextInBase64(role)
    return render_template("index.html", role=encoded_role)


@app.route("/posts")
def posts():
    role = request.args.get("role")

    if role is None:
        decodedRole = "guest"
    else:
        decodedRole = decodeTextFromBase64(role)
        if decodedRole is None:
            decodedRole = "guest"
    # If the role parameter is not 'guest' or 'admin', redirect to the same route with 'role=guest'
    if decodedRole not in ["guest", "admin"]:
        return redirect(url_for("posts", role=encodeTextInBase64("guest")))
    filter_text = request.args.get("filter", "")
    conn = get_db_connection()
    try:
        if filter_text:
            # Esta es una forma insegura de ejecutar la consulta, solo para propósitos educativos o de prueba
            posts = conn.execute(
                "SELECT * FROM posts WHERE content LIKE '%" + filter_text + "%'"
            ).fetchall()
        else:
            posts = conn.execute("SELECT * FROM posts").fetchall()
        conn.close()
        return render_template(
            "posts.html",
            role=role,
            posts=posts,
            error=None,
        )
    except Exception as e:
        error_message = str(e)
        return render_template("posts.html", posts=[], error=error_message)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if user:
            if bcrypt.check_password_hash(user["password"], password):
                session["user_id"] = user["id"]
                # session["user_id"] = encriptarBase64(username, rol)
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/post/<int:post_id>", methods=["POST"])
def commentPost(post_id):
    conn = get_db_connection()
    content = request.form["comment"]
    username = session.get("username", "Anónimo")
    query = f"""
        INSERT INTO comments (post_id, content, username)
        VALUES({post_id}, '{content}', '{username}')
    """
    post = conn.executescript(query)
    conn.close()
    return render_template("post.html", post=post)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user_id" not in session or "role" not in session or session["role"] != "admin":
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    return render_template("admin.html")


@app.route("/post/<int:post_id>", methods=["GET"])
def post(post_id):
    try:
        conn = get_db_connection()
        post = conn.execute(f"""SELECT * FROM posts WHERE id = {post_id};""").fetchone()
        comments = conn.execute(
            f"""SELECT * FROM comments WHERE post_id = {post_id};"""
        ).fetchall()
        conn.close()
        return render_template("post.html", post=post, comments=comments)
    except Exception as e:
        error_message = str(e)
        return render_template("posts.html", posts=[], error=error_message)


# Password recovery
def send_recovery_email(emailTo, token):
    try:
        # Get configs
        with open("config/config.yaml", "r") as file:
            configuration = yaml.safe_load(file)

        emailFrom = configuration["email"]["sender"]
        password = configuration["email"]["password"]
        subject = configuration["email"]["subject"]
        message = configuration["email"]["message"]
        server = configuration["email"]["server"]
        port = configuration["email"]["port"]

        # Message build
        msg = MIMEMultipart()
        msg["From"] = emailFrom
        msg["To"] = emailTo
        msg["Subject"] = subject

        # Add body message
        msg.attach(MIMEText(message + token, "plain"))

        # Gmail SMPT server configuration
        server = smtplib.SMTP(server, port)
        server.starttls()  # Safe connection with SMPT server.
        server.login(emailFrom, password)
        text = msg.as_string()
        server.sendmail(emailFrom, emailTo, text)  # Sending email
        server.quit()  # Close connection

        return "Correo enviado exitosamente."
    except Exception as e:
        return f"Error al enviar correo: {e}"


@app.route("/recover_password", methods=["GET", "POST"])
def recover_password():
    if request.method == "POST":
        userName = request.form["user"]
        conn = get_db_connection()
        userEmail = conn.execute(
            "SELECT email FROM users WHERE username = ?", (userName,)
        ).fetchone()[0]
        if userEmail:
            token = str(uuid.uuid4())
            conn.execute(
                "UPDATE users SET recovery_token = ? WHERE email = ?",
                (token, userEmail),
            )
            conn.commit()
            conn.close()
            send_recovery_email(userEmail, token)
            flash("Recovery email sent! Please check your inbox.")
            return redirect(url_for("login"))
        flash("Email not found!")
        conn.close()
    return render_template("recover_password.html")


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "POST":
        password = bcrypt.generate_password_hash(request.form["password"]).decode(
            "utf-8"
        )
        conn = get_db_connection()
        conn.execute(
            "UPDATE users SET password = ?, recovery_token = NULL WHERE recovery_token = ?",
            (password, token),
        )
        conn.commit()
        conn.close()
        flash("Password updated successfully!")
        return redirect(url_for("login"))
    return render_template("reset_password.html", token=token)


# Main
if __name__ == "__main__":
    init_db()
    text = "admin"
    print(encodeTextInBase64(text))
    print(decodeTextFromBase64(encodeTextInBase64(text)))
    app.run(debug=True)
