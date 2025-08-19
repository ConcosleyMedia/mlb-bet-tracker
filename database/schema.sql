-- ============================================
-- MLB BETTING SYSTEM - COMPLETE PRODUCTION SCHEMA
-- Full Database Design with All Features
-- Version 2.0 - Complete
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. TEAMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS teams (
   team_id INTEGER PRIMARY KEY,
   team_name VARCHAR(100) NOT NULL,
   abbreviation VARCHAR(10) NOT NULL UNIQUE,
   league VARCHAR(20),
   division VARCHAR(20),
   city VARCHAR(50),
   logo_url VARCHAR(255),
   primary_color VARCHAR(7),
   secondary_color VARCHAR(7),
   active BOOLEAN DEFAULT true,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. PLAYERS TABLE  
-- ============================================
CREATE TABLE IF NOT EXISTS players (
   player_id INTEGER PRIMARY KEY,
   full_name VARCHAR(100) NOT NULL,
   first_name VARCHAR(50),
   last_name VARCHAR(50),
   position VARCHAR(10),
   jersey_number INTEGER,
   team_id INTEGER REFERENCES teams(team_id),
   height_inches INTEGER,
   weight_lbs INTEGER,
   birth_date DATE,
   mlb_debut DATE,
   bat_side VARCHAR(1),
   throw_side VARCHAR(1),
   status VARCHAR(20) DEFAULT 'Active',
   salary DECIMAL(12,2),
   player_image_url VARCHAR(255),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. PITCHERS TABLE (Specialized Player Data)
-- ============================================
CREATE TABLE IF NOT EXISTS pitchers (
   pitcher_id INTEGER PRIMARY KEY REFERENCES players(player_id),
   era DECIMAL(4,2),
   whip DECIMAL(4,3),
   strikeout_rate DECIMAL(5,3),
   walk_rate DECIMAL(5,3),
   hr_per_9 DECIMAL(4,2),
   innings_pitched DECIMAL(6,1),
   wins INTEGER DEFAULT 0,
   losses INTEGER DEFAULT 0,
   saves INTEGER DEFAULT 0,
   holds INTEGER DEFAULT 0,
   blown_saves INTEGER DEFAULT 0,
   starter_reliever VARCHAR(10),
   throws_velocity_avg DECIMAL(4,1),
   pitch_count_season INTEGER DEFAULT 0,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 4. VENUES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS venues (
   venue_id INTEGER PRIMARY KEY,
   venue_name VARCHAR(100) NOT NULL,
   city VARCHAR(50),
   state VARCHAR(20),
   capacity INTEGER,
   surface VARCHAR(20),
   roof_type VARCHAR(20),
   timezone VARCHAR(50),
   elevation_ft INTEGER,
   coordinates_lat DECIMAL(10,8),
   coordinates_lng DECIMAL(11,8),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. GAMES TABLE (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS games (
   game_id INTEGER PRIMARY KEY,
   game_date DATE NOT NULL,
   game_time TIMESTAMP NOT NULL,
   home_team_id INTEGER REFERENCES teams(team_id),
   away_team_id INTEGER REFERENCES teams(team_id),
   venue_id INTEGER REFERENCES venues(venue_id),
   status VARCHAR(30) DEFAULT 'Scheduled',
   home_score INTEGER DEFAULT 0,
   away_score INTEGER DEFAULT 0,
   inning INTEGER DEFAULT 1,
   inning_state VARCHAR(20),
   home_probable_pitcher INTEGER REFERENCES pitchers(pitcher_id),
   away_probable_pitcher INTEGER REFERENCES pitchers(pitcher_id),
   weather_temp INTEGER,
   weather_condition VARCHAR(50),
   wind_speed INTEGER,
   wind_direction VARCHAR(10),
   attendance INTEGER,
   game_duration_minutes INTEGER,
   doubleheader BOOLEAN DEFAULT false,
   postponed BOOLEAN DEFAULT false,
   suspended BOOLEAN DEFAULT false,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 6. LIVE GAME UPDATES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS live_game_updates (
   update_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   inning INTEGER,
   inning_half VARCHAR(10),
   play_description TEXT,
   batter_id INTEGER REFERENCES players(player_id),
   pitcher_id INTEGER REFERENCES pitchers(pitcher_id),
   home_score INTEGER,
   away_score INTEGER,
   balls INTEGER DEFAULT 0,
   strikes INTEGER DEFAULT 0,
   outs INTEGER DEFAULT 0,
   runners_on_base TEXT,
   play_type VARCHAR(50),
   update_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. COMMUNITIES TABLE (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS communities (
   community_id SERIAL PRIMARY KEY,
   community_name VARCHAR(50) NOT NULL UNIQUE,
   tier_level INTEGER NOT NULL,
   price DECIMAL(6,2) DEFAULT 0,
   description TEXT,
   max_members INTEGER,
   current_members INTEGER DEFAULT 0,
   features JSONB,
   discord_webhook_url VARCHAR(255),
   telegram_chat_id VARCHAR(50),
   active BOOLEAN DEFAULT true,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 8. COMMUNITY MEMBERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS community_members (
   member_id SERIAL PRIMARY KEY,
   community_id INTEGER REFERENCES communities(community_id),
   user_email VARCHAR(255) NOT NULL,
   user_name VARCHAR(100),
   subscription_start DATE,
   subscription_end DATE,
   subscription_status VARCHAR(20) DEFAULT 'Active',
   payment_method VARCHAR(50),
   total_paid DECIMAL(8,2) DEFAULT 0,
   join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   notification_preferences JSONB,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   UNIQUE(community_id, user_email)
);

-- ============================================
-- 9. BETS TABLE (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS bets (
   bet_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   player_id INTEGER REFERENCES players(player_id),
   pitcher_id INTEGER REFERENCES pitchers(pitcher_id),
   team_id INTEGER REFERENCES teams(team_id),
   opposing_team_id INTEGER REFERENCES teams(team_id),
   bet_type VARCHAR(50) NOT NULL,
   bet_category VARCHAR(30) DEFAULT 'unknown',
   stat_type VARCHAR(30),
   target_value DECIMAL(6,2),
   operator VARCHAR(10),
   odds VARCHAR(20) NOT NULL,
   decimal_odds DECIMAL(6,3),
   implied_probability DECIMAL(5,3),
   units DECIMAL(4,2) NOT NULL,
   community_id INTEGER REFERENCES communities(community_id),
   status VARCHAR(20) DEFAULT 'Pending',
   result_value DECIMAL(6,2),
   actual_result VARCHAR(10),
   payout DECIMAL(10,2),
   roi DECIMAL(6,3),
   confidence_level INTEGER,
   raw_input TEXT,
   ai_confidence INTEGER,
   ai_interpretation TEXT,
   bet_reasoning TEXT,
   weather_factor BOOLEAN DEFAULT false,
   injury_factor BOOLEAN DEFAULT false,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   settled_at TIMESTAMP
);

-- ============================================
-- 10. BET TRACKING TABLE (Real-time Updates)
-- ============================================
CREATE TABLE IF NOT EXISTS bet_tracking (
   tracking_id SERIAL PRIMARY KEY,
   bet_id INTEGER REFERENCES bets(bet_id),
   game_id INTEGER REFERENCES games(game_id),
   current_value DECIMAL(6,2),
   target_value DECIMAL(6,2),
   progress_percentage DECIMAL(5,2),
   is_live BOOLEAN DEFAULT false,
   last_update_inning INTEGER,
   estimated_completion_inning INTEGER,
   probability_of_hit DECIMAL(5,3),
   alert_sent BOOLEAN DEFAULT false,
   milestone_alerts JSONB,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 11. PLAYER GAME STATS TABLE (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS player_game_stats (
   stat_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   player_id INTEGER REFERENCES players(player_id),
   at_bats INTEGER DEFAULT 0,
   hits INTEGER DEFAULT 0,
   singles INTEGER DEFAULT 0,
   doubles INTEGER DEFAULT 0,
   triples INTEGER DEFAULT 0,
   home_runs INTEGER DEFAULT 0,
   runs INTEGER DEFAULT 0,
   rbis INTEGER DEFAULT 0,
   walks INTEGER DEFAULT 0,
   strikeouts INTEGER DEFAULT 0,
   stolen_bases INTEGER DEFAULT 0,
   caught_stealing INTEGER DEFAULT 0,
   hit_by_pitch INTEGER DEFAULT 0,
   sacrifice_flies INTEGER DEFAULT 0,
   batting_avg DECIMAL(4,3),
   on_base_pct DECIMAL(4,3),
   slugging_pct DECIMAL(4,3),
   ops DECIMAL(4,3),
   risp_at_bats INTEGER DEFAULT 0,
   risp_hits INTEGER DEFAULT 0,
   clutch_situations INTEGER DEFAULT 0,
   clutch_hits INTEGER DEFAULT 0,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   UNIQUE(game_id, player_id)
);

-- ============================================
-- 12. PITCHER GAME STATS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS pitcher_game_stats (
   stat_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   pitcher_id INTEGER REFERENCES pitchers(pitcher_id),
   innings_pitched DECIMAL(4,2) DEFAULT 0,
   hits_allowed INTEGER DEFAULT 0,
   runs_allowed INTEGER DEFAULT 0,
   earned_runs INTEGER DEFAULT 0,
   walks_allowed INTEGER DEFAULT 0,
   strikeouts INTEGER DEFAULT 0,
   home_runs_allowed INTEGER DEFAULT 0,
   hit_batters INTEGER DEFAULT 0,
   wild_pitches INTEGER DEFAULT 0,
   win BOOLEAN DEFAULT false,
   loss BOOLEAN DEFAULT false,
   save BOOLEAN DEFAULT false,
   hold BOOLEAN DEFAULT false,
   blown_save BOOLEAN DEFAULT false,
   pitch_count INTEGER DEFAULT 0,
   strikes INTEGER DEFAULT 0,
   first_pitch_strikes INTEGER DEFAULT 0,
   era_game DECIMAL(4,2),
   whip_game DECIMAL(4,3),
   k_per_9 DECIMAL(4,2),
   inherited_runners INTEGER DEFAULT 0,
   inherited_scored INTEGER DEFAULT 0,
   leverage_situations INTEGER DEFAULT 0,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   UNIQUE(game_id, pitcher_id)
);

-- ============================================
-- 13. DAILY SCHEDULES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS daily_schedules (
   schedule_id SERIAL PRIMARY KEY,
   schedule_date DATE NOT NULL UNIQUE,
   total_games INTEGER DEFAULT 0,
   games_completed INTEGER DEFAULT 0,
   weather_delays INTEGER DEFAULT 0,
   postponements INTEGER DEFAULT 0,
   schedule_notes TEXT,
   data_last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 14. MESSAGE LOG TABLE (Enhanced)
-- ============================================
CREATE TABLE IF NOT EXISTS message_log (
   message_id SERIAL PRIMARY KEY,
   community_id INTEGER REFERENCES communities(community_id),
   message_type VARCHAR(50),
   message_content TEXT,
   message_title VARCHAR(200),
   recipient_count INTEGER DEFAULT 0,
   delivery_method VARCHAR(20),
   delivery_status VARCHAR(20) DEFAULT 'pending',
   bet_id INTEGER REFERENCES bets(bet_id),
   game_id INTEGER REFERENCES games(game_id),
   priority_level INTEGER DEFAULT 1,
   scheduled_send_time TIMESTAMP,
   sent_at TIMESTAMP,
   error_message TEXT,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 15. ALERT PREFERENCES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS alert_preferences (
   preference_id SERIAL PRIMARY KEY,
   member_id INTEGER REFERENCES community_members(member_id),
   alert_type VARCHAR(50),
   enabled BOOLEAN DEFAULT true,
   delivery_method VARCHAR(20),
   timing_minutes_before INTEGER DEFAULT 0,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   UNIQUE(member_id, alert_type, delivery_method)
);

-- ============================================
-- 16. HISTORICAL PERFORMANCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS historical_performance (
   performance_id SERIAL PRIMARY KEY,
   community_id INTEGER REFERENCES communities(community_id),
   date_range_start DATE,
   date_range_end DATE,
   total_bets INTEGER,
   won_bets INTEGER,
   lost_bets INTEGER,
   push_bets INTEGER,
   win_percentage DECIMAL(5,3),
   total_units_wagered DECIMAL(8,2),
   total_units_won DECIMAL(8,2),
   net_units DECIMAL(8,2),
   roi DECIMAL(6,3),
   avg_odds DECIMAL(6,3),
   best_bet_type VARCHAR(50),
   worst_bet_type VARCHAR(50),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 17. WEATHER DATA TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS weather_data (
   weather_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   venue_id INTEGER REFERENCES venues(venue_id),
   temperature_f INTEGER,
   humidity_pct INTEGER,
   wind_speed_mph INTEGER,
   wind_direction VARCHAR(10),
   precipitation_pct INTEGER,
   weather_condition VARCHAR(50),
   air_pressure DECIMAL(6,2),
   visibility_miles DECIMAL(4,1),
   forecast_accuracy INTEGER,
   weather_impact_score INTEGER,
   data_source VARCHAR(50),
   recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 18. INJURY REPORTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS injury_reports (
   injury_id SERIAL PRIMARY KEY,
   player_id INTEGER REFERENCES players(player_id),
   injury_type VARCHAR(100),
   body_part VARCHAR(50),
   severity VARCHAR(20),
   status VARCHAR(30),
   injury_date DATE,
   expected_return DATE,
   actual_return DATE,
   impact_on_performance TEXT,
   source VARCHAR(100),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 19. ODDS HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS odds_history (
   odds_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   bookmaker VARCHAR(50),
   bet_type VARCHAR(50),
   team_id INTEGER REFERENCES teams(team_id),
   player_id INTEGER REFERENCES players(player_id),
   opening_line VARCHAR(20),
   current_line VARCHAR(20),
   line_movement VARCHAR(10),
   total_movement DECIMAL(5,2),
   sharp_action BOOLEAN DEFAULT false,
   public_percentage DECIMAL(5,2),
   money_percentage DECIMAL(5,2),
   recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 20. BETTING TRENDS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS betting_trends (
   trend_id SERIAL PRIMARY KEY,
   player_id INTEGER REFERENCES players(player_id),
   team_id INTEGER REFERENCES teams(team_id),
   trend_type VARCHAR(50),
   trend_description TEXT,
   occurrence_count INTEGER DEFAULT 0,
   success_rate DECIMAL(5,3),
   last_occurrence DATE,
   confidence_score DECIMAL(5,3),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 21. AUTOMATED PICKS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS automated_picks (
   pick_id SERIAL PRIMARY KEY,
   game_id INTEGER REFERENCES games(game_id),
   community_id INTEGER REFERENCES communities(community_id),
   pick_type VARCHAR(50),
   pick_description TEXT,
   confidence_score DECIMAL(5,3),
   edge_percentage DECIMAL(5,2),
   model_version VARCHAR(20),
   factors_considered JSONB,
   published BOOLEAN DEFAULT false,
   published_at TIMESTAMP,
   result VARCHAR(20),
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 22. BANKROLL MANAGEMENT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS bankroll_management (
   bankroll_id SERIAL PRIMARY KEY,
   member_id INTEGER REFERENCES community_members(member_id),
   starting_bankroll DECIMAL(10,2),
   current_bankroll DECIMAL(10,2),
   unit_size DECIMAL(6,2),
   kelly_criterion BOOLEAN DEFAULT false,
   max_units_per_bet DECIMAL(4,2) DEFAULT 5.0,
   max_daily_exposure DECIMAL(6,2),
   current_daily_exposure DECIMAL(6,2) DEFAULT 0,
   stop_loss_amount DECIMAL(10,2),
   take_profit_amount DECIMAL(10,2),
   last_reset_date DATE,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 23. NOTIFICATION QUEUE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS notification_queue (
   queue_id SERIAL PRIMARY KEY,
   message_id INTEGER REFERENCES message_log(message_id),
   member_id INTEGER REFERENCES community_members(member_id),
   notification_type VARCHAR(50),
   priority INTEGER DEFAULT 1,
   scheduled_time TIMESTAMP,
   retry_count INTEGER DEFAULT 0,
   max_retries INTEGER DEFAULT 3,
   status VARCHAR(20) DEFAULT 'queued',
   error_log TEXT,
   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
   processed_at TIMESTAMP
);

-- ============================================
-- CREATE ALL INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_games_date ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_games_teams ON games(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_bets_status ON bets(status);
CREATE INDEX IF NOT EXISTS idx_bets_community ON bets(community_id);
CREATE INDEX IF NOT EXISTS idx_bets_game ON bets(game_id);
CREATE INDEX IF NOT EXISTS idx_bets_created ON bets(created_at);
CREATE INDEX IF NOT EXISTS idx_bets_type_category ON bets(bet_type, bet_category);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
CREATE INDEX IF NOT EXISTS idx_players_status ON players(status);
CREATE INDEX IF NOT EXISTS idx_pitchers_era ON pitchers(era);
CREATE INDEX IF NOT EXISTS idx_pitchers_type ON pitchers(starter_reliever);
CREATE INDEX IF NOT EXISTS idx_player_stats_game ON player_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_game_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_pitcher_stats_game ON pitcher_game_stats(game_id);
CREATE INDEX IF NOT EXISTS idx_pitcher_stats_pitcher ON pitcher_game_stats(pitcher_id);
CREATE INDEX IF NOT EXISTS idx_bet_tracking_bet ON bet_tracking(bet_id);
CREATE INDEX IF NOT EXISTS idx_bet_tracking_live ON bet_tracking(is_live);
CREATE INDEX IF NOT EXISTS idx_live_updates_game ON live_game_updates(game_id);
CREATE INDEX IF NOT EXISTS idx_live_updates_time ON live_game_updates(update_timestamp);
CREATE INDEX IF NOT EXISTS idx_community_members_email ON community_members(user_email);
CREATE INDEX IF NOT EXISTS idx_community_members_status ON community_members(subscription_status);
CREATE INDEX IF NOT EXISTS idx_message_log_community ON message_log(community_id);
CREATE INDEX IF NOT EXISTS idx_message_log_type ON message_log(message_type);
CREATE INDEX IF NOT EXISTS idx_message_log_status ON message_log(delivery_status);
CREATE INDEX IF NOT EXISTS idx_odds_history_game ON odds_history(game_id);
CREATE INDEX IF NOT EXISTS idx_odds_history_time ON odds_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_trends_player ON betting_trends(player_id);
CREATE INDEX IF NOT EXISTS idx_trends_team ON betting_trends(team_id);
CREATE INDEX IF NOT EXISTS idx_auto_picks_game ON automated_picks(game_id);
CREATE INDEX IF NOT EXISTS idx_auto_picks_published ON automated_picks(published);
CREATE INDEX IF NOT EXISTS idx_notification_queue_status ON notification_queue(status);
CREATE INDEX IF NOT EXISTS idx_notification_queue_scheduled ON notification_queue(scheduled_time);

-- ============================================
-- CREATE UPDATE TRIGGER FUNCTION
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

-- ============================================
-- APPLY UPDATE TRIGGERS
-- ============================================
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pitchers_updated_at BEFORE UPDATE ON pitchers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_games_updated_at BEFORE UPDATE ON games FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_communities_updated_at BEFORE UPDATE ON communities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bets_updated_at BEFORE UPDATE ON bets FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bet_tracking_updated_at BEFORE UPDATE ON bet_tracking FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_player_stats_updated_at BEFORE UPDATE ON player_game_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pitcher_stats_updated_at BEFORE UPDATE ON pitcher_game_stats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_injury_reports_updated_at BEFORE UPDATE ON injury_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_betting_trends_updated_at BEFORE UPDATE ON betting_trends FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bankroll_updated_at BEFORE UPDATE ON bankroll_management FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_alert_prefs_updated_at BEFORE UPDATE ON alert_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- CREATE VIEWS
-- ============================================

-- Active bets with full details
CREATE OR REPLACE VIEW v_active_bets AS
SELECT 
   b.*,
   g.game_date,
   g.game_time,
   g.status as game_status,
   p.full_name as player_name,
   t.team_name,
   ot.team_name as opposing_team_name,
   c.community_name,
   c.tier_level,
   bt.current_value,
   bt.progress_percentage
FROM bets b
JOIN games g ON b.game_id = g.game_id
LEFT JOIN players p ON b.player_id = p.player_id
LEFT JOIN teams t ON b.team_id = t.team_id
LEFT JOIN teams ot ON b.opposing_team_id = ot.team_id
JOIN communities c ON b.community_id = c.community_id
LEFT JOIN bet_tracking bt ON b.bet_id = bt.bet_id
WHERE b.status IN ('Pending', 'Live');

-- Today's schedule with betting info
CREATE OR REPLACE VIEW v_todays_schedule AS
SELECT 
   g.*,
   ht.team_name as home_team_name,
   at.team_name as away_team_name,
   hpp.full_name as home_pitcher_name,
   app.full_name as away_pitcher_name,
   v.venue_name,
   COUNT(DISTINCT b.bet_id) as total_bets_on_game
FROM games g
JOIN teams ht ON g.home_team_id = ht.team_id
JOIN teams at ON g.away_team_id = at.team_id
LEFT JOIN players hpp ON g.home_probable_pitcher = hpp.player_id
LEFT JOIN players app ON g.away_probable_pitcher = app.player_id
LEFT JOIN venues v ON g.venue_id = v.venue_id
LEFT JOIN bets b ON g.game_id = b.game_id
WHERE g.game_date = CURRENT_DATE
GROUP BY g.game_id, ht.team_name, at.team_name, hpp.full_name, app.full_name, v.venue_name;

-- Community performance dashboard
CREATE OR REPLACE VIEW v_community_performance AS
SELECT 
   c.community_name,
   c.tier_level,
   COUNT(DISTINCT cm.member_id) as member_count,
   COUNT(b.bet_id) as total_bets,
   SUM(CASE WHEN b.status = 'Won' THEN 1 ELSE 0 END) as wins,
   SUM(CASE WHEN b.status = 'Lost' THEN 1 ELSE 0 END) as losses,
   ROUND(AVG(CASE WHEN b.status = 'Won' THEN 100.0 ELSE 0 END), 2) as win_rate,
   SUM(b.units) as total_units_risked,
   SUM(CASE WHEN b.status = 'Won' THEN b.payout ELSE 0 END) as total_payout,
   ROUND(SUM(CASE WHEN b.status = 'Won' THEN b.payout - b.units WHEN b.status = 'Lost' THEN -b.units ELSE 0 END), 2) as net_units
FROM communities c
LEFT JOIN community_members cm ON c.community_id = cm.community_id
LEFT JOIN bets b ON c.community_id = b.community_id
WHERE b.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.community_id, c.community_name, c.tier_level;

-- Player hot streaks view
CREATE OR REPLACE VIEW v_player_hot_streaks AS
SELECT 
   p.player_id,
   p.full_name,
   t.team_name,
   COUNT(DISTINCT pgs.game_id) as games_played,
   AVG(pgs.hits) as avg_hits,
   AVG(pgs.home_runs) as avg_hrs,
   AVG(pgs.rbis) as avg_rbis,
   MAX(pgs.hits) as max_hits,
   MAX(pgs.home_runs) as max_hrs
FROM players p
JOIN teams t ON p.team_id = t.team_id
JOIN player_game_stats pgs ON p.player_id = pgs.player_id
JOIN games g ON pgs.game_id = g.game_id
WHERE g.game_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY p.player_id, p.full_name, t.team_name
HAVING COUNT(DISTINCT pgs.game_id) >= 3
ORDER BY AVG(pgs.hits) DESC;

-- Pitcher matchup analysis view
CREATE OR REPLACE VIEW v_pitcher_matchups AS
SELECT 
   p.pitcher_id,
   p.era,
   p.whip,
   pit.full_name as pitcher_name,
   t.team_name,
   COUNT(DISTINCT pgs.game_id) as games_pitched,
   AVG(pgs.innings_pitched) as avg_innings,
   AVG(pgs.strikeouts) as avg_strikeouts,
   AVG(pgs.earned_runs) as avg_earned_runs
FROM pitchers p
JOIN players pit ON p.pitcher_id = pit.player_id
JOIN teams t ON pit.team_id = t.team_id
LEFT JOIN pitcher_game_stats pgs ON p.pitcher_id = pgs.pitcher_id
GROUP BY p.pitcher_id, p.era, p.whip, pit.full_name, t.team_name;

-- ============================================
-- INSERT INITIAL DATA
-- ============================================
INSERT INTO communities (community_name, tier_level, price, description, max_members, features) VALUES
('StatEdge', 1, 0, 'Free community with basic MLB betting insights', 1000, '["daily_picks", "basic_stats"]'),
('StatEdge+', 2, 19.99, 'Premium tier with advanced analytics and live tracking', 500, '["daily_picks", "advanced_stats", "live_tracking", "discord_access"]'),
('StatEdge Premium', 3, 49.99, 'VIP tier with exclusive picks and personal consultation', 100, '["daily_picks", "advanced_stats", "live_tracking", "discord_access", "exclusive_picks", "consultation", "weather_analysis"]')
ON CONFLICT (community_name) DO NOTHING;

-- Insert initial daily schedule for today
INSERT INTO daily_schedules (schedule_date, total_games, data_last_updated) 
VALUES (CURRENT_DATE, 0, CURRENT_TIMESTAMP)
ON CONFLICT (schedule_date) DO NOTHING;

-- ============================================
-- VERIFICATION QUERY
-- ============================================
SELECT 
   'Database Setup Complete!' as status,
   COUNT(*) as total_tables,
   STRING_AGG(table_name, ', ' ORDER BY table_name) as tables_created
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE';