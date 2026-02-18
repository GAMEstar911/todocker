import mysql.connector
from dotenv import load_dotenv
import os

# Load the variables from your updated .env
load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        port=os.getenv('MYSQL_PORT'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )
    if connection.is_connected():
        print("✅ SUCCESS: Kali is connected to Railway MySQL!")
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"Tables found: {tables}")
        
except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        connection.close()