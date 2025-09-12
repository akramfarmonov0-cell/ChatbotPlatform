"""
AI Chatbot SaaS Platform - Asosiy entry point
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    import os
    debug_mode = os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)