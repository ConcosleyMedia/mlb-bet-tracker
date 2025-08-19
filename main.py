"""Main application entry point"""

import sys
import logging
from datetime import datetime
from src.database import db
from src.mlb_api import MLBAPI
from src.bet_manager import BetManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLBBettingSystem:
    """Main application class"""
    
    def __init__(self):
        self.mlb_api = MLBAPI()
        self.bet_manager = BetManager()
    
    def setup(self):
        """Initial setup with auto-refresh for stale data"""
        print("\n🚀 MLB Betting System Setup")
        print("=" * 50)
        
        # Test database connection
        if not db.test_connection():
            print("❌ Database connection failed!")
            return False
        
        print("✅ Database connected")
        
        # Check table counts
        counts = db.get_table_counts()
        for table, count in counts.items():
            print(f"  {table}: {count} rows")
        
        # Load teams if needed
        if counts.get('teams', 0) == 0:
            print("\n📥 Loading MLB teams...")
            self.mlb_api.update_teams_in_db()
        
        # Check data freshness and auto-refresh if needed
        print("\n🔍 Checking data freshness...")
        freshness = self.mlb_api.is_data_fresh()
        
        print(f"  Today's games: {freshness['today_games']}")
        if freshness['old_games'] > 0:
            print(f"  Previous games: {freshness['old_games']}")
        
        if freshness['needs_refresh']:
            print("\n🔄 Data is stale - auto-refreshing...")
            if self.mlb_api.auto_refresh_if_stale():
                print("✅ Data refreshed successfully")
            else:
                print("⚠️  Auto-refresh had issues, but continuing...")
        else:
            print("✅ Data is fresh")
        
        return True
    
    def update_data(self):
        """Update MLB data with freshness check"""
        print("\n🔄 Updating MLB Data")
        print("=" * 50)
        
        # Check if data is already fresh
        freshness = self.mlb_api.is_data_fresh()
        if freshness['is_fresh'] and freshness['today_games'] > 0:
            print(f"✅ Data is already fresh - {freshness['today_games']} games for today")
            print("Performing refresh anyway...")
        
        # Update teams
        print("Updating teams...")
        self.mlb_api.update_teams_in_db()
        
        # Update rosters
        print("Updating rosters...")
        self.mlb_api.update_rosters_in_db()
        
        # Update games
        print("Updating today's games...")
        games = self.mlb_api.update_todays_games()
        
        print(f"\n✅ Updated {len(games)} games for today")
        for game in games[:5]:
            print(f"  {game['teams']['away']['team']['name']} @ "
                  f"{game['teams']['home']['team']['name']}")
    
    def enter_bet(self):
        """Interactive bet entry"""
        print("\n📝 Enter New Bet")
        print("=" * 50)
        
        raw_input = input("Enter bet (e.g., 'Harper 2 HRs -110 2u'): ")
        
        print("\nCommunities:")
        print("  1. StatEdge (Free)")
        print("  2. StatEdge+ (Paid)")
        print("  3. StatEdge Premium (VIP)")
        
        choice = input("Select community (1-3): ")
        communities = ['StatEdge', 'StatEdge+', 'StatEdge Premium']
        community = communities[int(choice) - 1] if choice.isdigit() else 'StatEdge'
        
        result = self.bet_manager.log_bet(raw_input, community)
        
        if result['success']:
            print(f"\n✅ Bet logged successfully! ID: {result['bet_id']}")
            
            # Show validation feedback
            validation = result.get('validation', {})
            for suggestion in validation.get('suggestions', []):
                print(f"   {suggestion}")
        else:
            print(f"\n❌ {result.get('error', 'Failed to log bet')}")
            
            # Show validation errors and suggestions
            validation = result.get('validation', {})
            for error in validation.get('errors', []):
                print(f"   {error}")
            for suggestion in validation.get('suggestions', []):
                print(f"   {suggestion}")
    
    def view_bets(self):
        """View today's bets with game information"""
        from datetime import date
        today = date.today()
        
        print(f"\n📊 Today's Bets (Games for {today})")
        print("=" * 50)
        
        # Auto-update old bet statuses first
        self.bet_manager.update_old_bet_status()
        
        bets = self.bet_manager.get_todays_bets()
        
        if not bets:
            print("No bets for today's games")
            return
        
        for bet in bets:
            print(f"\n#{bet['bet_id']} - {bet['community_name']}")
            print(f"  Game: {bet['away_team']} @ {bet['home_team']} ({bet['game_date']})")
            print(f"  Input: {bet['raw_input']}")
            print(f"  Type: {bet['bet_type']} | Odds: {bet['odds']} | Units: {bet['units']}")
            print(f"  Status: {bet['status']}")
    
    def clear_bets_menu(self):
        """Clear bets submenu with options"""
        print("\n🗑️  Clear Bets")
        print("=" * 50)
        
        # Get current bet counts
        counts = self.bet_manager.get_bet_counts()
        
        print(f"Current bets:")
        print(f"  • All time: {counts['all']} bets")
        print(f"  • Today: {counts['today']} bets") 
        print(f"  • Active: {counts['active']} bets")
        
        if counts['all'] == 0:
            print("\nNo bets to clear!")
            return
        
        print("\nOptions:")
        print("1. Clear ALL bets (permanent deletion)")
        print("2. Clear today's bets only")
        print("3. Cancel active bets (marks as cancelled)")
        print("4. Go back")
        
        choice = input("\nSelect option (1-4): ")
        
        if choice == '1':
            if counts['all'] > 0:
                confirm = input(f"\n⚠️  DELETE ALL {counts['all']} BETS? This cannot be undone! (yes/no): ")
                if confirm.lower() == 'yes':
                    cleared = self.bet_manager.clear_all_bets()
                    print(f"✅ Cleared {cleared} bets from database")
                else:
                    print("❌ Cancelled")
            else:
                print("No bets to clear")
                
        elif choice == '2':
            if counts['today'] > 0:
                confirm = input(f"\n⚠️  DELETE today's {counts['today']} bets? (yes/no): ")
                if confirm.lower() == 'yes':
                    cleared = self.bet_manager.clear_todays_bets()
                    print(f"✅ Cleared {cleared} today's bets")
                else:
                    print("❌ Cancelled")
            else:
                print("No bets today to clear")
                
        elif choice == '3':
            if counts['active'] > 0:
                confirm = input(f"\n❓ Cancel {counts['active']} active bets? (yes/no): ")
                if confirm.lower() == 'yes':
                    cancelled = self.bet_manager.cancel_active_bets()
                    print(f"✅ Cancelled {cancelled} active bets")
                else:
                    print("❌ Cancelled")
            else:
                print("No active bets to cancel")
                
        elif choice == '4':
            return
        else:
            print("Invalid option")
    
    def run(self):
        """Main application loop"""
        if not self.setup():
            return
        
        while True:
            # Show data freshness status
            freshness = self.mlb_api.is_data_fresh()
            freshness_icon = "✅" if freshness['is_fresh'] else "⚠️"
            
            print("\n" + "=" * 50)
            print("⚾ MLB BETTING SYSTEM")
            print("=" * 50)
            print(f"{freshness_icon} Today's Games: {freshness['today_games']} | Date: {freshness['today_date']}")
            print("=" * 50)
            print("1. Update MLB Data")
            print("2. Enter New Bet")
            print("3. View Today's Bets")
            print("4. View Active Bets")
            print("5. Clear Bets")
            print("6. Track Live Games")
            print("7. Exit")
            
            choice = input("\nSelect option (1-7): ")
            
            if choice == '1':
                self.update_data()
            elif choice == '2':
                self.enter_bet()
            elif choice == '3':
                self.view_bets()
            elif choice == '4':
                bets = self.bet_manager.get_active_bets()
                print(f"\nActive bets: {len(bets)}")
                for bet in bets[:10]:
                    print(f"  #{bet['bet_id']}: {bet['raw_input']}")
            elif choice == '5':
                self.clear_bets_menu()
            elif choice == '6':
                self.track_live_games()
            elif choice == '7':
                print("\n👋 Goodbye!")
                break
            else:
                print("Invalid option")
    
    def track_live_games(self):
        """Track live games and bet progress"""
        print("\n📊 Live Game Tracking")
        print("=" * 50)
        
        from src.live_tracker import LiveGameTracker
        tracker = LiveGameTracker()
        tracker.track_all_live_games()
        
        # Show summary
        live_bets = tracker.get_active_game_bets()
        if live_bets:
            print(f"\n📈 Tracking {len(live_bets)} active bets")
            for bet in live_bets[:10]:
                current_val = bet.get('result_value') or 0
                target_val = bet.get('target_value') or 0
                print(f"  • {bet.get('player_name', 'Team bet')}: "
                      f"{current_val}/{target_val}")
        else:
            print("\n💤 No live games with active bets right now")
            print("   When games go live, they'll be tracked automatically!")


if __name__ == "__main__":
    app = MLBBettingSystem()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)