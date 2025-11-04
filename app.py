from flask import Flask, render_template, request, jsonify, redirect, url_for, g
import os
import sqlite3
import uuid
import pikepdf
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

DATABASE = 'print_shop_db.sqlite3'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db_connection():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/init-db')
def init_db():
    try:
        conn = get_db_connection()
        with open('schema.sql') as f:
            conn.executescript(f.read())
        conn.commit()
        return "Database initialized successfully!", 200
    except Exception as e:
        return f"Error initializing database: {e}", 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number')
        if not mobile_number or len(mobile_number) != 10:
            return "Invalid mobile number", 400
        return render_template('upload.html', mobile_number=mobile_number)
    return redirect(url_for('index'))

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

        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

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

@app.route('/submit-job', methods=['POST'])
def submit_job():
    try:
        data = request.get_json()
        mobile_number = data.get('mobile_number')
        jobs = data.get('jobs', [])
        if not mobile_number or not jobs:
            return jsonify({'success': False, 'error': 'Invalid data'}), 400

        connection = get_db_connection()
        cursor = connection.cursor()

        total_cost = sum(float(job['file_cost']) for job in jobs)

        cursor.execute(
            "INSERT INTO PrintBatches (mobile_number, status, total_cost, created_at) VALUES (?, ?, ?, ?)",
            (mobile_number, 'Waiting', total_cost, datetime.now())
        )
        batch_id = cursor.lastrowid

        for job in jobs:
            cursor.execute(
                "INSERT INTO PrintFiles (batch_id, file_name_original, file_path_saved, page_count_original, page_range, page_count_final, copies, print_color, print_duplex, file_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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

        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'total_cost': total_cost
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''SELECT b.batch_id, b.mobile_number, b.status, b.total_cost, b.created_at, 
                          GROUP_CONCAT(f.file_name_original, ', ') as files
                          FROM PrintBatches b 
                          LEFT JOIN PrintFiles f ON b.batch_id = f.batch_id
                          WHERE b.status IN ('Waiting', 'Printing')
                          GROUP BY b.batch_id
                          ORDER BY b.created_at ASC
                          ''')
        jobs = cursor.fetchall()
        cursor.close()

        # Convert created_at string to formatted date string, handle fractional seconds
        jobs_list = []
        for job in jobs:
            job_dict = dict(job)
            created_at_str = job_dict['created_at'].split('.')[0]  # strip microseconds if any
            job_dict['created_at'] = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M')
            jobs_list.append(job_dict)

        return render_template('dashboard.html', jobs=jobs_list)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/update-job-status/<int:batch_id>/<status>', methods=['POST'])
def update_job_status(batch_id, status):
    if status not in ['Waiting', 'Printing', 'Completed', 'Cancelled']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE PrintBatches SET status=? WHERE batch_id=?", (status, batch_id))
        connection.commit()
        cursor.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-pricing')
def get_pricing():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT setting_key, setting_value FROM Settings")
        settings = cursor.fetchall()
        cursor.close()
        pricing = {setting['setting_key']: float(setting['setting_value']) for setting in settings}
        return jsonify({'success': True, 'pricing': pricing}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
