# import logging

# from app import create_app


# app = create_app()

# if __name__ == "__main__":
#     logging.info("Flask app started")
#     app.run(host="0.0.0.0", port=5000)


import logging
import threading

from app import create_app

# Create a thread lock
lock = threading.Lock()

# Create the Flask app
app = create_app()

def run_app():
    with lock:  # Ensure only one thread accesses this block at a time
        logging.info("Flask app started")
        app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":
    # Use a thread to run the Flask app
    app_thread = threading.Thread(target=run_app)
    app_thread.start()

    # Optional: Wait for the thread to finish (if required)
    app_thread.join()
