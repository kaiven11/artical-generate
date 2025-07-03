#!/usr/bin/env python3
"""
Startup script for the Article Migration Tool.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import run_app
from app.core.config import get_settings
from app.core.database import init_db

def main():
    """Main entry point."""
    print("🚀 Starting Article Migration Tool...")

    # Get settings
    settings = get_settings()

    # Ensure directories exist
    from app.core.config import ensure_directories
    ensure_directories()

    # Initialize database
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    # Start the server
    print(f"🌐 Starting server at http://{settings.host}:{settings.port}")
    print("📊 Dashboard will be available at the root URL")
    print("🔧 API endpoints available at /api/v1/")
    print("⚡ Press Ctrl+C to stop the server")

    try:
        run_app()
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
