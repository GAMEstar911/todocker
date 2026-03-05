import sys
import os
from dotenv import load_dotenv

# Set the project directory (replace ELVISK with your username)
project_home = '/home/GAMEstar911/todocker'

# Add the project directory to the Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load the .env file from the project directory
dotenv_path = os.path.join(project_home, '.env')
load_dotenv(dotenv_path)

# Import the Flask app instance
from app import app as application