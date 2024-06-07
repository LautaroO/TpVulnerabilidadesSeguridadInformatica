import os
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

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
    
    if filter_text:
        # Esta es una forma insegura de ejecutar la consulta, solo para propósitos educativos o de prueba
        posts = conn.execute('SELECT * FROM posts WHERE content LIKE \'%' + filter_text + '%\'').fetchall()
    else:
        posts = conn.execute('SELECT * FROM posts').fetchall()
    
    conn.close()

    return render_template('posts.html', posts=posts)

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

if __name__ == '__main__':
    init_db()
    app.run(debug=True)