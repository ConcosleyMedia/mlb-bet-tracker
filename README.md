# MLB Betting System

Complete production-ready MLB betting system with AI-powered bet parsing, smart validation, auto-refresh, and comprehensive community management.

## ✨ **Latest Features (v2.0)**
- 🌅 **Daily Auto-Refresh**: Automatically updates MLB data each morning - no manual refresh needed
- 🎯 **Smart Bet Validation**: Only accepts bets for players actually playing today  
- 📅 **Proper Date Filtering**: "Today's Bets" shows bets for today's games (not when bet was created)
- 🗑️ **Enhanced Clear Bets**: Safe bet cleanup with confirmation prompts and multiple options
- 🔄 **Auto Status Updates**: Yesterday's bets automatically marked as completed
- ⚡ **Optimized Morning Workflow**: Open app → immediately start logging picks

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Setup Database
1. Go to your Supabase SQL Editor
2. Copy and paste the complete SQL from `database/schema.sql`
3. Run the SQL to create all 18 tables

### 3. Configure Environment
1. Update `.env` with your actual credentials:
   - Replace `[YOUR-PASSWORD]` with your Supabase password
   - Add your OpenAI API key

### 4. Run Setup
```bash
python3 scripts/setup.py
```

### 5. Test the System
```bash
python3 scripts/test_system.py
```

### 6. Run Main Application
```bash
python3 main.py
```

## 🌅 **Perfect Morning Workflow**

The system is now optimized for daily pick logging:

1. **Open Terminal & Run App** - `python main.py`
   - App automatically checks if MLB data is fresh
   - Auto-refreshes games/rosters if stale (no manual refresh needed!)

2. **Immediate Pick Entry** - Select option 2
   - Smart validation ensures only today's players are accepted
   - AI parses your bets: `"harper 2 hrs -110 2u"` → structured data

3. **View Today's Bets** - Select option 3  
   - Shows only bets for TODAY's games (not yesterday's lingering bets)
   - Yesterday's bets automatically marked as completed

4. **Clean Management** - Select option 5 when needed
   - Clear test bets safely with confirmation prompts
   - Multiple options: all bets, today only, or cancel active bets

**No more**:
- ❌ Forgetting to update data manually
- ❌ Yesterday's bets showing as "today's"
- ❌ Accepting bets for players not playing
- ❌ Confusion between bet creation date vs game date

## 📁 Project Structure

```
mlb-betting-system/
├── .env                    # Environment variables (copy from .env.example)
├── .env.example           # Environment template for setup
├── .gitignore             # Git ignore file  
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── main.py               # Main application with enhanced menu
├── database/
│   └── schema.sql        # Complete database schema (23 tables)
├── src/
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connection & utilities
│   ├── mlb_api.py        # MLB API integration + auto-refresh
│   ├── openai_parser.py  # AI bet parsing with OpenAI
│   ├── smart_validator.py # Smart bet validation (NEW)
│   └── bet_manager.py    # Enhanced bet management + clear options
└── scripts/              # Setup and test scripts
    ├── setup.py          # Initial setup script
    └── test_system.py    # System tests
```

## 🎯 Complete Feature Set

### **Core Betting System** 
- ✅ AI-powered bet parsing with OpenAI GPT
- ✅ **Smart bet validation** - Only accepts bets for players actually playing today
- ✅ **Intelligent error handling** - Suggests correct player names for typos
- ✅ **Daily auto-refresh** - Automatically updates stale MLB data
- ✅ Real-time bet tracking with progress monitoring
- ✅ Advanced bet analytics and ROI calculations
- ✅ **Enhanced bet management** - Clear bets safely with multiple options

### **MLB Data Integration**
- ✅ Complete MLB Stats API integration
- ✅ Real-time game feeds and live updates
- ✅ Player and pitcher comprehensive statistics
- ✅ Team, venue, and schedule management
- ✅ Historical performance tracking

