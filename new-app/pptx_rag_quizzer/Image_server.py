import os
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
        """Configure and return database connection."""
        load_dotenv()
        IMAGE_DB_HOST = os.getenv("IMAGE_DB_HOST")
        IMAGE_DB_USER = os.getenv("IMAGE_DB_USER")
        IMAGE_DB_PASSWORD = os.getenv("IMAGE_DB_PASS")
        IMAGE_DB_NAME = os.getenv("IMAGE_DB_NAME")
        
        try:
            mydb = mysql.connector.connect(
                host=IMAGE_DB_HOST,
                user=IMAGE_DB_USER,
                password=IMAGE_DB_PASSWORD,
                database=IMAGE_DB_NAME
            )
            print("✅ Database connection established successfully")
            return mydb
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
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

    def upload_image(self, image_bytes):
        """
        Uploads an image to the database and returns the image id
        image_bytes: bytes
        returns: image_id
        """
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
                return None
                
            mycursor = mydb.cursor()
            sql = "INSERT INTO images (image_data) VALUES (%s)"
            val = (image_bytes,)
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
        Gets an image from the database and returns the image data
        image_id: int
        returns: image_data
        """
        try:
            mydb = self.get_connection()
            if not mydb:
                print("❌ No database connection available")
                return None
                
            mycursor = mydb.cursor()
            sql = "SELECT image_data FROM images WHERE id = %s"
            val = (image_id,)
            mycursor.execute(sql, val)
            image_data = mycursor.fetchone()
            mycursor.close()
            return image_data
        except Exception as e:
            print(f"❌ Unexpected error during image get: {e}")
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
