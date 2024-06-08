from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import smtplib
import uuid
import yaml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['DEBUG'] = True

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT, role TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, title TEXT, content TEXT)')
    conn.execute('INSERT OR IGNORE INTO users (id,username,email,password,role) VALUES (?,?,?,?,?)',
                 (1,'admin','admin@admin.com','admin','admin')
                 );
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'role' not in session or session['role'] != 'admin':
        role = 'guest';
    else :
        role = 'admin';
        
    return render_template('index.html',role=role)

@app.route('/posts')
def posts():
    role = request.args.get('role', 'guest')
    
    # If the role parameter is not 'guest' or 'admin', redirect to the same route with 'role=guest'
    if role not in ['guest', 'admin']:
        return redirect(url_for('posts', role='guest'))
    
    filter_text = request.args.get('filter', '')
    conn = get_db_connection()
    
    try:
        if filter_text:
            # Esta es una forma insegura de ejecutar la consulta, solo para propósitos educativos o de prueba
            posts = conn.execute('SELECT * FROM posts WHERE content LIKE \'%' + filter_text + '%\'').fetchall()
        else:
            posts = conn.execute('SELECT * FROM posts').fetchall()
        
        conn.close()
        return render_template('posts.html', posts=posts, error=None)
    
    except Exception as e:
        error_message = str(e)
        return render_template('posts.html', posts=[], error=error_message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    role = request.args.get('role')
    
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn = get_db_connection()
        conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    return render_template('admin.html')

@app.route('/post/<int:post_id>')
def post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return render_template('post.html', post=post)

# Password recovery
def send_recovery_email(emailTo, token):
    try:
        # Get configs
        with open('config/config.yaml', 'r') as file:
            configuration = yaml.safe_load(file)

        emailFrom = configuration['email']['sender']
        password = configuration['email']['password']
        subject = configuration['email']['subject']
        message = configuration['email']['message']
        server = configuration['email']['server']
        port = configuration['email']['port']

        # Message build
        msg = MIMEMultipart()
        msg['From'] = emailFrom
        msg['To'] = emailTo
        msg['Subject'] = subject

        # Add body message
        msg.attach(MIMEText(message + token , 'plain'))

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

@app.route('/recover_password', methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        userName = request.form['user']
        conn = get_db_connection()
        userEmail = conn.execute('SELECT email FROM users WHERE username = ?', (userName,)).fetchone()[0]
        if userEmail:
            token = str(uuid.uuid4())
            conn.execute('UPDATE users SET recovery_token = ? WHERE email = ?', (token, userEmail))
            conn.commit()
            conn.close()
            send_recovery_email(userEmail, token)
            flash('Recovery email sent! Please check your inbox.')
            return redirect(url_for('login'))
        flash('Email not found!')
        conn.close()
    return render_template('recover_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form['password']
        conn = get_db_connection()
        conn.execute('UPDATE users SET password = ?, recovery_token = NULL WHERE recovery_token = ?', (password, token))
        conn.commit()
        conn.close()
        flash('Password updated successfully!')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

# Main
if __name__ == '__main__':
    init_db()
    app.run(debug=True)