from flask import Flask, request, jsonify, render_template_string
import sqlite3

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

@app.route('/user')
def get_user():
    username = request.args.get('username')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    
    # Vulnerabilidad de SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    print(f"Executing query: {query}")
    c.execute(query)
    
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({'id': user[0], 'username': user[1], 'email': user[3], 'role': user[4]})
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/reset_password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    
    # Vulnerabilidad de autenticación defectuosa
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    
    if user:
        # Enviaríamos el token al email del atacante
        return jsonify({'message': f'Recovery email sent to {email}'}), 200
    else:
        return jsonify({'error': 'Email not found'}), 404

@app.route('/profile')
def profile():
    username = request.args.get('username')
    conn = sqlite3.connect('example.db')
    c = conn.cursor()
    
    # Supongamos que obtenemos el perfil del usuario y lo mostramos sin sanitizar
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    
    if user:
        profile_template = f"""
            <h1>Profile of {user[1]}</h1>
            <p>Email: {user[3]}</p>
            <p>Role: {user[4]}</p>
            <p>Message: {request.args.get('message')}</p>
        """
        return render_template_string(profile_template)
    else:
        return jsonify({'error': 'User not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)