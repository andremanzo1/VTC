from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS programs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  program_name TEXT,
                  daily_rate REAL,
                  billed_residents INTEGER,
                  average_occupancy REAL,
                  total_daily_income REAL,
                  month TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS static_income
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  income_source TEXT,
                  amount REAL,
                  month TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS static_overhead
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  overhead_name TEXT,
                  amount REAL,
                  month TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))  # Default to current month
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    # Fetch programs for the selected month
    c.execute("SELECT * FROM programs WHERE month=?", (month,))
    programs = c.fetchall()

    # Fetch static income for the selected month
    c.execute("SELECT * FROM static_income WHERE month=?", (month,))
    static_income = c.fetchall()

    # Fetch static overhead for the selected month
    c.execute("SELECT * FROM static_overhead WHERE month=?", (month,))
    static_overhead = c.fetchall()

    conn.close()

    return render_template('index.html', programs=programs, static_income=static_income, static_overhead=static_overhead, selected_month=month)

@app.route('/add_program', methods=['POST'])
def add_program():
    program_name = request.form['program_name']
    daily_rate = float(request.form['daily_rate'])
    billed_residents = int(request.form['billed_residents'])
    average_occupancy = float(request.form['average_occupancy'])
    month = request.form['month']

    total_daily_income = daily_rate * billed_residents + average_occupancy

    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO programs (program_name, daily_rate, billed_residents, average_occupancy, total_daily_income, month) VALUES (?, ?, ?, ?, ?, ?)",
              (program_name, daily_rate, billed_residents, average_occupancy, total_daily_income, month))
    conn.commit()
    conn.close()

    return redirect(url_for('index', month=month))

@app.route('/add_static_income', methods=['POST'])
def add_static_income():
    income_source = request.form['income_source']
    amount = float(request.form['amount'])
    month = request.form['month']

    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO static_income (income_source, amount, month) VALUES (?, ?, ?)",
              (income_source, amount, month))
    conn.commit()
    conn.close()

    return redirect(url_for('index', month=month))

@app.route('/add_static_overhead', methods=['POST'])
def add_static_overhead():
    overhead_name = request.form['overhead_name']
    amount = float(request.form['amount'])
    month = request.form['month']

    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()
    c.execute("INSERT INTO static_overhead (overhead_name, amount, month) VALUES (?, ?, ?)",
              (overhead_name, amount, month))
    conn.commit()
    conn.close()

    return redirect(url_for('index', month=month))

if __name__ == '__main__':
    app.run(debug=True)