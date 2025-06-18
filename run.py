import os
from src.ui.app import app

if __name__ == '__main__':
    DSN = os.getenv("TEST_POSTGRES_DSN")
    if not DSN:
        print("Warning: TEST_POSTGRES_DSN environment variable is not set. UI will run without a database connection.")
    app.run(debug=True, port=5001)
