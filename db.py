import psycopg2
from psycopg2 import OperationalError
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseManager:
    """Handles all PostgreSQL database interactions."""
    
    def __init__(self):
        """Initialize database manager with credentials from .env"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.database = os.getenv('DB_NAME', 'quiz_app_db')
        self.user = os.getenv('DB_USER', 'quiz_user')
        self.password = os.getenv('DB_PASSWORD', 'quiz_password')
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish connection to PostgreSQL database.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to PostgreSQL database: {self.database}")
            return True
        
        except OperationalError as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection safely."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("🔌 Database connection closed")
    
    def test_connection(self):
        """Test the connection by running a simple query.
        
        Returns:
            str: PostgreSQL version if successful, None otherwise
        """
        if not self.conn:
            return None
        
        try:
            self.cursor.execute("SELECT version();")
            version = self.cursor.fetchone()[0]
            return version
        except Exception as e:
            print(f"❌ Test query failed: {e}")
            return None
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password.
        
        Args:
            username (str): Username to check
            password (str): Password to verify
        
        Returns:
            tuple: (user_id, username) if successful, None otherwise
        
        WARNING: This uses plain-text password comparison!
                 In production, use hashed passwords (bcrypt, argon2, etc.)
        """
        if not self.conn:
            print("❌ No database connection")
            return None
        
        try:
            self.cursor.execute(
                """
                SELECT id, username 
                FROM users 
                WHERE username = %s AND password_hash = %s
                """,
                (username, password)
            )
            user = self.cursor.fetchone()
            
            if user:
                print(f"✅ User authenticated: {user[1]}")
                return user  # Returns (id, username)
            else:
                print("❌ Invalid credentials")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None

# Global instance (Singleton pattern)
db = DatabaseManager()
