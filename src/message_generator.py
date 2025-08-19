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
        
        prompt = f"""
        Create a {style['tone']} progress update for a betting milestone.
        
        Bet details:
        - Team: {bet.get('team_name', bet.get('player_name'))}
        - Type: {bet['bet_type']}
        - Progress: {milestone}% complete
        - Current value: {bet.get('current_value', 'tracking')}
        - Target: {bet.get('target_value', 'unknown')}
        
        Style guidelines:
        - Tone: {style['tone']}
        - Use emojis: {style['emojis']}
        - Show excitement for progress
        - Keep it engaging and short
        
        Format as:
        TITLE: [title]
        CONTENT: [content]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create exciting sports betting progress updates."},
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
                'title': title or f"{milestone}% Complete! {style['emojis']}",
                'content': content or f"Our pick is {milestone}% of the way there!"
            }
            
        except Exception as e:
            logger.error(f"OpenAI milestone generation failed: {e}")
            return {
                'title': f"{milestone}% Complete! {style['emojis']}",
                'content': f"Our pick is {milestone}% of the way there!"
            }
    
    def generate_win_message(self, bet: Dict, community: str) -> Dict:
        """Generate victory celebration message"""
        
        style = self.tier_styles[community]
        
        prompt = f"""
        Create an {style['tone']} VICTORY celebration message.
        
        Winning bet details:
        - Team: {bet.get('team_name', bet.get('player_name'))}
        - Type: {bet['bet_type']}
        - Odds: {bet['odds']}
        - Units: {bet['units']}
        - Final result: WON
        
        Style guidelines:
        - Tone: {style['tone']} but VERY EXCITED
        - Use emojis: {style['emojis']} plus victory emojis
        - Celebrate the win enthusiastically
        - For Premium: Show value won
        - Keep it hype and authentic
        
        Format as:
        TITLE: [title]
        CONTENT: [content]
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You create hype victory celebrations for sports betting wins."},
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
            
            return {
                'title': title or f"WINNER! {style['emojis']} 🎉",
                'content': content or f"Our pick just hit! {style['emojis']} Another W for the books!"
            }
            
        except Exception as e:
            logger.error(f"OpenAI win generation failed: {e}")
            return {
                'title': f"WINNER! {style['emojis']} 🎉",
                'content': f"Our pick just hit! {style['emojis']} Another W for the books!"
            }
    
    def _get_fallback_title(self, bet: Dict, community: str) -> str:
        """Fallback title if OpenAI fails"""
        if community == 'StatEdge Premium':
            return f"$19,999 PREMIUM SELECTION 🌟"
        elif community == 'StatEdge+':
            return f"VIP {bet.get('team_name', 'Pick')} | {bet['bet_type']}"
        else:
            return f"{bet.get('team_name', 'Pick')} $1,000 SLIP 👇"
    
    def _get_fallback_content(self, bet: Dict, community: str) -> str:
        """Fallback content if OpenAI fails"""
        base = f"{bet['raw_input']} | Odds: {bet['odds']}"
        
        if community == 'StatEdge Premium':
            return f"{base}\n\n💎 PREMIUM EXCLUSIVE - $19.99 to unlock"
        elif community == 'StatEdge+':
            return f"{base}\n\n🔥 VIP MEMBERS ONLY"
        else:
            return f"{base}\n\nWant VIP + Premium access? Link in bio"