#!/usr/bin/env python3
"""
Migration script to add RAG quizzer tables to the database.
Run this script to create the new tables for persisting RAG quizzer data.
"""

import os
import mysql.connector
from dotenv import load_dotenv

def run_migration():
    """Run the migration to add RAG quizzer tables."""
    load_dotenv()
    
    host = os.getenv("HOMEWORK_DB_HOST")
    user = os.getenv("HOMEWORK_DB_USER")
    password = os.getenv("HOMEWORK_DB_PASS")
    database = os.getenv("HOMEWORK_DB_NAME")
    
    try:
        # Connect to database
        mydb = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
        )
        
        cursor = mydb.cursor()
        
        # Create rag_quizzers table
        print("Creating rag_quizzers table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_quizzers (
              id INT PRIMARY KEY AUTO_INCREMENT,
              teacher_id INT NOT NULL,
              name VARCHAR(255) NOT NULL,
              collection_id VARCHAR(255) NOT NULL,
              presentation_name VARCHAR(255) NOT NULL,
              num_slides INT NOT NULL,
              num_text_items INT NOT NULL DEFAULT 0,
              num_image_items INT NOT NULL DEFAULT 0,
              created_at DATETIME NOT NULL,
              status ENUM('active','archived') NOT NULL DEFAULT 'active',
              FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        """)
        
        # Create rag_quizzer_slides table
        print("Creating rag_quizzer_slides table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_quizzer_slides (
              id INT PRIMARY KEY AUTO_INCREMENT,
              rag_quizzer_id INT NOT NULL,
              slide_number INT NOT NULL,
              slide_content LONGTEXT NULL,
              created_at DATETIME NOT NULL,
              FOREIGN KEY (rag_quizzer_id) REFERENCES rag_quizzers(id) ON DELETE CASCADE ON UPDATE CASCADE
            )
        """)
        
        mydb.commit()
        print("✅ Migration completed successfully!")
        
        # Show table structure
        cursor.execute("SHOW TABLES LIKE 'rag_quizzers'")
        if cursor.fetchone():
            print("✅ rag_quizzers table exists")
        
        cursor.execute("SHOW TABLES LIKE 'rag_quizzer_slides'")
        if cursor.fetchone():
            print("✅ rag_quizzer_slides table exists")
        
        cursor.close()
        mydb.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting RAG Quizzer migration...")
    success = run_migration()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
