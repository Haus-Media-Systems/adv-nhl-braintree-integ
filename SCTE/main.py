#!/usr/bin/env python3
"""
SCTE-35/104 NHL Auction Platform - Main Application
Production-ready SCTE-integrated auction system
"""

import os
import sys
import signal
import threading
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, scte_listener, scte_config
import routes  # Import routes to register them
import auction_engine  # Import auction engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scte_auction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Graceful shutdown handler"""
    logger.info("Received shutdown signal, stopping SCTE listener...")
    
    if scte_listener.is_listening:
        scte_listener.stop_listening()
    
    logger.info("SCTE NHL Auction Platform stopped")
    sys.exit(0)

def ensure_directories():
    """Ensure required directories exist"""
    directories = [
        'logs',
        'config',
        'data',
        'static/uploads'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def startup_checks():
    """Perform startup checks and initialization"""
    logger.info("Performing startup checks...")
    
    # Check configuration
    if not scte_config.config:
        logger.error("Failed to load SCTE configuration")
        return False
    
    # Check UDP port availability
    udp_port = scte_config.get('listener.udp_port', 9999)
    try:
        import socket
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.bind(('0.0.0.0', udp_port))
        test_socket.close()
        logger.info(f"UDP port {udp_port} is available")
    except OSError as e:
        logger.warning(f"UDP port {udp_port} may not be available: {e}")
    
    # Auto-start SCTE listener if configured
    if scte_config.get('listener.enabled', True):
        logger.info("Auto-starting SCTE listener...")
        success = scte_listener.start_listening()
        if success:
            logger.info("SCTE listener started successfully")
        else:
            logger.warning("Failed to auto-start SCTE listener")
    
    return True

def main():
    """Main application entry point"""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure directories exist
    ensure_directories()
    
    # Perform startup checks
    if not startup_checks():
        logger.error("Startup checks failed")
        sys.exit(1)
    
    # Get Flask configuration
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    logger.info(f"Starting SCTE NHL Auction Platform on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"SCTE listener: {'Enabled' if scte_config.get('listener.enabled') else 'Disabled'}")
    
    try:
        # Start Flask application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid issues with SCTE listener
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if scte_listener.is_listening:
            scte_listener.stop_listening()

if __name__ == '__main__':
    main()