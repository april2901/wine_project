from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = 'dohoongyuri'

FAMILY_USERS = {
    'dad': '1111',
    'mom': '2222', 
    'son': '3333',
    'daughter': '4444'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('이 기능을 사용하려면 로그인이 필요합니다.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    conn = sqlite3.connect('wine.db')
    conn.row_factory = sqlite3.Row
    return conn

# 로그인 페이지
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in FAMILY_USERS and FAMILY_USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            flash('로그인 성공! 이제 와인을 추가하고 편집할 수 있습니다.', 'success')
            return redirect(url_for('index'))
        else:
            flash('잘못된 사용자 이름 또는 비밀번호입니다.', 'error')
    
    return render_template('login.html')

# 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다. 와인 목록은 계속 볼 수 있습니다.', 'info')
    return redirect(url_for('index'))

conn = get_db()
conn.execute('''
CREATE TABLE IF NOT EXISTS wine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT,
    region TEXT,
    grape_variety TEXT,
    year INTEGER,
    price INTEGER,
    note TEXT,
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()

# 홈: 와인 목록 보기
@app.route('/')
def index():
    conn = get_db()
    wines = conn.execute('SELECT * FROM wine').fetchall()
    conn.close()
    return render_template('index.html', wines=wines)

# 와인 추가
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        country = request.form['country']
        region = request.form.get('region', '')  # 빈 문자열이 기본값
        grape_variety = request.form.get('grape_variety', '')
        year = request.form.get('year', '')
        price = request.form.get('price', '')
        if price:
            price = int(float(price))
        note = request.form.get('note', '')
        
        conn = get_db()
        conn.execute('''
            INSERT INTO wine (name, country, region, grape_variety, year, price, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, country, region, grape_variety, year, price, note))
        conn.commit()
        conn.close()
        return redirect('/')
    return render_template('add.html')

# Edit wine
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    conn = get_db()
    if request.method == 'POST':
        name = request.form['name']
        country = request.form.get('country', '')
        region = request.form.get('region', '')
        grape_variety = request.form.get('grape_variety', '')
        year = request.form.get('year', '')
        price = request.form.get('price', '')
        note = request.form.get('note', '')
        
        conn.execute('''
            UPDATE wine 
            SET name = ?, country = ?, region = ?, grape_variety = ?, 
                year = ?, price = ?, note = ? 
            WHERE id = ?
        ''', (name, country, region, grape_variety, year, price, note, id))
        conn.commit()
        conn.close()
        return redirect('/')
    
    # Get the wine to edit
    wine = conn.execute('SELECT * FROM wine WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', wine=wine)

# Search wines
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    conn = get_db()
    wines = conn.execute(
        'SELECT * FROM wine WHERE name LIKE ? OR country LIKE ?', 
        ('%' + query + '%', '%' + query + '%')
    ).fetchall()
    conn.close()
    return render_template('index.html', wines=wines, query=query)

# Delete wine
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    conn = get_db()
    conn.execute('DELETE FROM wine WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    conn = get_db()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS wine (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT,
        region TEXT,
        grape_variety TEXT,
        year INTEGER,
        price INTEGER,
        note TEXT,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conn.commit()
    conn.close()
    app.run(debug=True)
