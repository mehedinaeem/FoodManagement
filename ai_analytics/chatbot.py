"""
NourishBot - Multi-Capability AI Chatbot
Provides food waste reduction advice, nutrition balancing, meal planning, and more.
"""

import json
import os
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from logs.models import FoodLog
from inventory.models import InventoryItem
from ai_analytics.models import ChatSession, ChatMessage
from ai_analytics.ai_engine import AIConsumptionAnalyzer
from ai_analytics.waste_estimator import WasteEstimator


class NourishBot:
    """
    AI-powered chatbot for food management and sustainability guidance.
    """
    
    # System prompt for the chatbot
    SYSTEM_PROMPT = """You are NourishBot, a helpful AI assistant for food management and sustainability. 
    Your role is to help users reduce food waste, improve nutrition, plan meals, and make sustainable choices.
    You provide practical, actionable advice based on their consumption patterns and inventory.
    Be friendly, encouraging, and specific in your recommendations."""
    
    # Context templates for different query types
    CONTEXT_TEMPLATES = {
        'waste_reduction': "The user is asking about reducing food waste. Consider their inventory and consumption patterns.",
        'nutrition': "The user is asking about nutrition. Consider their dietary preferences and consumption history.",
        'meal_planning': "The user is asking about meal planning. Consider their budget, inventory, and preferences.",
        'leftovers': "The user is asking about using leftovers creatively.",
        'sharing': "The user is asking about local food sharing opportunities.",
        'environment': "The user is asking about environmental impact of food choices.",
    }
    
    def __init__(self, user, session_id=None):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.session_id = session_id or self._generate_session_id()
        # Initialize analyzers BEFORE creating session (which calls _build_context)
        self.consumption_analyzer = AIConsumptionAnalyzer(user)
        self.waste_estimator = WasteEstimator(user)
        self.session = self._get_or_create_session()
    
    def _generate_session_id(self):
        """Generate unique session ID."""
        return f"{self.user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _get_or_create_session(self):
        """Get or create chat session."""
        try:
            session, created = ChatSession.objects.get_or_create(
                session_id=self.session_id,
                defaults={
                    'user': self.user,
                    'context': self._build_context()
                }
            )
            if not created:
                # Only update context if session belongs to this user
                if session.user == self.user:
                    session.context = self._build_context()
                    session.save()
                else:
                    # Create a new session if it belongs to a different user
                    self.session_id = self._generate_session_id()
                    session = ChatSession.objects.create(
                        session_id=self.session_id,
                        user=self.user,
                        context=self._build_context()
                    )
            return session
        except Exception as e:
            # Fallback: create a new session with a unique ID
            self.session_id = self._generate_session_id()
            return ChatSession.objects.create(
                session_id=self.session_id,
                user=self.user,
                context=self._build_context()
            )
    
    def _build_context(self):
        """Build context about user for the chatbot."""
        try:
            # Get recent activity
            recent_logs = FoodLog.objects.filter(user=self.user).order_by('-date_consumed')[:5]
            expiring_items = InventoryItem.objects.filter(
                user=self.user,
                status='expiring_soon'
            )[:5]
            
            # Safely get waste summary
            try:
                waste_summary = self.waste_estimator.estimate_weekly_waste()
            except Exception as e:
                # Fallback if waste estimation fails
                waste_summary = {
                    'total_waste_grams': 0,
                    'total_waste_cost': 0,
                }
            
            context = {
                'user_profile': {
                    'household_size': self.profile.household_size if self.profile else 1,
                    'dietary_preferences': self.profile.dietary_preferences if self.profile else 'none',
                    'budget_range': self.profile.budget_range if self.profile else 'medium',
                    'location': (self.profile.location if self.profile else None) or 'Not specified',
                },
                'recent_consumption': [
                    {
                        'item': log.item_name,
                        'category': log.category,
                        'date': log.date_consumed.isoformat()
                    }
                    for log in recent_logs
                ],
                'expiring_items': [
                    {
                        'item': item.item_name,
                        'category': item.category,
                        'expires': item.expiration_date.isoformat() if item.expiration_date else None
                    }
                    for item in expiring_items
                ],
                'waste_summary': waste_summary,
            }
            
            return context
        except Exception as e:
            # Return minimal context if something goes wrong
            return {
                'user_profile': {
                    'household_size': self.profile.household_size if self.profile else 1,
                    'dietary_preferences': self.profile.dietary_preferences if self.profile else 'none',
                    'budget_range': self.profile.budget_range if self.profile else 'medium',
                    'location': 'Not specified',
                },
                'recent_consumption': [],
                'expiring_items': [],
                'waste_summary': {
                    'total_waste_grams': 0,
                    'total_waste_cost': 0,
                },
            }
    
    def chat(self, user_message, use_ai=True):
        """
        Process user message and generate response.
        If use_ai=False, uses rule-based responses.
        """
        # Save user message
        ChatMessage.objects.create(
            session=self.session,
            role='user',
            content=user_message
        )
        
        # Detect intent
        intent = self._detect_intent(user_message)
        
        # Generate response
        if use_ai and self._has_openai_key():
            response = self._generate_ai_response(user_message, intent)
        else:
            response = self._generate_rule_based_response(user_message, intent)
        
        # Save assistant response
        ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content=response,
            metadata={'intent': intent}
        )
        
        return response
    
    def _detect_intent(self, message):
        """Detect user intent from message."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['waste', 'throw away', 'expire', 'spoiled']):
            return 'waste_reduction'
        elif any(word in message_lower for word in ['nutrition', 'vitamin', 'nutrient', 'healthy', 'diet']):
            return 'nutrition'
        elif any(word in message_lower for word in ['meal plan', 'plan meals', 'menu', 'shopping']):
            return 'meal_planning'
        elif any(word in message_lower for word in ['leftover', 'left over', 'use up', 'transform']):
            return 'leftovers'
        elif any(word in message_lower for word in ['share', 'donate', 'surplus', 'community']):
            return 'sharing'
        elif any(word in message_lower for word in ['environment', 'carbon', 'sustainable', 'impact']):
            return 'environment'
        else:
            return 'general'
    
    def _generate_ai_response(self, user_message, intent):
        """Generate AI response using OpenAI API."""
        try:
            import openai
            
            # Check for API key
            api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                return self._generate_rule_based_response(user_message, intent)
            
            client = openai.OpenAI(api_key=api_key)
            
            # Build messages
            messages = [
                {'role': 'system', 'content': self.SYSTEM_PROMPT},
                {'role': 'system', 'content': f"User context: {json.dumps(self.session.context, indent=2)}"},
            ]
            
            # Add conversation history (last 5 messages)
            recent_messages = ChatMessage.objects.filter(
                session=self.session
            ).order_by('-created_at')[:5]
            
            for msg in reversed(recent_messages):
                messages.append({
                    'role': msg.role,
                    'content': msg.content
                })
            
            messages.append({'role': 'user', 'content': user_message})
            
            # Call OpenAI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            # Fallback to rule-based
            return self._generate_rule_based_response(user_message, intent)
    
    def _generate_rule_based_response(self, user_message, intent):
        """Generate rule-based response when AI is not available."""
        message_lower = user_message.lower()
        context = self.session.context
        
        if intent == 'waste_reduction':
            expiring = context.get('expiring_items', [])
            if expiring:
                items_list = ", ".join([item['item'] for item in expiring[:3]])
                return f"I see you have some items expiring soon: {items_list}. Here are some tips:\n\n" \
                       f"1. Plan meals around these items first\n" \
                       f"2. Consider freezing items that can be frozen\n" \
                       f"3. Use them in soups, stews, or smoothies\n" \
                       f"4. Share with neighbors or community if you can't use them\n\n" \
                       f"Your weekly waste estimate is {context.get('waste_summary', {}).get('total_waste_grams', 0):.0f} grams. " \
                       f"Try to reduce this by using items before they expire!"
            else:
                return "Great news! You don't have any items expiring soon. Keep up the good work! " \
                       "To prevent waste, try meal planning and only buying what you need."
        
        elif intent == 'nutrition':
            diet_pref = self.profile.get_dietary_preferences_display() if self.profile else "standard"
            return f"Based on your profile, you follow a {diet_pref} diet. " \
                   f"Here are some nutrition tips:\n\n" \
                   f"1. Aim for variety across food categories\n" \
                   f"2. Include plenty of vegetables and fruits\n" \
                   f"3. Balance your meals with protein, carbs, and healthy fats\n" \
                   f"4. Stay hydrated throughout the day\n\n" \
                   f"Would you like specific advice based on your consumption patterns?"
        
        elif intent == 'meal_planning':
            return f"Meal planning can help you save money and reduce waste! Here's how:\n\n" \
                   f"1. Check your inventory first and plan meals around what you have\n" \
                   f"2. Create a weekly meal plan based on your {self.profile.get_budget_range_display()} budget\n" \
                   f"3. Make a shopping list for only what you need\n" \
                   f"4. Prep ingredients in advance to save time\n\n" \
                   f"Would you like me to generate a personalized meal plan for you?"
        
        elif intent == 'leftovers':
            return "Leftovers are a great way to reduce waste! Here are creative ideas:\n\n" \
                   "1. Transform yesterday's vegetables into a frittata or omelet\n" \
                   "2. Turn leftover meat into sandwiches or wraps\n" \
                   "3. Blend fruits into smoothies or make fruit salad\n" \
                   "4. Use leftover rice for fried rice or rice pudding\n" \
                   "5. Make soup or stew from various leftovers\n\n" \
                   "What leftovers do you have? I can give you specific recipe ideas!"
        
        elif intent == 'sharing':
            location = (self.profile.location if self.profile else None) or "your area"
            return f"Food sharing is a wonderful way to reduce waste! Here are options in {location}:\n\n" \
                   "1. Check local community food sharing apps\n" \
                   "2. Connect with neighbors through community groups\n" \
                   "3. Donate to local food banks or shelters\n" \
                   "4. Organize a food swap with friends\n" \
                   "5. Use social media groups for local food sharing\n\n" \
                   "Would you like help finding specific sharing opportunities?"
        
        elif intent == 'environment':
            waste_summary = context.get('waste_summary', {})
            return f"Your food choices impact the environment! Here's your impact:\n\n" \
                   f"• Weekly waste: {waste_summary.get('total_waste_grams', 0):.0f} grams\n" \
                   f"• Estimated cost: ${waste_summary.get('total_waste_cost', 0):.2f}\n\n" \
                   "To reduce environmental impact:\n" \
                   "1. Reduce food waste (biggest impact!)\n" \
                   "2. Choose local and seasonal produce\n" \
                   "3. Reduce meat consumption if possible\n" \
                   "4. Compost food scraps\n" \
                   "5. Buy in bulk to reduce packaging\n\n" \
                   "Every small change makes a difference!"
        
        else:
            return "Hi! I'm NourishBot, your food management assistant. I can help you with:\n\n" \
                   "• Reducing food waste\n" \
                   "• Nutrition and meal planning\n" \
                   "• Creative ways to use leftovers\n" \
                   "• Food sharing opportunities\n" \
                   "• Understanding your environmental impact\n\n" \
                   "What would you like to know? Just ask me anything about food management!"
    
    def _has_openai_key(self):
        """Check if OpenAI API key is available."""
        import os
        from django.conf import settings
        api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        return api_key is not None
    
    def get_conversation_history(self, limit=20):
        """Get conversation history for this session."""
        return ChatMessage.objects.filter(
            session=self.session
        ).order_by('created_at')[:limit]

