#!/usr/bin/env python3
"""
Reset database data while maintaining structure.
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def reset_database_data():
    """Reset all data in the database while maintaining structure."""
    print("🔄 Resetting database data...")
    
    load_dotenv()
    HOST = os.getenv("HOMEWORK_DB_HOST")
    USER = os.getenv("HOMEWORK_DB_USER")
    PASSWORD = os.getenv("HOMEWORK_DB_PASS")
    DATABASE = os.getenv("HOMEWORK_DB_NAME")
    
    try:
        mydb = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = mydb.cursor()
        
        # Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"📊 Found {len(tables)} tables to reset")
        
        # Reset each table
        for table in tables:
            try:
                cursor.execute(f"TRUNCATE TABLE {table}")
                print(f"   ✅ Reset table: {table}")
            except Exception as e:
                print(f"   ❌ Error resetting {table}: {e}")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # Commit changes
        mydb.commit()
        cursor.close()
        mydb.close()
        
        print("✅ Database reset completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        return False

def verify_reset():
    """Verify that all tables are empty but structure remains."""
    print("\n🔍 Verifying reset...")
    
    load_dotenv()
    HOST = os.getenv("HOMEWORK_DB_HOST")
    USER = os.getenv("HOMEWORK_DB_USER")
    PASSWORD = os.getenv("HOMEWORK_DB_PASS")
    DATABASE = os.getenv("HOMEWORK_DB_NAME")
    
    try:
        mydb = mysql.connector.connect(
            host=HOST,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = mydb.cursor(dictionary=True)
        
        # Get all tables and their row counts
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        print("📊 Table verification:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"   - {table}: {count} rows")
        
        cursor.close()
        mydb.close()
        
        print("✅ Verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying reset: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Reset Tool")
    print("=" * 40)
    
    # Confirm with user
    response = input("⚠️  This will DELETE ALL DATA from the database. Are you sure? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Reset cancelled.")
        exit()
    
    # Reset database
    if reset_database_data():
        # Verify reset
        verify_reset()
    
    print("\n🏁 Reset process completed!")
