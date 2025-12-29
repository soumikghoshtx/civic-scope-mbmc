import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import logging

# --- CONFIGURATION & LOGGING ---
# We use logging so you can see output in the Render Dashboard
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = "mbmc_data.db"
MBMC_URL = "https://mbmc.gov.in/mbmc/etender-mbmc"

# --- DATABASE SETUP ---
def init_db():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    department TEXT,
                    publish_date TEXT,
                    status TEXT,
                    last_checked TEXT
                )
            ''')
            conn.commit()
            logger.info("✅ Database initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Database Error: {e}")

# --- THE AUTOMATED SCRAPER ROBOT ---
def scrape_mbmc_data():
    logger.info(f"[{datetime.now()}] 🤖 Robot Waking Up: Scanning MBMC Website...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        # Verify is False to bypass common govt SSL issues
        response = requests.get(MBMC_URL, headers=headers, verify=False, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"❌ Failed to fetch page: Status {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # NOTE: This selector targets the standard table on MBMC's current site.
        table = soup.find('table') 
        
        if not table:
            logger.warning("❌ No table found on page.")
            return

        rows = table.find_all('tr')
        new_projects_count = 0
        
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Skipping header row
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                # Extract Data (Robust fallback logic)
                try:
                    p_id = cols[0].text.strip()
                    dept = cols[1].text.strip()
                    title = cols[2].text.strip()
                    dates = cols[3].text.strip()
                except IndexError:
                    continue
                
                status = "Active"
                
                cursor.execute('''
                    INSERT INTO projects (id, title, department, publish_date, status, last_checked)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status=excluded.status,
                        last_checked=excluded.last_checked
                ''', (p_id, title, dept, dates, status, datetime.now().strftime("%Y-%m-%d %H:%M")))
                
                new_projects_count += 1
            
            conn.commit()
            logger.info(f"✅ Scan Complete. Processed {new_projects_count} projects.")

    except Exception as e:
        logger.error(f"❌ Scraper Error: {e}")

# --- STARTUP LOGIC ---
# Run this immediately so the DB exists before the server starts on Render
init_db()

# --- SCHEDULER ---
# Run scraper every 6 hours automatically
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_mbmc_data, trigger="interval", hours=6)
scheduler.start()

# --- ROUTES ---

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/force-refresh')
def force_refresh():
    """Manual trigger to run the robot immediately"""
    scrape_mbmc_data()
    return "✅ Manual Scrape Complete! Go back to the homepage to see data."

@app.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY last_checked DESC")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- LOCAL EXECUTION ---
if __name__ == '__main__':
    # Only run an initial scrape if we are testing locally
    scrape_mbmc_data()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
