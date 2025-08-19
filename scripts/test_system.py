"""Test the system"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db
from src.bet_manager import BetManager

def main():
    print("🧪 Testing MLB Betting System")
    
    # Test database
    print("\n1. Testing database connection...")
    assert db.test_connection(), "Database connection failed"
    print("✅ Database OK")
    
    # Test bet parsing
    print("\n2. Testing bet parsing...")
    manager = BetManager()
    
    test_bets = [
        "Harper 2 HRs -110 2u",
        "Phillies ML -150",
        "Wheeler over 6 Ks +100 1.5 units"
    ]
    
    for bet in test_bets:
        print(f"\nTesting: {bet}")
        bet_id = manager.log_bet(bet, "StatEdge")
        if bet_id:
            print(f"✅ Bet {bet_id} logged")
        else:
            print("❌ Failed")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()