### **Community Management**
- ✅ Multi-tier community system (Free, Premium, VIP)
- ✅ Member subscription and payment tracking
- ✅ Customizable notification preferences
- ✅ Discord and Telegram integration
- ✅ Message delivery tracking and analytics

### **Live Tracking & Alerts**
- ✅ Real-time game monitoring
- ✅ Play-by-play bet progress updates
- ✅ Milestone alerts (50%, 80%, completion)
- ✅ Pre-game notifications and reminders
- ✅ Weather delay and postponement tracking

### **Advanced Analytics**
- ✅ Historical performance analysis
- ✅ Weather impact scoring
- ✅ Injury report integration
- ✅ Pitcher vs batter matchup analysis
- ✅ Venue-specific statistics

### **Technical Infrastructure**
- ✅ Production-ready PostgreSQL schema (18 tables)
- ✅ Comprehensive indexing for performance
- ✅ Automatic timestamp triggers
- ✅ JSONB support for flexible data
- ✅ UUID extension support

## 💡 Usage Examples

### **Smart Bet Validation in Action**

```bash
# ✅ Valid bet (player is playing today):
"Harper 2 HRs -110 2u"
→ ✅ Bryce Harper plays for Philadelphia Phillies in today's game

# ❌ Invalid bet (typo in name):
"Shohei Otani home runs over 0.5"  
→ ❌ 'Shohei Otani' not found in today's active rosters
→ 🎯 Did you mean: Shohei Ohtani (Los Angeles Dodgers)?

# ❌ Invalid bet (player not playing today):
"Wheeler over 6 Ks"
→ ❌ 'Zack Wheeler' is not a probable pitcher today
→ 🎯 Today's probable pitchers:
   • Dylan Cease (Padres vs Giants)
   • Logan Webb (Giants vs Padres)

# ✅ More valid examples:
"Phillies ML -150"
"Cease over 6.5 Ks +100 1.5 units" 
"Dodgers team total over 4.5 -115 2u"
```

### **Daily Auto-Refresh**
```bash
# When you start the app with stale data:
🔍 Checking data freshness...
  Today's games: 0
🔄 Data is stale - auto-refreshing...
✅ Data refreshed successfully

# When data is already fresh:  
🔍 Checking data freshness...
  Today's games: 13
✅ Data is fresh
```

## 🗄️ Database Schema

The comprehensive schema includes 18 production-ready tables:

**Core Tables:**
1. `teams` - MLB teams with colors, logos, divisions
2. `players` - Player info with physical stats, salaries
3. `pitchers` - Specialized pitcher statistics
4. `venues` - Stadium information with coordinates
5. `games` - Enhanced game data with weather, attendance

**Tracking Tables:**
6. `live_game_updates` - Real-time play-by-play
7. `bet_tracking` - Live bet progress monitoring
8. `player_game_stats` - Comprehensive batting stats
9. `pitcher_game_stats` - Complete pitching metrics
10. `daily_schedules` - Schedule management

**Community Tables:**
11. `communities` - Multi-tier system with features
12. `community_members` - Member subscription tracking
13. `message_log` - Multi-platform messaging
14. `alert_preferences` - Custom notification settings

**Analytics Tables:**
15. `historical_performance` - Performance analytics
16. `weather_data` - Weather impact analysis
17. `injury_reports` - Player injury tracking
18. `bets` - Enhanced betting with ROI tracking

## 🔧 Configuration

Update your `.env` file with:
```env
# Database
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.uzxqrliphwwejocnwijc.supabase.co:5432/postgres

# APIs
OPENAI_API_KEY=your-openai-api-key-here
MLB_API_BASE_URL=https://statsapi.mlb.com/api/v1

# Settings
ENVIRONMENT=development
DEBUG=True
```

## 🚀 Production Ready

This system is designed for production use with:
- Comprehensive error handling
- Performance optimized queries
- Scalable database design
- Real-time data processing
- Multi-platform notifications
- Advanced analytics and reporting