# SDG Impact Scoring Engine - Implementation

## ✅ Implementation Status: COMPLETE

The SDG Impact Scoring Engine is fully implemented with AI-powered insights, weekly progress tracking, and specific actionable steps.

## 🎯 Core Requirements Met

### 1. **AI-Powered Evaluation** ✅
- Uses OpenAI GPT-3.5 for generating insights (with rule-based fallback)
- Evaluates user progress in waste reduction and nutrition improvement
- Analyzes consumption patterns, waste data, and sustainability metrics
- Provides context-aware insights based on actual user data

### 2. **Personal SDG Score (0-100)** ✅
- **Overall Score**: Weighted combination of three components
  - Waste Reduction: 40% weight
  - Nutrition: 35% weight
  - Sustainability: 25% weight
- **Component Scores**: Individual scores for each area
- **Real-time Calculation**: Updates based on current week's data

### 3. **Weekly Insights on Improvements** ✅
- **AI-Generated Insights**: Uses OpenAI for personalized insights
- **Rule-Based Fallback**: Comprehensive insights when AI unavailable
- **Progress Tracking**: Compares current week to previous week
- **Trend Analysis**: Shows improvement/decline patterns
- **Category-Specific**: Insights for waste, nutrition, and sustainability

### 4. **Actionable Next Steps** ✅
- **Specific Recommendations**: Item-specific actions (e.g., "Use expiring items: Apple, Banana")
- **Improvement Estimates**: Shows expected point improvements (e.g., "10-15 points")
- **Boost Percentages**: Specific percentage improvements (e.g., "Focus on veggies to boost score by 10%")
- **Priority-Based**: High/Medium priority categorization
- **Category-Targeted**: Steps for waste, nutrition, and sustainability

## 📊 Scoring Components

### Waste Reduction Score (0-100)
**Calculation Factors:**
- Weekly waste amount (compared to community average)
- Expired items count
- Expiring items usage
- Improvement trend (week-over-week)

**Scoring Logic:**
- 0g waste = 100 points
- ≤30% of average = 95 points
- ≤50% of average = 85 points
- ≤70% of average = 75 points
- ≤100% of average = 60 points
- >100% of average = 30-45 points

**Bonuses:**
- Using expiring items: +2 points per item (max +10)
- Improvement trend: +5 to +15 points
- Penalties: -5 points per expired item (max -25)

### Nutrition Score (0-100)
**Calculation Factors:**
- Category imbalances (over/under-consumption)
- Nutrient gaps
- Dietary variety (number of categories)
- Vegetable/fruit consumption
- Regular consumption frequency

**Scoring Logic:**
- Base score: 100 points
- Under-consumption penalties: -6 to -20 points
- Over-consumption penalties: -5 to -10 points
- Nutrient gap penalties: -3 to -25 points
- Variety bonuses: +2 to +15 points
- Regular consumption bonus: +5 to +10 points
- Vegetable/fruit bonus: +5 to +10 points

### Sustainability Score (0-100)
**Calculation Factors:**
- Waste levels (low waste = sustainable)
- Expiring items usage
- Regular tracking (awareness)
- Meal planning usage

**Scoring Logic:**
- Base score: 60 points
- Low waste bonuses: +5 to +20 points
- Expiring items usage: +5 to +15 points
- Regular tracking: +5 to +10 points

## 🤖 AI-Powered Features

### AI Insights Generation
- **OpenAI Integration**: Uses GPT-3.5-turbo for insights
- **Context-Aware**: Includes user's actual data (waste, consumption, patterns)
- **Structured Output**: JSON format with type, category, message, impact
- **Fallback**: Rule-based insights when AI unavailable

### AI Prompt Structure
```
Analyze user's SDG impact scores and provide 3-5 specific insights:
- Current scores (overall, waste, nutrition, sustainability)
- Context (waste amounts, expiring items, consumption patterns)
- Previous week comparison
- Specific, actionable observations
```

## 📈 Weekly Insights

### Features
- **4-Week Trends**: Shows progress over last 4 weeks
- **Visual Charts**: Chart.js line chart for trends
- **Score Comparison**: Week-over-week changes
- **Component Tracking**: Individual scores for each component

### Data Points
- Overall score trend
- Waste reduction trend
- Nutrition trend
- Sustainability trend

## 🎯 Actionable Steps

### Step Structure
Each actionable step includes:
- **Action**: Specific, actionable instruction
- **Priority**: High or Medium
- **Category**: Waste, Nutrition, or Sustainability
- **Expected Improvement**: Point estimate (e.g., "10-15 points")
- **Boost Percentage**: Percentage improvement (e.g., "10-15%")
- **Specific Flag**: Whether step is specific to user's data

### Example Steps

**Waste Reduction:**
- "Use expiring items first: Apple, Banana, Milk" - 12-18 points
- "Plan meals around your inventory to reduce waste" - 10-15 points
- "Check expiration dates regularly and use FIFO" - 8-12 points

**Nutrition:**
- "Focus on adding more vegetables to your meals" - 10-15 points (10-15% boost)
- "Increase Vitamin C intake - you have a 45% gap" - 13 points (13% boost)
- "Add more variety to your diet - aim for 5+ categories" - 8-12 points

