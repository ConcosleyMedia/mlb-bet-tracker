#!/usr/bin/env python3
"""
Automated live game tracking script for cron execution
Runs every 2-3 minutes during MLB games
"""

import sys
import os
import logging
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.live_tracker import LiveGameTracker
from src.database import db

def setup_logging():
    """Configure logging for cron execution"""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'live_tracking.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also log to console
        ]
    )

def main():
    """Main tracking execution"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("AUTOMATED LIVE TRACKING STARTED")
    logger.info("=" * 60)
    
    try:
        # Test database connection
        if not db.test_connection():
            logger.error("Database connection failed - aborting")
            sys.exit(1)
        
        # Initialize tracker
        tracker = LiveGameTracker()
        
        # Run tracking
        summary = tracker.track_all_live_games()
        
        # Log summary
        logger.info(f"Tracking Summary:")
        logger.info(f"  Games tracked: {summary['games_tracked']}")
        logger.info(f"  Bets checked: {summary['bets_checked']}")
        logger.info(f"  Bets updated: {summary['bets_updated']}")
        logger.info(f"  Messages queued: {summary['messages_queued']}")
        logger.info(f"  Winners: {len(summary['winners'])}")
        logger.info(f"  Errors: {len(summary['errors'])}")
        logger.info(f"  Duration: {summary.get('duration_seconds', 0):.1f}s")
        
        # Log winners
        for winner in summary['winners']:
            logger.info(f"🎉 BET WON: {winner['player']} ({winner['community']})")
        
        # Log errors
        for error in summary['errors']:
            logger.error(f"Tracking error: {error}")
        
        # Exit code based on results
        if summary['errors'] and not summary['bets_updated']:
            logger.warning("No bets updated due to errors")
            sys.exit(1)
        
        logger.info("Automated tracking completed successfully")
        
    except Exception as e:
        logger.error(f"Critical error in automated tracking: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()