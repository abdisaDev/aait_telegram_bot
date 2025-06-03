from flask import Flask, jsonify
import threading
from config import PORT, logger

def create_server():
    """Create and configure the Flask web server"""
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Daddy Telegram Bot is running!"
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "bot": "running"})
    
    return app

def start_server(app):
    """Start the Flask server in a separate thread"""
    def run_flask():
        app.run(host='0.0.0.0', port=PORT)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info(f"Flask server started on port {PORT}")
    
    return flask_thread
