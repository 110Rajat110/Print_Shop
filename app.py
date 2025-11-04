from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from mysql.connector import Error
import os
from werkzeug.utils import secure_filename
import pikepdf
import uuid
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Database configuration - CHANGE PASSWORD HERE
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rajat@1234',
    'database': 'Print_Project'
}


# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Database connection helper
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize database
@app.route('/init-db')
def init_db():
    try:
        connection = get_db_connection()
        if connection is None:
            return "Failed to connect to MySQL server", 500
        
        cursor = connection.cursor()
        
        # Read and execute schema file
        with open('schema.sql', 'r') as schema_file:
            sql_commands = schema_file.read()
            
        # Split by semicolon and execute each command
        for command in sql_commands.split(';'):
            if command.strip():
                cursor.execute(command)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return "Database initialized successfully!", 200
    except Error as e:
        return f"Error initializing database: {e}", 500

# Route 1: Home page
@app.route('/')
def index():
    return render_template('index.html')

# Route 2: Upload page
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number')
        if not mobile_number or len(mobile_number) != 10:
            return "Invalid mobile number", 400
        return render_template('upload.html', mobile_number=mobile_number)
    return redirect(url_for('index'))

# Route 3: File upload endpoint (async)
@app.route('/upload-file', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Get page count using pikepdf
        try:
            pdf = pikepdf.open(file_path)
            page_count = len(pdf.pages)
            pdf.close()
        except Exception as e:
            os.remove(file_path)
            return jsonify({'success': False, 'error': f'Invalid PDF file: {str(e)}'}), 400
        
        return jsonify({
            'success': True,
            'original_name': original_filename,
            'saved_path': unique_filename,
            'page_count': page_count
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Route 4: Submit print job
@app.route('/submit-job', methods=['POST'])
def submit_job():
    try:
        data = request.get_json()
        mobile_number = data.get('mobile_number')
        jobs = data.get('jobs', [])
        
        if not mobile_number or not jobs:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        
        # Calculate total cost
        total_cost = sum(float(job['file_cost']) for job in jobs)
        
        # Insert batch
        cursor.execute(
            "INSERT INTO PrintBatches (mobile_number, status, total_cost) VALUES (%s, %s, %s)",
            (mobile_number, 'Waiting', total_cost)
        )
        batch_id = cursor.lastrowid
        
        # Insert files
        for job in jobs:
            cursor.execute(
                """INSERT INTO PrintFiles 
                (batch_id, file_name_original, file_path_saved, page_count_original, 
                page_range, page_count_final, copies, print_color, print_duplex, file_cost)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    batch_id,
                    job['original_name'],
                    job['saved_path'],
                    job['page_count_original'],
                    job['page_range'],
                    job['page_count_final'],
                    job['copies'],
                    1 if job['print_color'] == 'Color' else 0,
                    1 if job['print_duplex'] == '2-Sided' else 0,
                    job['file_cost']
                )
            )
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'total_cost': total_cost
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Route 5: Admin dashboard
@app.route('/dashboard')
def dashboard():
    try:
        connection = get_db_connection()
        if connection is None:
            return "Database connection failed", 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Get all jobs with Waiting or Printing status
        cursor.execute("""
            SELECT 
                b.batch_id,
                b.mobile_number,
                b.status,
                b.total_cost,
                b.created_at,
                GROUP_CONCAT(f.file_name_original SEPARATOR ', ') as files
            FROM PrintBatches b
            LEFT JOIN PrintFiles f ON b.batch_id = f.batch_id
            WHERE b.status IN ('Waiting', 'Printing')
            GROUP BY b.batch_id
            ORDER BY b.created_at ASC
        """)
        
        jobs = cursor.fetchall()
        cursor.close()
        connection.close()
        
        return render_template('dashboard.html', jobs=jobs)
        
    except Exception as e:
        return f"Error: {str(e)}", 500

# Route 6: Update job status
@app.route('/update-job-status/<int:batch_id>/<status>', methods=['POST'])
def update_job_status(batch_id, status):
    try:
        if status not in ['Waiting', 'Printing', 'Completed', 'Cancelled']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE PrintBatches SET status = %s WHERE batch_id = %s",
            (status, batch_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Route 7: Get pricing settings
@app.route('/get-pricing', methods=['GET'])
def get_pricing():
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT setting_key, setting_value FROM Settings")
        settings = cursor.fetchall()
        cursor.close()
        connection.close()
        
        pricing = {}
        for setting in settings:
            pricing[setting['setting_key']] = float(setting['setting_value'])
        
        return jsonify({'success': True, 'pricing': pricing}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
