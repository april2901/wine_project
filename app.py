from flask import Flask, render_template, request, redirect

import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('wine.db')
    conn.row_factory = sqlite3.Row
    return conn

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
def delete(id):
    conn = get_db()
    conn.execute('DELETE FROM wine WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
