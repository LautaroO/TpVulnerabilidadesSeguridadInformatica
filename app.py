from flask import Flask, request, jsonify, render_template, url_for, redirect
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    c.execute('''
        INSERT INTO users (username, password, email, role)
        VALUES ('admin', 'adminpass', 'admin@example.com', 'admin')
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('example.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Login successful!', 'success')
            return redirect(url_for('profile', username=username))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('sign-in.html')

@app.route('/user')
def get_user():
    username = request.args.get('username')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        user_data = {'id': user[0], 'username': user[1], 'email': user[3], 'role': user[4]}
        return jsonify(user_data)
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/profile')
def profile():
    username = request.args.get('username')
    message = request.args.get('message', '')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()

    if user:
        user_data = {'username': user[1], 'email': user[3], 'role': user[4]}
        return render_template('user_profile.html', user=user_data, message=message)
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()

    if user:
        return jsonify({'message': f'Recovery email sent to {email}'}), 200
    else:
        return jsonify({'error': 'Email not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
