"""
NourishBot - Multi-Capability AI Chatbot
Enhanced with contextual memory, resource retrieval, and comprehensive capabilities.
"""

import json
import os
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from logs.models import FoodLog
from inventory.models import InventoryItem
from resources.models import Resource
from ai_analytics.models import ChatSession, ChatMessage
from ai_analytics.ai_engine import AIConsumptionAnalyzer
from ai_analytics.waste_estimator import WasteEstimator
from ai_analytics.expiration_predictor import ExpirationRiskPredictor


class NourishBot:
    """
    Enhanced AI-powered chatbot for food management and sustainability guidance.
    Features:
    - Multi-capability handling (waste, nutrition, meal planning, leftovers, sharing, environment)
    - Contextual memory with prompt chaining
    - Resource retrieval from database
    - Rule-based fallback with comprehensive tips
    """
    
    # Enhanced system prompt
    SYSTEM_PROMPT = """You are NourishBot, an expert AI assistant for food management, sustainability, and nutrition.

Your capabilities include:
1. Food Waste Reduction: Provide practical advice on reducing food waste, using expiring items, and preservation techniques
2. Nutrition Balancing: Offer guidance on balanced nutrition, dietary requirements, and healthy eating patterns
3. Budget Meal Planning: Help create cost-effective meal plans that use available inventory and fit budgets
4. Leftover Transformation: Suggest creative recipes and ideas to transform leftovers into delicious meals
5. Local Food Sharing: Guide users on sharing surplus food with community, food banks, and neighbors
6. Environmental Impact: Explain how food choices affect the environment and suggest sustainable practices

Always:
- Be friendly, encouraging, and practical
- Provide specific, actionable advice
- Reference the user's actual inventory and consumption patterns when relevant
- Use the provided context about their food items, waste patterns, and preferences
- Be concise but informative
- Offer step-by-step guidance when appropriate"""
    
    # Enhanced intent detection keywords
    INTENT_KEYWORDS = {
        'waste_reduction': [
            'waste', 'throw away', 'expire', 'spoiled', 'rotten', 'garbage', 
            'trash', 'discard', 'reduce waste', 'prevent waste', 'save food',
            'expiring', 'expiration', 'going bad', 'spoiling'
        ],
        'nutrition': [
            'nutrition', 'nutrient', 'vitamin', 'healthy', 'diet', 'protein',
            'carb', 'calorie', 'balanced', 'health', 'wellness', 'nutritious',
            'vitamins', 'minerals', 'dietary', 'nutritional'
        ],
        'meal_planning': [
            'meal plan', 'plan meals', 'menu', 'shopping list', 'weekly meals',
            'meal prep', 'planning', 'what to cook', 'meal ideas', 'recipes',
            'cook', 'prepare', 'budget meals', 'cheap meals'
        ],
        'leftovers': [
            'leftover', 'left over', 'left overs', 'use up', 'transform',
            'repurpose', 'reuse', 'old food', 'yesterday', 'remaining',
            'extra food', 'surplus food', 'leftover recipe'
        ],
        'sharing': [
            'share', 'donate', 'surplus', 'community', 'food bank', 'give away',
            'charity', 'neighbor', 'local sharing', 'food sharing', 'donation',
            'help others', 'share food'
        ],
        'environment': [
            'environment', 'carbon', 'sustainable', 'impact', 'climate',
            'eco', 'green', 'footprint', 'emission', 'sustainability',
            'environmental', 'planet', 'earth'
        ],
    }
    
    # Comprehensive rule-based tips database
    TIPS_DATABASE = {
        'waste_reduction': [
            "Plan meals around items expiring soon - use them first!",
            "Freeze items before they expire - most foods can be frozen",
            "Use the FIFO method: First In, First Out - older items first",
            "Store fruits and vegetables properly - different items need different storage",
            "Turn overripe fruits into smoothies, jams, or baked goods",
            "Use vegetable scraps to make broth or stock",
            "Preserve herbs by freezing in oil or drying them",
            "Check your inventory before shopping to avoid duplicates",
            "Portion control helps reduce leftovers and waste",
            "Compost food scraps instead of throwing them away",
        ],
        'nutrition': [
            "Aim for a colorful plate - variety ensures diverse nutrients",
            "Include protein, carbs, and healthy fats in each meal",
            "Eat plenty of vegetables - aim for 5 servings daily",
            "Choose whole grains over refined grains when possible",
            "Stay hydrated - drink water throughout the day",
            "Balance your meals - don't skip any food groups",
            "Include healthy fats like avocados, nuts, and olive oil",
            "Eat fruits for natural sugars and vitamins",
            "Plan meals to include all essential nutrients",
            "Listen to your body's hunger and fullness cues",
        ],
        'meal_planning': [
            "Check your inventory first - plan meals around what you have",
            "Create a weekly meal plan to save time and money",
            "Make a shopping list based on your meal plan",
            "Prep ingredients in advance for easier cooking",
            "Cook in batches and freeze portions for later",
            "Plan meals that use similar ingredients to reduce waste",
            "Consider your schedule - plan quick meals for busy days",
            "Include leftovers in your meal plan",
            "Plan for variety to avoid meal fatigue",
            "Budget-friendly tip: Plan meals around sales and seasonal produce",
        ],
        'leftovers': [
            "Transform leftover vegetables into frittatas or omelets",
            "Turn leftover meat into sandwiches, wraps, or salads",
            "Use leftover rice for fried rice or rice pudding",
            "Blend leftover fruits into smoothies or make fruit salad",
            "Make soup or stew from various leftovers",
            "Create casseroles or bakes from leftover ingredients",
            "Turn leftover bread into croutons or bread pudding",
            "Use leftover pasta in pasta salads or frittatas",
            "Transform leftovers into new cuisines - be creative!",
            "Freeze leftovers in portion sizes for future meals",
        ],
        'sharing': [
            "Check local food sharing apps like Olio, Too Good To Go",
            "Connect with neighbors through community groups or apps",
            "Donate to local food banks or shelters",
            "Organize a food swap with friends or neighbors",
            "Use social media groups for local food sharing",
            "Check if your area has community fridges or food pantries",
            "Share surplus garden produce with neighbors",
            "Coordinate with local restaurants or cafes for food rescue",
            "Join or start a community food sharing initiative",
            "Share knowledge - teach others about food preservation",
        ],
        'environment': [
            "Reducing food waste is the #1 way to reduce your food carbon footprint",
            "Choose local and seasonal produce to reduce transportation emissions",
            "Reduce meat consumption - plant-based meals have lower environmental impact",
            "Compost food scraps to reduce methane emissions from landfills",
            "Buy in bulk to reduce packaging waste",
            "Choose products with minimal packaging",
            "Support sustainable farming practices when possible",
            "Reduce food miles by buying locally",
            "Every meal saved from waste reduces greenhouse gas emissions",
            "Your food choices directly impact water usage and land use",
        ],
    }
    
    def __init__(self, user, session_id=None):
        self.user = user
        self.profile = getattr(user, 'profile', None)
        self.session_id = session_id or self._generate_session_id()
        # Initialize analyzers BEFORE creating session
        self.consumption_analyzer = AIConsumptionAnalyzer(user)
        self.waste_estimator = WasteEstimator(user)
        self.expiration_predictor = ExpirationRiskPredictor(user)
        self.session = self._get_or_create_session()
    
    def _generate_session_id(self):
        """Generate unique session ID."""
        return f"{self.user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _get_or_create_session(self):
        """Get or create chat session with enhanced context."""
        try:
            session, created = ChatSession.objects.get_or_create(
                session_id=self.session_id,
                defaults={
                    'user': self.user,
                    'context': self._build_context()
                }
            )
            if not created:
                if session.user == self.user:
                    # Update context to include latest data
                    session.context = self._build_context()
                    session.save()
                else:
                    self.session_id = self._generate_session_id()
                    session = ChatSession.objects.create(
                        session_id=self.session_id,
                        user=self.user,
                        context=self._build_context()
                    )
            return session
        except Exception as e:
            self.session_id = self._generate_session_id()
            return ChatSession.objects.create(
                session_id=self.session_id,
                user=self.user,
                context=self._build_context()
            )
    
    def _build_context(self):
        """Build comprehensive context about user for the chatbot."""
        try:
            # Get recent activity
            recent_logs = FoodLog.objects.filter(user=self.user).order_by('-date_consumed')[:10]
            expiring_items = InventoryItem.objects.filter(
                user=self.user,
                status='expiring_soon'
            )[:10]
            
            # Get consumption patterns
            try:
                patterns = self.consumption_analyzer.analyze_weekly_trends()
                imbalances = self.consumption_analyzer.detect_category_imbalances()
            except:
                patterns = {}
                imbalances = []
            
            # Get waste summary
            try:
                waste_summary = self.waste_estimator.estimate_weekly_waste()
            except:
                waste_summary = {'total_waste_grams': 0, 'total_waste_cost': 0}
            
            # Get expiration risks
            try:
                expiration_risks = self.expiration_predictor.get_high_risk_alerts(limit=5)
            except:
                expiration_risks = []
            
            # Get top consumed categories
            category_counts = {}
            for log in recent_logs:
                cat = log.category
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
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
                        'quantity': str(log.quantity),
                        'date': log.date_consumed.isoformat()
                    }
                    for log in recent_logs
                ],
                'expiring_items': [
                    {
                        'item': item.item_name,
                        'category': item.category,
                        'quantity': str(item.quantity),
                        'expires': item.expiration_date.isoformat() if item.expiration_date else None,
                        'days_left': (item.expiration_date - timezone.now().date()).days if item.expiration_date else None
                    }
                    for item in expiring_items
                ],
                'expiration_risks': [
                    {
                        'item': risk['item_name'],
                        'days_until_expiry': risk['days_until_expiry'],
                        'risk_score': float(risk['risk_score']),
                    }
                    for risk in expiration_risks
                ],
                'waste_summary': waste_summary,
                'consumption_patterns': {
                    'top_categories': dict(list(category_counts.items())[:5]),
                    'total_logs': recent_logs.count(),
                },
                'imbalances': [
                    {
                        'category': imb['category'],
                        'status': imb['status'],
                        'message': imb['message']
                    }
                    for imb in imbalances[:3]
                ] if imbalances else [],
            }
            
            return context
        except Exception as e:
            return {
                'user_profile': {
                    'household_size': self.profile.household_size if self.profile else 1,
                    'dietary_preferences': self.profile.dietary_preferences if self.profile else 'none',
                    'budget_range': self.profile.budget_range if self.profile else 'medium',
                    'location': 'Not specified',
                },
                'recent_consumption': [],
                'expiring_items': [],
                'expiration_risks': [],
                'waste_summary': {'total_waste_grams': 0, 'total_waste_cost': 0},
                'consumption_patterns': {},
                'imbalances': [],
            }
    
    def chat(self, user_message, use_ai=True):
        """
        Process user message and generate response with enhanced context.
        """
        # Save user message
        ChatMessage.objects.create(
            session=self.session,
            role='user',
            content=user_message
        )
        
        # Detect intent
        intent = self._detect_intent(user_message)
        
        # Retrieve relevant resources
        relevant_resources = self._retrieve_resources(intent, user_message)
        
        # Generate response
        if use_ai and self._has_openai_key():
            response = self._generate_ai_response(user_message, intent, relevant_resources)
        else:
            response = self._generate_rule_based_response(user_message, intent, relevant_resources)
        
        # Save assistant response
        ChatMessage.objects.create(
            session=self.session,
            role='assistant',
            content=response,
            metadata={'intent': intent, 'resources_used': len(relevant_resources)}
        )
        
        return response
    
    def _detect_intent(self, message):
        """Enhanced intent detection with multiple keyword matching."""
        message_lower = message.lower()
        
        # Count matches for each intent
        intent_scores = {}
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return intent with highest score
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        
        return 'general'
    
    def _retrieve_resources(self, intent, user_message):
        """Retrieve relevant resources from database based on intent."""
        # Map intent to resource categories
        intent_to_category = {
            'waste_reduction': ['waste_reduction', 'storage_tips', 'preservation'],
            'nutrition': ['nutrition', 'cooking_tips'],
            'meal_planning': ['meal_planning', 'budget_tips', 'shopping'],
            'leftovers': ['cooking_tips', 'waste_reduction'],
            'sharing': ['sustainability', 'waste_reduction'],
            'environment': ['sustainability', 'waste_reduction'],
        }
        
        categories = intent_to_category.get(intent, ['waste_reduction', 'storage_tips'])
        
        # Search resources
        resources = Resource.objects.filter(
            category__in=categories
        ).filter(featured=True)[:3]
        
        # If no featured, get any matching resources
        if not resources.exists():
            resources = Resource.objects.filter(
                category__in=categories
            )[:3]
        
        return list(resources)
    
    def _generate_ai_response(self, user_message, intent, relevant_resources):
        """Generate AI response using OpenAI with enhanced prompt chaining."""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
            if not api_key:
                return self._generate_rule_based_response(user_message, intent, relevant_resources)
            
            client = openai.OpenAI(api_key=api_key)
            
            # Build enhanced system prompt with context
            context_str = self._format_context_for_ai()
            resources_str = self._format_resources_for_ai(relevant_resources)
            
            system_prompt = f"""{self.SYSTEM_PROMPT}

User Context:
{context_str}

Relevant Resources Available:
{resources_str}

Use this context to provide personalized, specific advice. Reference actual items from their inventory when relevant."""
            
            # Build messages with conversation history (prompt chaining)
            messages = [
                {'role': 'system', 'content': system_prompt},
            ]
            
            # Get conversation history (last 10 messages for context)
            recent_messages = ChatMessage.objects.filter(
                session=self.session
            ).order_by('-created_at')[:10]
            
            # Add conversation history in chronological order
            for msg in reversed(recent_messages):
                if msg.role in ['user', 'assistant']:
                    messages.append({
                        'role': msg.role,
                        'content': msg.content
                    })
            
            # Add current user message
            messages.append({'role': 'user', 'content': user_message})
            
            # Call OpenAI with enhanced parameters
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=400,  # Increased for more detailed responses
                top_p=0.9,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to rule-based
            return self._generate_rule_based_response(user_message, intent, relevant_resources)
    
    def _format_context_for_ai(self):
        """Format user context for AI prompt."""
        context = self.session.context
        lines = []
        
        # User profile
        profile = context.get('user_profile', {})
        lines.append(f"Household: {profile.get('household_size', 1)} people")
        lines.append(f"Diet: {profile.get('dietary_preferences', 'standard')}")
        lines.append(f"Budget: {profile.get('budget_range', 'medium')}")
        
        # Recent consumption
        recent = context.get('recent_consumption', [])
        if recent:
            lines.append(f"\nRecent items consumed:")
            for item in recent[:5]:
                lines.append(f"  - {item['item']} ({item['category']}) on {item['date']}")
        
        # Expiring items
        expiring = context.get('expiring_items', [])
        if expiring:
            lines.append(f"\nItems expiring soon:")
            for item in expiring[:5]:
                days = item.get('days_left', '?')
                lines.append(f"  - {item['item']} ({item['category']}) - {days} days left")
        
        # Waste summary
        waste = context.get('waste_summary', {})
        if waste.get('total_waste_grams', 0) > 0:
            lines.append(f"\nWeekly waste: {waste.get('total_waste_grams', 0):.0f}g (${waste.get('total_waste_cost', 0):.2f})")
        
        # Consumption patterns
        patterns = context.get('consumption_patterns', {})
        top_cats = patterns.get('top_categories', {})
        if top_cats:
            lines.append(f"\nMost consumed categories: {', '.join(top_cats.keys())}")
        
        return "\n".join(lines)
    
    def _format_resources_for_ai(self, resources):
        """Format resources for AI prompt."""
        if not resources:
            return "No specific resources available, but provide general advice."
        
        lines = []
        for resource in resources:
            lines.append(f"- {resource.title}: {resource.description[:100]}...")
            if resource.url:
                lines.append(f"  URL: {resource.url}")
        
        return "\n".join(lines) if lines else "No specific resources available."
    
    def _generate_rule_based_response(self, user_message, intent, relevant_resources):
        """Generate comprehensive rule-based response with resource integration."""
        message_lower = user_message.lower()
        context = self.session.context
        
        # Get tips from database
        tips = self.TIPS_DATABASE.get(intent, [])
        selected_tips = tips[:5] if tips else []
        
        response_parts = []
        
        if intent == 'waste_reduction':
            expiring = context.get('expiring_items', [])
            expiration_risks = context.get('expiration_risks', [])
            
            if expiring or expiration_risks:
                items_list = []
                if expiring:
                    items_list.extend([item['item'] for item in expiring[:3]])
                if expiration_risks:
                    items_list.extend([risk['item'] for risk in expiration_risks[:2]])
                
                unique_items = list(set(items_list))[:5]
                items_str = ", ".join([f'"{item}"' for item in unique_items])
                
                response_parts.append(f"I see you have items that need attention: {items_str}.")
                response_parts.append("\nHere's how to reduce waste:\n")
            else:
                response_parts.append("Great! You don't have items expiring soon. Here are tips to prevent waste:\n")
            
            for i, tip in enumerate(selected_tips, 1):
                response_parts.append(f"{i}. {tip}")
            
            waste_summary = context.get('waste_summary', {})
            if waste_summary.get('total_waste_grams', 0) > 0:
                response_parts.append(f"\nYour current weekly waste: {waste_summary.get('total_waste_grams', 0):.0f} grams (${waste_summary.get('total_waste_cost', 0):.2f}).")
                response_parts.append("Try to reduce this by using items before they expire!")
            
            # Add resource links
            if relevant_resources:
                response_parts.append("\n📚 Helpful Resources:")
                for resource in relevant_resources[:2]:
                    response_parts.append(f"• {resource.title}")
        
        elif intent == 'nutrition':
            diet_pref = context.get('user_profile', {}).get('dietary_preferences', 'standard')
            top_cats = context.get('consumption_patterns', {}).get('top_categories', {})
            
            response_parts.append(f"Based on your {diet_pref} diet preferences, here's nutrition guidance:\n")
            
            for i, tip in enumerate(selected_tips, 1):
                response_parts.append(f"{i}. {tip}")
            
            if top_cats:
                response_parts.append(f"\nI notice you consume: {', '.join(list(top_cats.keys())[:3])}.")
                response_parts.append("Aim for variety across all food groups for balanced nutrition!")
            
            imbalances = context.get('imbalances', [])
            if imbalances:
                response_parts.append("\n⚠️ Nutrition Note:")
                for imb in imbalances[:2]:
                    response_parts.append(f"• {imb.get('message', '')}")
        
        elif intent == 'meal_planning':
            budget = context.get('user_profile', {}).get('budget_range', 'medium')
            expiring = context.get('expiring_items', [])
            inventory_count = len(context.get('expiring_items', [])) + 5  # Estimate
            
            response_parts.append(f"Let's plan meals for your {budget} budget!\n")
            
            if expiring:
                items_str = ", ".join([item['item'] for item in expiring[:3]])
                response_parts.append(f"First, use these items: {items_str}")
                response_parts.append("")
            
            for i, tip in enumerate(selected_tips, 1):
                response_parts.append(f"{i}. {tip}")
            
            response_parts.append("\n💡 Tip: Check your inventory first, then plan meals around what you have!")
            response_parts.append("Would you like me to generate a specific meal plan? Use the Meal Optimizer feature!")
        
        elif intent == 'leftovers':
            recent = context.get('recent_consumption', [])
            
            response_parts.append("Creative leftover transformation ideas:\n")
            
            for i, tip in enumerate(selected_tips, 1):
                response_parts.append(f"{i}. {tip}")
            
            if recent:
                recent_items = [item['item'] for item in recent[:3]]
                response_parts.append(f"\nBased on your recent consumption ({', '.join(recent_items)}),")
                response_parts.append("you could transform these into new dishes!")
            
            response_parts.append("\n💡 What leftovers do you have? Tell me and I'll give you specific recipe ideas!")
        
        elif intent == 'sharing':
            location = context.get('user_profile', {}).get('location', 'your area')
            expiring = context.get('expiring_items', [])
            
            response_parts.append(f"Food sharing opportunities in {location}:\n")
            
            for i, tip in enumerate(selected_tips, 1):
                response_parts.append(f"{i}. {tip}")
            
            if expiring:
                items_str = ", ".join([item['item'] for item in expiring[:3]])
                response_parts.append(f"\nYou could share: {items_str}")
                response_parts.append("These items are still good but expiring soon - perfect for sharing!")
        
        elif intent == 'environment':
            waste_summary = context.get('waste_summary', {})
            
            response_parts.append("Your food choices impact the environment! Here's your impact:\n")
            
            waste_grams = waste_summary.get('total_waste_grams', 0)
            waste_cost = waste_summary.get('total_waste_cost', 0)
            
            if waste_grams > 0:
                response_parts.append(f"• Weekly waste: {waste_grams:.0f} grams")
                response_parts.append(f"• Estimated cost: ${waste_cost:.2f}")
                response_parts.append(f"• Environmental impact: This waste contributes to greenhouse gas emissions")
            else:
                response_parts.append("• Great job! Your waste is minimal.")
            
            response_parts.append("\nWays to reduce environmental impact:\n")
            
            for i, tip in enumerate(selected_tips, 1):
                response_parts.append(f"{i}. {tip}")
            
            response_parts.append("\n🌍 Every small change makes a big difference for our planet!")
        
        else:
            response_parts.append("Hi! I'm NourishBot, your food management assistant. I can help with:\n")
            response_parts.append("• 🗑️ Reducing food waste")
            response_parts.append("• 🥗 Nutrition and healthy eating")
            response_parts.append("• 📋 Meal planning and budgeting")
            response_parts.append("• 🍳 Creative leftover recipes")
            response_parts.append("• 🤝 Food sharing opportunities")
            response_parts.append("• 🌍 Environmental impact")
            response_parts.append("\nWhat would you like to know? Just ask me anything!")
        
        # Add resource recommendations
        if relevant_resources and intent != 'general':
            response_parts.append("\n📚 Recommended Resources:")
            for resource in relevant_resources[:2]:
                response_parts.append(f"• {resource.title} - {resource.description[:80]}...")
        
        return "\n".join(response_parts)
    
    def _has_openai_key(self):
        """Check if OpenAI API key is available."""
        api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        return api_key is not None
    
    def get_conversation_history(self, limit=20):
        """Get conversation history for this session."""
        return ChatMessage.objects.filter(
            session=self.session
        ).order_by('created_at')[:limit]
    
    def get_session_summary(self):
        """Get summary of the current session."""
        messages = ChatMessage.objects.filter(session=self.session)
        user_messages = messages.filter(role='user').count()
        assistant_messages = messages.filter(role='assistant').count()
        
        # Get unique intents discussed
        intents = set()
        for msg in messages.filter(role='assistant'):
            if msg.metadata and 'intent' in msg.metadata:
                intents.add(msg.metadata['intent'])
        
        return {
            'total_messages': messages.count(),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'topics_discussed': list(intents),
            'session_created': self.session.created_at,
        }
