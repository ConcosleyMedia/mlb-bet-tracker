"""Generate authentic betting messages with OpenAI"""

import openai
import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class MessageGenerator:
    """Generate TrustMySystem-style messages"""
    
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        self.tier_styles = {
            'StatEdge': {
                'tone': 'friendly, accessible, community-focused',
                'emojis': '👇💰',
                'cta': 'Want VIP + Premium access?'
            },
            'StatEdge+': {
                'tone': 'confident, professional, insider knowledge',
                'emojis': '🔥⚡',
                'cta': None
            },
            'StatEdge Premium': {
                'tone': 'exclusive, high-energy, premium value',
                'emojis': '🌟💎🚀',
                'cta': None,
                'value_multiplier': 19.999  # Show as $19,999
            }
        }
    
    def generate_pregame_message(self, bet: Dict, community: str) -> Dict:
        """Generate pre-game announcement"""
        
        style = self.tier_styles[community]
        
        # Build prompt for OpenAI
        prompt = f"""
        Create a {style['tone']} pre-game betting announcement.
        
        Bet details:
        - Team: {bet.get('team_name', bet.get('player_name'))}
        - Type: {bet['bet_type']}
        - Odds: {bet['odds']}
        - Units: {bet['units']}
        
        Style guidelines:
        - Tone: {style['tone']}
        - Use emojis: {style['emojis']}
        - For Premium: Show value as ${int(bet['units'] * style.get('value_multiplier', 1) * 1000):,}
        - For VIP: Show as "{bet['units']}k"
        - Keep it short and impactful
        
        Format as:
        TITLE: [title]
        CONTENT: [content]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create authentic sports betting community messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Parse response
            text = response.choices[0].message.content
            lines = text.split('\n')
            
            title = ""
            content = ""
            
            for line in lines:
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('CONTENT:'):
                    content = line.replace('CONTENT:', '').strip()
            
            # Add CTA for free tier
            if community == 'StatEdge' and style['cta']:
                content += f"\n\n{style['cta']}"
            
            return {
                'title': title or self._get_fallback_title(bet, community),
                'content': content or self._get_fallback_content(bet, community)
            }
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return {
                'title': self._get_fallback_title(bet, community),
                'content': self._get_fallback_content(bet, community)
            }
    
    def generate_milestone_message(self, bet: Dict, community: str) -> Dict:
        """Generate milestone progress message"""
        
        style = self.tier_styles[community]
        milestone = bet.get('milestone_percentage', 0)
        
        # Create human betting language based on progress
        current = bet.get('current_value', 0)
        target = bet.get('target_value', 1)
        player = bet.get('player_name', bet.get('team_name', 'Our pick'))
        bet_type = bet.get('bet_type', 'bet')
        
        # Fix remaining calculation with proper betting math
        # For over bets: need to exceed target (1.5 → need 2 total, 2.5 → need 3 total)
        import math
        if current and target:
            # Calculate how many total needed to win
            needed_total = math.ceil(target) if target != int(target) else int(target) + 1
            remaining = max(0, needed_total - int(current))
        else:
            remaining = 1
        
        # Determine progress stage for human language
        if current >= target:
            progress_stage = "WE HIT! Cashing baby!"
        elif current == 0:
            progress_stage = "just getting started"
        elif current >= target * 0.9:
            progress_stage = "SO CLOSE! Almost there"
        elif current >= target * 0.5:
            progress_stage = "halfway there"
        else:
            progress_stage = "building momentum"
        
        prompt = f"""
        Create a {style['tone']} live betting update that sounds like a real person hyping their friends.
        
        Situation:
        - Player: {player}
        - Bet: {bet_type}
        - Current: {int(current) if current else 0}
        - Need: {int(target) if target else 1} total
        - Remaining: {remaining} more to hit
        - Stage: {progress_stage}
        
        Write like a betting enthusiast, NOT a robot:
        - NO percentages or "% complete"
        - Use "halfway there", "almost there", "1 more to go"
        - Add excitement: "let's go!", "we're cooking!", "cashing baby!"
        - Sound human and hyped
        - Tone: {style['tone']} but conversational
        - Emojis: {style['emojis']}
        
        Format as:
        TITLE: [exciting human title]
        CONTENT: [hype message like you're texting friends]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You're a hype betting enthusiast texting friends about live bets. Sound human, excited, and conversational. NO corporate language or percentages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9
            )
            
            # Parse response
            text = response.choices[0].message.content
            lines = text.split('\n')
            
            title = ""
            content = ""
            
            for line in lines:
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('CONTENT:'):
                    content = line.replace('CONTENT:', '').strip()
            
            # Create human fallback based on progress
            if current >= target:
                fallback_title = f"WE HIT! {style['emojis']}"
                fallback_content = f"{player} just cashed our {bet_type} bet! Let's go! {style['emojis']}"
            elif remaining == 1:
                fallback_title = f"1 MORE TO GO! {style['emojis']}"
                fallback_content = f"{player} needs just 1 more {bet_type} and we're cashing! {style['emojis']}"
            elif progress_stage == "halfway there":
                fallback_title = f"Halfway there! {style['emojis']}"
                fallback_content = f"{player} got {int(current)}! {remaining} more to go and we're golden! {style['emojis']}"
            else:
                fallback_title = f"{player} cooking! {style['emojis']}"
                fallback_content = f"Tracking {player} - {remaining} {bet_type} to go! Let's ride! {style['emojis']}"
            
            return {
                'title': title or fallback_title,
                'content': content or fallback_content
            }
            
        except Exception as e:
            logger.error(f"OpenAI milestone generation failed: {e}")
            return {
                'title': f"{milestone}% Complete! {style['emojis']}",
                'content': f"Our pick is {milestone}% of the way there!"
            }
    
    def generate_win_message(self, bet: Dict, community: str) -> Dict:
        """Generate simple 1-sentence victory message"""
        
        style = self.tier_styles[community]
        
        # Simple 1-sentence win messages
        team_or_player = bet.get('team_name', bet.get('player_name', 'Our pick'))
        bet_type = bet.get('bet_type', 'bet')
        odds = bet.get('odds', '+100')
        units = bet.get('units', 1)
        
        # Create simple, direct win message
        if bet_type.lower() == 'total':
            content = f"{team_or_player} Total {odds} ({units}u) ✅ HITS!"
        elif bet_type.lower() in ['moneyline', 'ml']:
            content = f"{team_or_player} ML {odds} ({units}u) ✅ CASHES!"
        else:
            content = f"{team_or_player} {bet_type} {odds} ({units}u) ✅ WINNER!"
        
        return {
            'title': f"🎉 WINNER",
            'content': content
        }
    
    def _get_fallback_title(self, bet: Dict, community: str) -> str:
        """Fallback title if OpenAI fails"""
        if community == 'StatEdge Premium':
            return f"$19,999 PREMIUM SELECTION 🌟"
        elif community == 'StatEdge+':
            return f"VIP {bet.get('team_name', 'Pick')} | {bet['bet_type']}"
        else:
            return f"{bet.get('team_name', 'Pick')} $1,000 SLIP 👇"
    
    def generate_streak_message(self, data: Dict, community: str) -> Dict:
        """Generate streak notification message"""
        
        style = self.tier_styles[community]
        consecutive_wins = data.get('consecutive_wins', 3)
        source_community = data.get('source_community', community)
        
        prompt = f"""
        Create a {style['tone']} winning streak announcement.
        
        Context:
        - Streak: {consecutive_wins} consecutive wins
        - Source: {source_community} {'(higher tier)' if source_community != community else ''}
        - Recent wins: {data.get('recent_wins', [])}
        
        Style guidelines:
        - Tone: {style['tone']}
        - Use fire/streak emojis: 🔥🎯⚡
        - If cross-tier: mention the higher tier's success
        - If same-tier: celebrate together
        - Include CTA if appropriate for tier
        
        Format as:
        TITLE: [exciting streak title]
        CONTENT: [streak celebration message]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create exciting winning streak announcements."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9
            )
            
            text = response.choices[0].message.content
            lines = text.split('\n')
            
            title = ""
            content = ""
            
            for line in lines:
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('CONTENT:'):
                    content = line.replace('CONTENT:', '').strip()
            
            # Add tier-specific CTA if cross-tier
            if source_community != community and community == 'StatEdge':
                content += f"\n\nWant access to {source_community} picks? Upgrade now!"
            
            return {
                'title': title or f"🔥 {consecutive_wins}-BET WIN STREAK!",
                'content': content or f"We're on fire with {consecutive_wins} straight wins!"
            }
            
        except Exception as e:
            logger.error(f"OpenAI streak generation failed: {e}")
            return {
                'title': f"🔥 {consecutive_wins}-BET WIN STREAK!",
                'content': f"{source_community} is on fire with {consecutive_wins} straight wins! 🎯"
            }
    
    def generate_marketing_message(self, data: Dict, community: str) -> Dict:
        """Generate marketing/upsell message"""
        
        style = self.tier_styles[community]
        message_variant = data.get('variant', 'upsell')
        
        # Pre-written marketing messages by tier
        if community == 'StatEdge':
            # Free tier upsells
            if message_variant == 'trial':
                return {
                    'title': '🔓 2-Day VIP Trial Available!',
                    'content': 'Get instant access to StatEdge+ premium picks!\n\n'
                              '✅ All VIP picks for 48 hours\n'
                              '✅ Live bet tracking\n'
                              '✅ Win rate: 67% this month\n\n'
                              'Start your trial now → Link in bio'
                }
            elif message_variant == 'results':
                return {
                    'title': '💎 See What Premium Members Won Today',
                    'content': f"StatEdge+ members hit {data.get('wins', 3)} winners today!\n\n"
                              f"{data.get('examples', '• Multiple winning bets listed here')}\n\n"
                              'Upgrade for tomorrow\'s picks!'
                }
            else:
                return {
                    'title': '🚀 Level Up Your Betting',
                    'content': 'Free picks are great, but VIP is better!\n\n'
                              'StatEdge+ Features:\n'
                              '• 3-4 daily premium picks\n'
                              '• Advanced analytics\n'
                              '• Priority support\n\n'
                              'Try 2 days FREE → Link in bio'
                }
        
        elif community == 'StatEdge+':
            # Plus tier teasers
            return {
                'title': '🌟 Premium Pick Preview',
                'content': 'Premium members getting exclusive access:\n\n'
                          '🔒 [High-Value Pick Locked]\n'
                          'Confidence: ⭐⭐⭐⭐⭐\n'
                          'Value: $19.99\n\n'
                          'Unlock with Premium membership!'
            }
        
        else:  # Premium
            # Premium exclusive content
            return {
                'title': '🎁 FREE Bonus Pick - Premium Only!',
                'content': 'Exclusive for Premium members:\n\n'
                          f"⚾ {data.get('bonus_pick', 'Special analytics-based pick')}\n\n"
                          'This bonus pick is FREE for Premium members only!'
            }

    def generate_smart_milestone_message(self, bet: Dict, milestone_type: str, community: str) -> Dict:
        """Generate smart milestone messages with positive framing"""
        
        style = self.tier_styles[community]
        
        # Build context-aware prompts based on milestone type
        prompts = {
            'first_progress': f"""
            Create a {style['tone']} update celebrating the first milestone.
            
            Context:
            - Player: {bet.get('player_name')}
            - Got their first: {bet['bet_type']} (needs {bet.get('target_value', 2)} total)
            - Current: {bet.get('current_value', 1)} of {bet.get('target_value', 2)}
            
            Guidelines:
            - Celebrate the progress
            - Stay positive about remaining target
            - Use emojis: {style['emojis']}
            - Keep it brief and exciting
            
            Format as:
            TITLE: [brief exciting title]
            CONTENT: [positive update message]
            """,
            
            'halfway': f"""
            Create a {style['tone']} momentum update showing strong progress.
            
            Context:
            - Pitcher: {bet.get('player_name')}
            - Strikeouts: {bet.get('current_value')} of {bet.get('target_value')} Ks
            - Inning: {bet.get('inning', 'mid-game')}
            
            Guidelines:
            - Emphasize the momentum/dealing
            - Project confidence
            - Use fire/heat emojis
            - Tone: {style['tone']}
            
            Format as:
            TITLE: [momentum title]
            CONTENT: [confident progress update]
            """,
            
            'last_chance': f"""
            Create a {style['tone']} opportunity alert for a late-game chance.
            
            Context:
            - Player: {bet.get('player_name')}
            - Needs: 1 more {bet['bet_type']}
            - Situation: Late innings, final opportunities
            
            Guidelines:
            - Build anticipation (not worry)
            - "Let's see some magic" vibe
            - Keep it exciting and hopeful
            - Emojis: {style['emojis']} + 👀✨
            
            Format as:
            TITLE: [anticipation title]
            CONTENT: [exciting opportunity message]
            """
        }
        
        prompt = prompts.get(milestone_type, prompts['first_progress'])
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create positive, exciting sports betting updates. Never sound worried or negative."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            
            # Parse response
            text = response.choices[0].message.content
            lines = text.split('\n')
            
            title = ""
            content = ""
            
            for line in lines:
                if line.startswith('TITLE:'):
                    title = line.replace('TITLE:', '').strip()
                elif line.startswith('CONTENT:'):
                    content = line.replace('CONTENT:', '').strip()
            
            return {
                'title': title or self._get_smart_fallback_title(bet, milestone_type, community),
                'content': content or self._get_smart_fallback_content(bet, milestone_type, community)
            }
            
        except Exception as e:
            logger.error(f"OpenAI smart milestone generation failed: {e}")
            return {
                'title': self._get_smart_fallback_title(bet, milestone_type, community),
                'content': self._get_smart_fallback_content(bet, milestone_type, community)
            }

    def _get_smart_fallback_title(self, bet: Dict, milestone_type: str, community: str) -> str:
        """Smart fallback titles"""
        player = bet.get('player_name', 'Player')
        
        if milestone_type == 'first_progress':
            return f"⚾ {player} gets his first!"
        elif milestone_type == 'halfway':
            return f"🔥 {player} dealing!"
        elif milestone_type == 'last_chance':
            return f"👀 {player} - opportunity knocks!"
        elif milestone_type == 'lead_change':
            return f"💪 Lead change alert!"
        else:
            return f"📈 Live update - {player}"

    def _get_smart_fallback_content(self, bet: Dict, milestone_type: str, community: str) -> str:
        """Smart fallback content"""
        current = bet.get('current_value', 0)
        target = bet.get('target_value', 0)
        
        if milestone_type == 'first_progress':
            return f"{current}/{target} - great start! {target - current} more to go 🎯"
        elif milestone_type == 'halfway':
            return f"{current} Ks and counting! Momentum building 🔥"
        elif milestone_type == 'last_chance':
            return f"One more needed - let's see some magic! ✨"
        else:
            return f"Progress: {current}/{target} - tracking live!"

    def _get_fallback_content(self, bet: Dict, community: str) -> str:
        """Fallback content if OpenAI fails"""
        base = f"{bet['raw_input']} | Odds: {bet['odds']}"
        
        if community == 'StatEdge Premium':
            return f"{base}\n\n💎 PREMIUM EXCLUSIVE - $19.99 to unlock"
        elif community == 'StatEdge+':
            return f"{base}\n\n🔥 VIP MEMBERS ONLY"
        else:
            return f"{base}\n\nWant VIP + Premium access? Link in bio"