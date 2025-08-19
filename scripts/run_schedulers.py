#!/usr/bin/env python3
"""Run all schedulers - streak detection, pre-game alerts, and marketing"""

import sys
import os
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import db
from src.streak_detector import StreakDetector
from src.pregame_scheduler import PregameScheduler
from src.marketing_scheduler import MarketingScheduler

def setup_logging():
    """Configure logging"""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'schedulers.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    """Run all scheduling tasks"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("RUNNING SCHEDULERS")
    logger.info("=" * 60)
    
    try:
        # Test database
        if not db.test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
        
        total_messages = 0
        
        # 1. Check for winning streaks
        logger.info("Checking for winning streaks...")
        streak_detector = StreakDetector()
        streaks = streak_detector.check_all_streaks()
        
        for streak in streaks:
            if not streak['already_notified']:
                messages = streak_detector.trigger_streak_notifications(streak)
                total_messages += messages
                logger.info(f"Triggered {messages} streak notifications")
        
        # 2. Schedule pre-game alerts
        logger.info("Scheduling pre-game alerts...")
        pregame_scheduler = PregameScheduler()
        pregame_messages = pregame_scheduler.schedule_todays_pregame_alerts()
        total_messages += pregame_messages
        logger.info(f"Scheduled {pregame_messages} pre-game alerts")
        
        # 3. Schedule marketing messages
        logger.info("Scheduling marketing messages...")
        marketing_scheduler = MarketingScheduler()
        marketing_messages = marketing_scheduler.schedule_daily_marketing()
        total_messages += marketing_messages
        logger.info(f"Scheduled {marketing_messages} marketing messages")
        
        # Summary
        logger.info(f"Total messages scheduled: {total_messages}")
        
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()