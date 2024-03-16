import os
import sqlite3
from flask import Flask, render_template, request, jsonify
import openai
from datetime import datetime
import base64
from io import BytesIO

app = Flask(__name__)
openai.api_key = "OPENAI-API-KEY"

# Create a SQLite database connection
conn = sqlite3.connect('life_log.db', check_same_thread=False)
c = conn.cursor()

# Create a table to store life log entries
c.execute('''CREATE TABLE IF NOT EXISTS life_log
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             date TEXT,
             entry TEXT)''')
conn.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/log_entry', methods=['POST'])
def log_entry():
    entry = request.form['entry']
    date = datetime.now().strftime('%Y-%m-%d')  # Get the current date
    c.execute("INSERT INTO life_log (date, entry) VALUES (?, ?)", (date, entry))
    conn.commit()
    return jsonify(success=True)

@app.route('/get_summary', methods=['POST'])
def get_summary():
    period = request.form['period']
    if period == 'day':
        c.execute("SELECT entry FROM life_log WHERE date = date('now')")
    elif period == 'month':
        c.execute("SELECT entry FROM life_log WHERE date BETWEEN date('now', 'start of month') AND date('now')")
    elif period == 'year':
        c.execute("SELECT entry FROM life_log WHERE date BETWEEN date('now', 'start of year') AND date('now')")
    
    entries = c.fetchall()
    entries_text = "\n".join([entry[0] for entry in entries])
    
    prompt = f"Given the following life log entries:\n\n{entries_text}\n\nPlease provide a summary including what went well, what could have been better, and advice for tomorrow."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes life log entries."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
    )
    summary = response.choices[0].message['content'].strip()

    # Generate an image using DALL-E based on the summary
    image_prompt = f"An artistic representation of the following summary: {summary}"
    image_response = openai.Image.create(
        prompt=image_prompt[:990],
        n=1,
        size="512x512",
        response_format="b64_json"
    )
    image_data = image_response['data'][0]['b64_json']

    return jsonify(summary=summary, image_data=image_data)

@app.route('/get_all_entries', methods=['GET'])
def get_all_entries():
    c.execute("SELECT date, entry FROM life_log ORDER BY date DESC")
    entries = c.fetchall()
    return jsonify(entries=entries)

if __name__ == '__main__':
    app.run(debug=True)
