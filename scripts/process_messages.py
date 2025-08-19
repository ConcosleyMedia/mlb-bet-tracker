#!/usr/bin/env python3
"""
Process queued messages and send notifications
Runs every minute to send pending messages to Discord/Telegram
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.message_sender import MessageSender
from src.database import db

def setup_logging():
    """Configure logging for message processing"""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'message_processing.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_pending_messages():
    """Get messages ready to be sent"""
    return db.fetch_dict("""
        SELECT 
            ml.*,
            c.community_name,
            c.discord_webhook_url,
            c.telegram_chat_id
        FROM message_log ml
        JOIN communities c ON ml.community_id = c.community_id
        WHERE ml.status = 'Pending'
        AND ml.scheduled_send_time <= %s
        ORDER BY ml.priority_level DESC, ml.created_at ASC
        LIMIT 50
    """, (datetime.now(),))

def send_message(sender, message):
    """Send a single message and update status"""
    try:
        # Attempt to send message
        success = sender.send_message(message)
        
        if success:
            # Mark as sent
            db.execute("""
                UPDATE message_log 
                SET status = 'Sent',
                    sent_at = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE log_id = %s
            """, (datetime.now(), message['log_id']))
            
            return True
        else:
            # Mark as failed
            db.execute("""
                UPDATE message_log 
                SET status = 'Failed',
                    updated_at = CURRENT_TIMESTAMP
                WHERE log_id = %s
            """, (message['log_id'],))
            
            return False
            
    except Exception as e:
        logging.error(f"Failed to send message {message['log_id']}: {e}")
        
        # Mark as failed
        db.execute("""
            UPDATE message_log 
            SET status = 'Failed',
                error_message = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE log_id = %s
        """, (str(e), message['log_id']))
        
        return False

def main():
    """Main message processing execution"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("MESSAGE PROCESSING STARTED")
    
    try:
        # Test database connection
        if not db.test_connection():
            logger.error("Database connection failed - aborting")
            sys.exit(1)
        
        # Get pending messages
        pending_messages = get_pending_messages()
        
        if not pending_messages:
            logger.info("No pending messages to process")
            return
        
        logger.info(f"Processing {len(pending_messages)} pending messages")
        
        # Initialize message sender
        sender = MessageSender()
        
        # Process each message
        sent_count = 0
        failed_count = 0
        
        for message in pending_messages:
            logger.info(f"Processing message {message['log_id']}: {message['message_title']}")
            
            if send_message(sender, message):
                sent_count += 1
                logger.info(f"✅ Message {message['log_id']} sent successfully")
            else:
                failed_count += 1
                logger.error(f"❌ Message {message['log_id']} failed to send")
        
        # Log summary
        logger.info(f"Message processing complete:")
        logger.info(f"  Sent: {sent_count}")
        logger.info(f"  Failed: {failed_count}")
        
        # Clean up old messages (older than 7 days)
        cleanup_date = datetime.now() - timedelta(days=7)
        db.execute("""
            DELETE FROM message_log 
            WHERE created_at < %s 
            AND status IN ('Sent', 'Failed')
        """, (cleanup_date,))
        
        logger.info("Old messages cleaned up")
        
    except Exception as e:
        logger.error(f"Critical error in message processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()