import os
import sys

# Add the project root directory to the Python path
# This allows us to use absolute imports starting from 'src'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ui.app import app

if __name__ == '__main__':
    DSN = os.getenv("TEST_POSTGRES_DSN")
    if not DSN:
        print("Warning: TEST_POSTGRES_DSN environment variable is not set. UI will run without a database connection.")
    
    # Use host='0.0.0.0' to make the server accessible from the network
    app.run(host='0.0.0.0', port=5001, debug=True)
