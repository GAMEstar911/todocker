import sys
import os

# Add the project directory to the Python path
path = '/home/ELVISK/todocker'  # IMPORTANT: Replace ELVISK with your PythonAnywhere username
if path not in sys.path:
    sys.path.insert(0, path)

# Set the environment variable for the Flask app
os.environ['FLASK_APP'] = 'app.py'

# Import the Flask app instance
from app import app as application