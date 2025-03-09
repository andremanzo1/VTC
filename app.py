from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import calendar
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages

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

    # Calculate total income
    total_income = sum(program[5] for program in programs) + sum(income[2] for income in static_income)

    # Calculate total expenses
    total_expenses = sum(overhead[2] for overhead in static_overhead)

    # Calculate profit/loss
    profit_loss = total_income - total_expenses

    # Calculate the number of days in the selected month
    year, month_num = map(int, month.split('-'))
    _, num_days_in_month = calendar.monthrange(year, month_num)  # Get the number of days in the month

    # Break-even analysis for each program
    program_break_even = []
    for program in programs:
        program_id, program_name, daily_rate, billed_residents, average_occupancy, total_daily_income, program_month = program
        if daily_rate > 0:
            break_even_beds = total_expenses / (daily_rate * num_days_in_month)  # Use the correct number of days
            program_break_even.append((program_name, break_even_beds))

    conn.close()

    return render_template('index.html', programs=programs, static_income=static_income, static_overhead=static_overhead, selected_month=month, total_income=total_income, total_expenses=total_expenses, profit_loss=profit_loss, program_break_even=program_break_even)

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

    flash('Program added successfully!', 'success')
    return redirect(url_for('index', month=month))

@app.route('/edit_program/<int:id>', methods=['GET', 'POST'])
def edit_program(id):
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    if request.method == 'POST':
        program_name = request.form['program_name']
        daily_rate = float(request.form['daily_rate'])
        billed_residents = int(request.form['billed_residents'])
        average_occupancy = float(request.form['average_occupancy'])
        month = request.form['month']

        total_daily_income = daily_rate * billed_residents + average_occupancy

        c.execute("UPDATE programs SET program_name=?, daily_rate=?, billed_residents=?, average_occupancy=?, total_daily_income=?, month=? WHERE id=?",
                  (program_name, daily_rate, billed_residents, average_occupancy, total_daily_income, month, id))
        conn.commit()
        conn.close()

        flash('Program updated successfully!', 'success')
        return redirect(url_for('index', month=month))

    # Fetch the program to edit
    c.execute("SELECT * FROM programs WHERE id=?", (id,))
    program = c.fetchone()
    conn.close()

    return render_template('edit_program.html', program=program)

@app.route('/delete_program/<int:id>')
def delete_program(id):
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    # Fetch the month before deleting to redirect correctly
    c.execute("SELECT month FROM programs WHERE id=?", (id,))
    month = c.fetchone()[0]

    c.execute("DELETE FROM programs WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash('Program deleted successfully!', 'success')
    return redirect(url_for('index', month=month))

# Static Income Routes
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

    flash('Static income added successfully!', 'success')
    return redirect(url_for('index', month=month))

@app.route('/edit_static_income/<int:id>', methods=['GET', 'POST'])
def edit_static_income(id):
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    if request.method == 'POST':
        income_source = request.form['income_source']
        amount = float(request.form['amount'])
        month = request.form['month']

        c.execute("UPDATE static_income SET income_source=?, amount=?, month=? WHERE id=?",
                  (income_source, amount, month, id))
        conn.commit()
        conn.close()

        flash('Static income updated successfully!', 'success')
        return redirect(url_for('index', month=month))

    # Fetch the static income to edit
    c.execute("SELECT * FROM static_income WHERE id=?", (id,))
    static_income = c.fetchone()
    conn.close()

    return render_template('edit_static_income.html', static_income=static_income)

@app.route('/delete_static_income/<int:id>')
def delete_static_income(id):
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    # Fetch the month before deleting to redirect correctly
    c.execute("SELECT month FROM static_income WHERE id=?", (id,))
    month = c.fetchone()[0]

    c.execute("DELETE FROM static_income WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash('Static income deleted successfully!', 'success')
    return redirect(url_for('index', month=month))

# Static Overhead Routes
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

    flash('Static overhead added successfully!', 'success')
    return redirect(url_for('index', month=month))

@app.route('/edit_static_overhead/<int:id>', methods=['GET', 'POST'])
def edit_static_overhead(id):
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    if request.method == 'POST':
        overhead_name = request.form['overhead_name']
        amount = float(request.form['amount'])
        month = request.form['month']

        c.execute("UPDATE static_overhead SET overhead_name=?, amount=?, month=? WHERE id=?",
                  (overhead_name, amount, month, id))
        conn.commit()
        conn.close()

        flash('Static overhead updated successfully!', 'success')
        return redirect(url_for('index', month=month))

    # Fetch the static overhead to edit
    c.execute("SELECT * FROM static_overhead WHERE id=?", (id,))
    static_overhead = c.fetchone()
    conn.close()

    return render_template('edit_static_overhead.html', static_overhead=static_overhead)

@app.route('/delete_static_overhead/<int:id>')
def delete_static_overhead(id):
    conn = sqlite3.connect('financial_data.db')
    c = conn.cursor()

    # Fetch the month before deleting to redirect correctly
    c.execute("SELECT month FROM static_overhead WHERE id=?", (id,))
    month = c.fetchone()[0]

    c.execute("DELETE FROM static_overhead WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash('Static overhead deleted successfully!', 'success')
    return redirect(url_for('index', month=month))

if __name__ == '__main__':
    app.run(debug=True)