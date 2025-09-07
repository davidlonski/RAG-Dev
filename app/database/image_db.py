import os
from datetime import datetime
from dotenv import load_dotenv
import mysql.connector


class ImageServer:
    """
    Singleton class for managing image database connections.
    Ensures only one database connection is created and reused.
    """
    _instance = None
    _mydb = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ImageServer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._mydb = self._configure_image_server()
            self._initialized = True

    def _configure_image_server(self):
        """Configure and return database connection using homework database."""
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
            print("✅ Image Server connected to homework database successfully")
            return mydb
        except Exception as e:
            print(f"❌ Error connecting to homework database: {e}")
            return None

    @property
    def mydb(self):
        """Get the database connection."""
        return self._mydb

    def get_connection(self):
        """Get database connection with reconnection logic."""
        try:
            # Test if connection is still alive
            if self._mydb and self._mydb.is_connected():
                return self._mydb
            else:
                # Reconnect if connection is lost
                print("🔄 Reconnecting to database...")
                self._mydb = self._configure_image_server()
                return self._mydb
        except Exception as e:
            print(f"❌ Error getting database connection: {e}")
            return None

    def upload_image(self, image_bytes, image_extension=None, content_type=None):
        """
        Uploads an image to the database and returns the image id
        image_bytes: bytes
        image_extension: str (optional) - file extension like 'png', 'jpg'
        content_type: str (optional) - MIME type like 'image/png'
        returns: image_id
        """
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
                return None
                
            file_size = len(image_bytes)
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            mycursor = mydb.cursor()
            sql = "INSERT INTO images (image_data, image_extension, created_at, file_size, content_type) VALUES (%s, %s, %s, %s, %s)"
            val = (image_bytes, image_extension, created_at, file_size, content_type)
            mycursor.execute(sql, val)
            mydb.commit()
            image_id = mycursor.lastrowid
            mycursor.close()
            return image_id
        except Exception as e:
            print(f"❌ Unexpected error during image upload: {e}")
            return None
            
    def get_image(self, image_id):
        """
        Gets an image from the database and returns the image data and metadata
        image_id: int
        returns: dict with image_data, image_extension, file_size, content_type, created_at
        """
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
                return None
                
            mycursor = mydb.cursor(dictionary=True)
            sql = "SELECT image_data, image_extension, file_size, content_type, created_at FROM images WHERE id = %s"
            val = (image_id,)
            mycursor.execute(sql, val)
            result = mycursor.fetchone()
            mycursor.close()
            return result
        except Exception as e:
            print(f"❌ Unexpected error during image get: {e}")
            return None
            
    def get_image_as_base64(self, image_id):
        """
        Gets an image from the database and returns it as base64 encoded string
        image_id: int
        returns: base64 encoded string or None if error
        """
        try:
            import base64
            result = self.get_image(image_id)
            if result and result.get('image_data'):
                return base64.b64encode(result['image_data']).decode('utf-8')
            return None
        except Exception as e:
            print(f"❌ Unexpected error during image base64 conversion: {e}")
            return None

    def delete_image(self, image_id):
        """
        Deletes an image from the database
        image_id: int
        returns: True if successful, None if error
        """
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
                return None
                
            mycursor = mydb.cursor()
            sql = "DELETE FROM images WHERE id = %s"
            val = (image_id,)
            mycursor.execute(sql, val)
            mydb.commit()
            mycursor.close()
            return True
        except Exception as e:
            print(f"❌ Unexpected error during image delete: {e}")
            return None

    def close_connection(self):
        """Close the database connection."""
        try:
            if self._mydb and self._mydb.is_connected():
                self._mydb.close()
                print("✅ Database connection closed")
        except Exception as e:
            print(f"❌ Error closing database connection: {e}")

    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close_connection()