**Sustainability:**
- "Log your food consumption daily" - 5-10 points
- "Use the Meal Optimizer to plan sustainable meals" - 8-12 points

## 📊 UI Features

### Score Display
- **Large Score Cards**: Overall, Waste, Nutrition, Sustainability
- **Progress Bars**: Visual representation of scores
- **Improvement Badges**: Week-over-week change indicators
- **Color-Coded**: Different colors for each component

### Insights Section
- **AI-Powered Badge**: Shows if AI is enabled
- **Categorized Insights**: Grouped by type (success, warning, info)
- **Impact Indicators**: High/Medium/Low impact badges
- **Improvement Potential**: Shows potential improvements

### Actionable Steps Section
- **Priority-Based Sorting**: High priority first
- **Visual Cards**: Color-coded borders (red for high, yellow for medium)
- **Category Badges**: Color-coded by category
- **Improvement Badges**: Shows expected points and percentages
- **Specific Indicators**: Badge for user-specific steps

### Weekly Progress Chart
- **Line Chart**: Chart.js visualization
- **4 Datasets**: Overall, Waste, Nutrition, Sustainability
- **Trend Lines**: Shows progress over 4 weeks
- **Interactive**: Hover for details

### Historical Scores Table
- **Last 12 Weeks**: Historical data table
- **All Components**: Shows all score components
- **Date Sorting**: Most recent first

## 🔧 Technical Implementation

### Main Files
- **`ai_analytics/sdg_scorer.py`**: Core scoring engine (700+ lines)
  - `SDGImpactScorer` class
  - Score calculation methods
  - AI insights generation
  - Actionable steps generation
  - Weekly insights tracking

- **`ai_analytics/views.py`**: View handler
  - `sdg_impact()` view
  - AI/rule-based mode selection
  - Data preparation for templates

- **`ai_analytics/templates/ai_analytics/sdg_impact.html`**: UI template
  - Score display cards
  - Insights section
  - Actionable steps
  - Weekly progress chart
  - Historical scores table

- **`ai_analytics/models.py`**: Database models
  - `SDGImpactScore`: Stores weekly scores

### Key Methods

**`calculate_sdg_score(week_start_date, use_ai)`**
- Calculates all component scores
- Generates AI or rule-based insights
- Creates actionable steps
- Returns comprehensive score data

**`_generate_ai_insights(...)`**
- Uses OpenAI API for insights
- Includes user context
- Returns structured insights

**`_generate_actionable_steps(...)`**
- Analyzes user data for specific steps
- Calculates improvement estimates
- Prioritizes steps
- Returns sorted list of steps

**`get_weekly_insights(weeks)`**
- Calculates scores for multiple weeks
- Returns trend data
- Used for chart visualization

## 📝 Usage Examples

### Example 1: Low Waste Score
**User Score**: Waste Reduction = 45/100
**Insights**: 
- "Your waste reduction score is 45.0/100. You're wasting 450g per week ($5.20). Focus on using items before they expire."
- Impact: High
- Potential: 15-20 points

**Actionable Steps**:
1. "Use expiring items first: Apple, Banana" - 12-18 points (High Priority)
2. "Plan meals around your inventory" - 10-15 points (High Priority)
3. "Check expiration dates regularly" - 8-12 points (Medium Priority)

### Example 2: Nutrition Gap
**User Score**: Nutrition = 65/100
**Insights**:
- "Your nutrition score is 65.1/100. You're under-consuming: vegetables, fruits. Adding these can boost your score significantly."
- Impact: High
- Potential: 10-15 points

**Actionable Steps**:
1. "Focus on adding more vegetables to your meals" - 10-15 points, 10-15% boost (High Priority)
2. "Increase Vitamin C intake - you have a 45% gap" - 13 points, 13% boost (High Priority)
3. "Add more variety - aim for 5+ categories" - 8-12 points (Medium Priority)

### Example 3: Improvement Tracking
**Current Week**: Overall = 75/100
**Previous Week**: Overall = 68/100
**Change**: +7 points

**Insight**:
- "Great progress! Your score improved by 7.0 points this week."
- Type: Success
- Impact: Positive

## 🚀 Access

**URL**: `/ai/sdg-impact/`

**Features**:
- Real-time score calculation
- AI-powered insights (optional)
- Weekly progress tracking
- Specific actionable steps
- Historical score trends
- Interactive charts

## 📊 Testing Results

✅ Score calculation: Working for all components
✅ AI insights: Generated with OpenAI (with fallback)
✅ Actionable steps: Specific with improvement estimates
✅ Weekly insights: 4-week trend tracking
✅ Historical scores: 12-week history
✅ UI components: All displaying correctly

## 🎉 Status

**SDG Impact Scoring Engine is fully implemented and ready to use!**

All requirements met:
- ✅ AI-powered evaluation
- ✅ Personal SDG Score (0-100)
- ✅ Weekly insights on improvements
- ✅ Actionable next steps with specific improvements (e.g., "Focus on veggies to boost score by 10%")

