#!/usr/bin/env python3
"""Daily data refresh script for cron job"""

import sys
import os
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.mlb_api import MLBAPI

def main():
    """Update today's MLB data"""
    try:
        api = MLBAPI()
        api.update_todays_games()
        print("✅ Daily data refresh completed")
    except Exception as e:
        print(f"❌ Daily data refresh failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()