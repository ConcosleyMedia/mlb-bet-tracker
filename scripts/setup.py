"""Initial system setup"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db
from src.mlb_api import MLBAPI

def main():
    print("🚀 Running initial setup...")
    
    # Test connection
    if not db.test_connection():
        print("❌ Database connection failed!")
        return
    
    # Load MLB data
    api = MLBAPI()
    
    print("Loading teams...")
    api.update_teams_in_db()
    
    print("Loading rosters...")
    api.update_rosters_in_db()
    
    print("Loading today's games...")
    api.update_todays_games()
    
    print("✅ Setup complete!")

if __name__ == "__main__":
    main()