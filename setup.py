"""
Quick Setup Script for Print Shop Management System
Run this after installing requirements to verify setup
"""

import os
import sys

def check_python_version():
    """Check if Python version is 3.7+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required. Current version:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    required = ['flask', 'mysql.connector', 'pikepdf', 'werkzeug']
    missing = []
    
    for package in required:
        try:
            if package == 'mysql.connector':
                __import__('mysql.connector')
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)
    
    if missing:
        print("\n⚠️  Missing packages. Install with:")
        print("pip install -r requirements.txt")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    dirs = ['uploads', 'static', 'templates']
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")
    return True

def check_files():
    """Check if required files exist"""
    required_files = {
        'app.py': 'Main Flask application',
        'schema.sql': 'Database schema',
        'requirements.txt': 'Dependencies list',
        'templates/index.html': 'Home page template',
        'templates/upload.html': 'Upload page template',
        'templates/dashboard.html': 'Dashboard template',
        'static/style.css': 'Stylesheet'
    }
    
    all_present = True
    for file, description in required_files.items():
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - {description}")
            all_present = False
    
    return all_present

def test_mysql_connection():
    """Test MySQL connection"""
    try:
        import mysql.connector
        print("\n🔍 Testing MySQL connection...")
        print("   Enter MySQL credentials to test:")
        
        host = input("   Host (default: localhost): ").strip() or 'localhost'
        user = input("   User (default: root): ").strip() or 'root'
        password = input("   Password: ").strip()
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password
        )
        
        if connection.is_connected():
            print("✅ MySQL connection successful!")
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            
            db_exists = any('Print_Project' in db for db in databases)
            if db_exists:
                print("✅ Print_Project database exists")
            else:
                print("⚠️  Print_Project database not found")
                print("   Run http://localhost:5000/init-db after starting the app")
            
            cursor.close()
            connection.close()
            return True
        
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        print("   Make sure MySQL is running and credentials are correct")
        return False

def main():
    print("=" * 60)
    print("Print Shop Management System - Setup Verification")
    print("=" * 60)
    
    print("\n📋 Checking Python version...")
    if not check_python_version():
        return
    
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        return
    
    print("\n📁 Checking/Creating directories...")
    create_directories()
    
    print("\n📄 Checking required files...")
    if not check_files():
        print("\n⚠️  Some files are missing. Please ensure all files are in place.")
        return
    
    print("\n" + "=" * 60)
    mysql_test = input("\nTest MySQL connection? (y/n): ").strip().lower()
    if mysql_test == 'y':
        test_mysql_connection()
    
    print("\n" + "=" * 60)
    print("✅ Setup verification complete!")
    print("\n📝 Next steps:")
    print("   1. Update MySQL credentials in app.py")
    print("   2. Run: python app.py")
    print("   3. Visit: http://localhost:5000/init-db")
    print("   4. Start using: http://localhost:5000/")
    print("=" * 60)

if __name__ == "__main__":
    main()
