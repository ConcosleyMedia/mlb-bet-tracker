#!/usr/bin/env python3
"""Process queued messages and send to Whop forums"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import db
from src.whop_client import WhopGraphQLClient
from src.message_generator import MessageGenerator

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

async def process_message_queue():
    """Process pending messages for Whop"""
    logger = logging.getLogger(__name__)
    
    # Get pending messages with bet details
    messages = db.fetch_dict("""
        SELECT 
            m.*,
            c.community_name,
            b.raw_input,
            b.bet_type,
            b.odds,
            b.units,
            b.player_id,
            b.team_id,
            p.full_name as player_name,
            t.team_name
        FROM message_log m
        JOIN communities c ON m.community_id = c.community_id
        JOIN bets b ON m.bet_id = b.bet_id
        LEFT JOIN players p ON b.player_id = p.player_id
        LEFT JOIN teams t ON b.team_id = t.team_id
        WHERE m.delivery_status = 'pending'
        AND m.scheduled_send_time <= NOW()
        ORDER BY m.priority_level DESC, m.created_at ASC
        LIMIT 10
    """)

    if not messages:
        logger.info("No pending messages")
        return

    # Initialize Whop client
    whop = WhopGraphQLClient()
    generator = MessageGenerator()
    
    try:
        await whop.initialize()
        
        processed_count = 0
        success_count = 0
        
        for msg in messages:
            try:
                processed_count += 1
                logger.info(f"Processing message {msg['message_id']} ({processed_count}/{len(messages)})")
                
                # Generate message content based on type
                if msg['message_type'] == 'pregame':
                    generated = generator.generate_pregame_message(msg, msg['community_name'])
                elif msg['message_type'] == 'milestone':
                    generated = generator.generate_milestone_message(msg, msg['community_name'])
                elif msg['message_type'] == 'won':
                    generated = generator.generate_win_message(msg, msg['community_name'])
                else:
                    # Use pre-generated content
                    generated = {
                        'title': msg['message_title'],
                        'content': msg['message_content']
                    }
                
                # Post to appropriate community
                success = False
                
                if msg['community_name'] == 'StatEdge Premium':
                    success = await whop.post_premium_bet(
                        title=generated['title'],
                        content=generated['content'],
                        paywall_amount=19.99
                    )
                elif msg['community_name'] == 'StatEdge+':
                    success = await whop.post_vip_bet(
                        title=generated['title'],
                        content=generated['content']
                    )
                else:  # StatEdge Free
                    success = await whop.post_free_bet(
                        title=generated['title'],
                        content=generated['content']
                    )
                
                if success:
                    db.execute("""
                        UPDATE message_log 
                        SET delivery_status = 'sent',
                            sent_at = CURRENT_TIMESTAMP
                        WHERE message_id = %s
                    """, (msg['message_id'],))
                    
                    success_count += 1
                    logger.info(f"✅ Posted to {msg['community_name']}: {generated['title']}")
                else:
                    raise Exception("Whop post failed")
                    
            except Exception as e:
                logger.error(f"❌ Error processing message {msg['message_id']}: {e}")
                
                db.execute("""
                    UPDATE message_log 
                    SET delivery_status = 'failed',
                        error_message = %s
                    WHERE message_id = %s
                """, (str(e), msg['message_id']))
        
        logger.info(f"📊 Processed {processed_count} messages, {success_count} successful")
        
    finally:
        await whop.close()

async def main():
    """Main async message processing execution"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 WHOP MESSAGE PROCESSING STARTED")
    
    try:
        # Test database connection
        if not db.test_connection():
            logger.error("Database connection failed - aborting")
            sys.exit(1)
        
        # Process message queue
        await process_message_queue()
        
        # Clean up old messages (older than 7 days)
        cleanup_date = datetime.now() - timedelta(days=7)
        deleted_count = db.execute("""
            DELETE FROM message_log 
            WHERE created_at < %s 
            AND delivery_status IN ('sent', 'failed')
        """, (cleanup_date,))
        
        logger.info(f"📧 Cleaned up {deleted_count or 0} old messages")
        logger.info("✅ Whop message processing completed")
        
    except Exception as e:
        logger.error(f"💥 Critical error in message processing: {e}")
        sys.exit(1)

def sync_main():
    """Synchronous wrapper for async main"""
    asyncio.run(main())

if __name__ == "__main__":
    sync_main()