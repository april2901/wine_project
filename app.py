from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def init_db():
    conn = sqlite3.connect('wine_cellar.db')
    cursor = conn.cursor()
    
    # 먼저 wines 테이블이 존재하는지 확인
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='wines'
    """)
    
    table_exists = cursor.fetchone()
    
    if not table_exists:
        # 테이블이 없으면 새로 생성 (위치 정보 포함)
        cursor.execute('''
            CREATE TABLE wines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT,
                region TEXT,
                year INTEGER,
                grape_variety TEXT,
                price INTEGER,
                notes TEXT,
                date_added TEXT,
                shelf_number INTEGER,
                position_in_shelf INTEGER,
                wine_type INTEGER
            )
        ''')
        print("wines 테이블이 생성되었습니다.")
    else:
        # 테이블이 있으면 컬럼 확인 및 추가
        cursor.execute("PRAGMA table_info(wines)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # shelf_number 컬럼이 없으면 추가
        if 'shelf_number' not in columns:
            cursor.execute('ALTER TABLE wines ADD COLUMN shelf_number INTEGER')
            print("shelf_number 컬럼이 추가되었습니다.")
        
        # position_in_shelf 컬럼이 없으면 추가
        if 'position_in_shelf' not in columns:
            cursor.execute('ALTER TABLE wines ADD COLUMN position_in_shelf INTEGER')
            print("position_in_shelf 컬럼이 추가되었습니다.")
        
        if 'position_in_shelf' not in columns:
            cursor.execute('ALTER TABLE wines ADD COLUMN wine_type INTEGER')
            print("wine_type 컬럼이 추가되었습니다.")
    
    conn.commit()
    conn.close()


init_db()

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    
    conn = sqlite3.connect('wine_cellar.db')
    cursor = conn.cursor()
    
    if search_query:
        cursor.execute('''
            SELECT id, name, country, region, year, grape_variety, price, notes, date_added, shelf_number, position_in_shelf, wine_type
            FROM wines 
            WHERE name LIKE ? OR country LIKE ? OR region LIKE ? OR grape_variety LIKE ?
            ORDER BY date_added DESC
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
    else:
        cursor.execute('''
            SELECT id, name, country, region, year, grape_variety, price, notes, date_added, shelf_number, position_in_shelf, wine_type
            FROM wines 
            ORDER BY date_added DESC
        ''')
    
    wines = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', wines=wines, search_query=search_query)

@app.route('/cellar')
def cellar_view():
    
    # 셀러 전체 현황 가져오기
    cellar_data = get_cellar_overview()
    return render_template('cellar.html', cellar_data=cellar_data)

@app.route('/cellar/shelf/<int:shelf_number>')
def shelf_detail(shelf_number):
    
    # 특정 선반의 와인들 가져오기
    wines = get_wines_by_shelf(shelf_number)
    cellar_data = get_cellar_overview()
    
    return render_template('cellar.html', 
                         cellar_data=cellar_data, 
                         selected_shelf=shelf_number,
                         shelf_wines=wines)

@app.route('/api/cellar/overview')
def api_cellar_overview():
    """AJAX용 셀러 현황 API"""
    return jsonify(get_cellar_overview())

@app.route('/api/shelf/<int:shelf_number>/wines')
def api_shelf_wines(shelf_number):
    """AJAX용 특정 선반 와인 목록 API"""
    wines = get_wines_by_shelf(shelf_number)
    wine_list = []
    
    for wine in wines:
        wine_dict = {
            'id': wine[0],
            'name': wine[1],
            'country': wine[2],
            'region': wine[3],
            'year': wine[4],
            'grape_variety': wine[5],
            'price': wine[6],
            'notes': wine[7],
            'position': None,
            'type': wine[11]
        }
        
        # 위치 정보가 있는 경우 추가 (컬럼 개수 확인)
        if len(wine) > 9:
            wine_dict['position'] = wine[10]
        
        wine_list.append(wine_dict)
    
    return jsonify(wine_list)

def get_cellar_overview():
    """셀러 전체 현황 반환"""
    conn = sqlite3.connect('wine_cellar.db')
    cursor = conn.cursor()
    
    # 각 선반별 와인 개수 조회
    cursor.execute('''
        SELECT shelf_number, COUNT(*) as wine_count
        FROM wines 
        WHERE shelf_number IS NOT NULL
        GROUP BY shelf_number
    ''')
    
    shelf_counts = dict(cursor.fetchall())
    conn.close()
    
    # 10개 선반 데이터 구성 (빈 선반도 포함)
    cellar_data = []
    for shelf in range(1, 11):
        cellar_data.append({
            'shelf_number': shelf,
            'wine_count': shelf_counts.get(shelf, 0),
            'max_capacity': 8,
            'is_full': shelf_counts.get(shelf, 0) >= 8
        })
    
    return cellar_data

def get_wines_by_shelf(shelf_number):
    """특정 선반의 와인들 반환"""
    conn = sqlite3.connect('wine_cellar.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM wines 
        WHERE shelf_number = ? 
        ORDER BY position_in_shelf
    ''', (shelf_number,))
    
    wines = cursor.fetchall()
    conn.close()
    return wines

@app.route('/add', methods=['GET', 'POST'])
def add_wine():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        country = request.form['country']
        region = request.form['region']
        year = request.form['year']
        grape_variety = request.form['grape_variety']
        price = request.form['price']
        notes = request.form['notes']
        shelf_number = request.form.get('shelf_number') or None
        position_in_shelf = request.form.get('position_in_shelf') or None
        wine_type = request.form['type']
        
        conn = sqlite3.connect('wine_cellar.db')
        cursor = conn.cursor()
        
        # 위치가 이미 사용 중인지 확인
        if shelf_number and position_in_shelf:
            cursor.execute('''
                SELECT id FROM wines 
                WHERE shelf_number = ? AND position_in_shelf = ?
            ''', (shelf_number, position_in_shelf))
            
            if cursor.fetchone():
                flash('해당 위치에 이미 와인이 있습니다.', 'error')
                conn.close()
                return render_template('add.html')
        
        cursor.execute('''
            INSERT INTO wines (name, country, region, year, grape_variety, price, notes, date_added, shelf_number, position_in_shelf,wine_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, country, region, year, grape_variety, price, notes, datetime.now().strftime('%Y-%m-%d'), shelf_number, position_in_shelf,wine_type))
        
        conn.commit()
        conn.close()
        
        flash('와인이 성공적으로 추가되었습니다!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')

@app.route('/edit/<int:wine_id>', methods=['GET', 'POST'])
def edit_wine(wine_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('wine_cellar.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        country = request.form['country']
        region = request.form['region']
        year = request.form['year']
        grape_variety = request.form['grape_variety']
        price = request.form['price']
        notes = request.form['notes']
        shelf_number = request.form.get('shelf_number') or None
        position_in_shelf = request.form.get('position_in_shelf') or None
        wine_type = request.form['type']
        
        # 위치가 이미 사용 중인지 확인 (현재 와인 제외)
        if shelf_number and position_in_shelf:
            cursor.execute('''
                SELECT id FROM wines 
                WHERE shelf_number = ? AND position_in_shelf = ? AND id != ?
            ''', (shelf_number, position_in_shelf, wine_id))
            
            if cursor.fetchone():
                flash('해당 위치에 이미 다른 와인이 있습니다.', 'error')
                cursor.execute('SELECT * FROM wines WHERE id = ?', (wine_id,))
                wine = cursor.fetchone()
                conn.close()
                return render_template('edit.html', wine=wine)
        
        cursor.execute('''
            UPDATE wines 
            SET name=?, country=?, region=?, year=?, grape_variety=?, price=?, notes=?, shelf_number=?, position_in_shelf=?,wine_type=?
            WHERE id=?
        ''', (name, country, region, year, grape_variety, price, notes, shelf_number, position_in_shelf,wine_type, wine_id))
        
        conn.commit()
        conn.close()
        
        flash('와인 정보가 성공적으로 수정되었습니다!', 'success')
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM wines WHERE id = ?', (wine_id,))
    wine = cursor.fetchone()
    conn.close()
    
    if wine:
        return render_template('edit.html', wine=wine)
    else:
        flash('와인을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))

@app.route('/delete/<int:wine_id>', methods=['POST'])
def delete_wine(wine_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('wine_cellar.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM wines WHERE id = ?', (wine_id,))
    conn.commit()
    conn.close()
    
    flash('와인이 성공적으로 삭제되었습니다!', 'success')
    return redirect(url_for('index'))


load_dotenv()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        allowed_usernames = os.getenv('ADMIN_USERNAME', '').split(',')
        admin_password = os.getenv('ADMIN_PASSWORD', '')

        if username in allowed_usernames and password == admin_password:
            session['logged_in'] = True
            session['username'] = username
            flash('로그인 성공!', 'success')
            return redirect(url_for('index'))
        else:
            flash('잘못된 사용자명 또는 비밀번호입니다.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # 앱 시작 시 데이터베이스 초기화/업데이트
    app.run(debug=True, host='0.0.0.0', port=5000)