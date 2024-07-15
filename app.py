from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessary for session management

DATABASE = 'employees.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def create_tables():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            department TEXT,
            salary REAL
        );
        """)
        db.commit()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user[2], password):
            session['logged_in'] = True
            session['user_id'] = user[0]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already exists")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/add', methods=['GET', 'POST'])
def add_employee():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        department = request.form['department']
        salary = request.form['salary']

        db = get_db()
        db.execute("INSERT INTO employees (name, age, department, salary) VALUES (?, ?, ?, ?)", 
                   (name, age, department, salary))
        db.commit()

        return redirect(url_for('view_employees'))
    return render_template('add_employee.html')

@app.route('/view')
def view_employees():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    employees = db.execute("SELECT * FROM employees").fetchall()
    return render_template('view_employees.html', employees=employees)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_employee(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        department = request.form['department']
        salary = request.form['salary']

        db.execute("UPDATE employees SET name = ?, age = ?, department = ?, salary = ? WHERE id = ?", 
                   (name, age, department, salary, id))
        db.commit()

        return redirect(url_for('view_employees'))

    employee = db.execute("SELECT * FROM employees WHERE id = ?", (id,)).fetchone()
    return render_template('edit_employee.html', employee=employee)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_employee(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    db = get_db()
    db.execute("DELETE FROM employees WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for('view_employees'))

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
