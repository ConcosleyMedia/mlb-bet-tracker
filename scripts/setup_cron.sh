#!/bin/bash
# Setup cron jobs for automated MLB live tracking and message processing
# Run this script once to install automated background monitoring

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Setting up MLB Betting System automation..."
echo "Project directory: $PROJECT_DIR"

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$PROJECT_DIR/scripts/track_live.py"
chmod +x "$PROJECT_DIR/scripts/process_messages.py"
chmod +x "$PROJECT_DIR/scripts/run_schedulers.py"

# Create logs directory if it doesn't exist
echo "Creating logs directory..."
mkdir -p "$PROJECT_DIR/logs"

# Backup existing crontab
echo "Backing up existing crontab..."
crontab -l > "$PROJECT_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab to backup"

# Create temporary cron file
cat > /tmp/mlb_cron_jobs << 'EOF'
# MLB Betting System - Live Game Tracking (runs every 3 minutes during game hours)
*/3 12-23 * * * cd PROJECT_DIR_PLACEHOLDER && PROJECT_DIR_PLACEHOLDER/venv/bin/python scripts/track_live.py >> logs/cron_tracking.log 2>&1

# MLB Betting System - Message Processing (runs every minute)
* * * * * cd PROJECT_DIR_PLACEHOLDER && PROJECT_DIR_PLACEHOLDER/venv/bin/python scripts/process_messages.py >> logs/cron_messages.log 2>&1

# MLB Betting System - Schedulers (runs every hour)
0 * * * * cd PROJECT_DIR_PLACEHOLDER && PROJECT_DIR_PLACEHOLDER/venv/bin/python scripts/run_schedulers.py >> logs/cron_schedulers.log 2>&1

# MLB Betting System - Daily Data Refresh (6 AM ET)
0 6 * * * cd PROJECT_DIR_PLACEHOLDER && PROJECT_DIR_PLACEHOLDER/venv/bin/python scripts/update_data.py >> logs/cron_daily.log 2>&1
EOF

# Replace placeholder with actual project directory
sed -i '' "s|PROJECT_DIR_PLACEHOLDER|$PROJECT_DIR|g" /tmp/mlb_cron_jobs

# Add cron jobs to existing crontab
echo "Installing cron jobs..."
(crontab -l 2>/dev/null; cat /tmp/mlb_cron_jobs) | crontab -

# Clean up temporary file
rm /tmp/mlb_cron_jobs

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "AUTOMATION SCHEDULE:"
echo "📊 Live Tracking: Every 3 minutes (12 PM - 11 PM ET)"
echo "📨 Message Processing: Every minute"
echo "🎯 Schedulers: Every hour (streaks, pre-game, marketing)"
echo "🔄 Daily Data Refresh: 6 AM ET"
echo ""
echo "LOG FILES:"
echo "  • Live tracking: $PROJECT_DIR/logs/live_tracking.log"
echo "  • Message processing: $PROJECT_DIR/logs/message_processing.log"
echo "  • Schedulers: $PROJECT_DIR/logs/schedulers.log"
echo "  • Cron output: $PROJECT_DIR/logs/cron_*.log"
echo ""
echo "MANAGEMENT COMMANDS:"
echo "  • View cron jobs: crontab -l | grep MLB"
echo "  • Remove cron jobs: crontab -e (delete MLB lines)"
echo "  • Check logs: tail -f $PROJECT_DIR/logs/live_tracking.log"
echo ""
echo "🚀 Your MLB betting system is now running automatically!"
echo "   Live tracking will start when games begin."