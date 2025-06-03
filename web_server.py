from flask import Flask, jsonify, request
import threading
import time
import requests
from config import PORT, WEBHOOK_URL, logger, IS_PRODUCTION

# Track server status
server_start_time = time.time()
server_healthy = True
ping_interval = 5 * 60  # 5 minutes

def create_server():
    """Create and configure the Flask web server"""
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return "Daddy Telegram Bot is running!"
    
    @app.route('/health')
    def health():
        uptime = time.time() - server_start_time
        return jsonify({
            "status": "healthy" if server_healthy else "degraded",
            "bot": "running",
            "uptime_seconds": int(uptime),
            "uptime_formatted": f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
        })
    
    @app.route('/ping')
    def ping():
        """Simple endpoint for external monitoring services to ping"""
        return jsonify({"status": "pong", "timestamp": time.time()})
    
    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({"error": "Not found", "status": 404}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        global server_healthy
        server_healthy = False
        logger.error(f"Server error: {e}")
        return jsonify({"error": "Internal server error", "status": 500}), 500
    
    return app

def keep_server_alive():
    """Periodically ping the server to keep it alive"""
    if not IS_PRODUCTION:
        logger.info("Server keep-alive not needed in development mode")
        return
        
    while True:
        try:
            time.sleep(ping_interval)
            # Self-ping to keep the server alive
            response = requests.get(f"http://localhost:{PORT}/ping", timeout=10)
            if response.status_code == 200:
                logger.debug("Server keep-alive ping successful")
            else:
                logger.warning(f"Server keep-alive ping returned status code {response.status_code}")
        except Exception as e:
            logger.error(f"Error in server keep-alive ping: {e}")

def start_server(app):
    """Start the Flask server in a separate thread"""
    def run_flask():
        try:
            # Use threaded=True for better handling of concurrent requests
            app.run(host='0.0.0.0', port=PORT, threaded=True)
        except Exception as e:
            global server_healthy
            server_healthy = False
            logger.error(f"Flask server error: {e}")
    
    # Start the Flask server in a daemon thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info(f"Flask server started on port {PORT}")
    
    # Start the keep-alive thread
    keep_alive_thread = threading.Thread(target=keep_server_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    logger.info("Server keep-alive thread started")
    
    return flask_thread
