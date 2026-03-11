from crewai import Agent
from config.settings import settings
from tools.travel_tools import FlightSearchTool, HotelSearchTool, TravelInfoTool, WeatherTool

class TravelAdvisorAgent:
    def __init__(self):
        self.agent = Agent(
            role="Travel Advisor",
            goal="Provide personalized travel recommendations, create comprehensive trip itineraries, and ensure customer satisfaction",
            backstory="""You are an experienced travel advisor with extensive knowledge of destinations worldwide.
            Your expertise includes:
            - Creating personalized travel itineraries based on customer preferences and budget
            - Recommending the best flights, hotels, and activities for any destination
            - Providing insider tips and local recommendations
            - Adapting recommendations based on weather, season, and current events
            - Balancing customer desires with practical considerations like budget and time constraints
            - Offering alternative options when preferred choices aren't available
            - Ensuring all recommendations align with safety and quality standards""",
            verbose=settings.verbose,
            allow_delegation=True,
            temperature=settings.travel_advisor_temperature,
            tools=[
                FlightSearchTool(),
                HotelSearchTool(),
                TravelInfoTool(),
                WeatherTool()
            ]
        )

    def get_agent(self):
        return self.agent

    def create_trip_recommendation(self, destination: str, duration: int, budget: str, preferences: str) -> str:
        """Create a comprehensive trip recommendation"""
        return f"""Based on your request for {destination}:

**Trip Overview:**
- Destination: {destination}
- Duration: {duration} days
- Budget: {budget}
- Preferences: {preferences}

I'll create a personalized recommendation that includes:
1. Flight options analysis
2. Hotel recommendations within budget
3. Daily itinerary suggestions
4. Local transportation tips
5. Restaurant and activity recommendations
6. Weather considerations and packing tips

Let me gather the most current information and create your perfect itinerary!"""

    def analyze_options(self, options_data: str) -> str:
        """Analyze and compare different travel options"""
        return """When analyzing travel options, I consider:

**Flight Analysis:**
- Price vs. convenience vs. duration
- Airline reputation and amenities
- Layover times and total travel time
- Flexibility for changes/cancellations

**Hotel Analysis:**
- Location convenience and safety
- Value for money (price vs. amenities vs. reviews)
- Guest ratings and recent feedback
- Cancellation policies

**Overall Trip Value:**
- Total cost breakdown
- Time efficiency
- Comfort and convenience factors
- Unique experiences offered

I'll present you with the top 2-3 recommendations with clear pros/cons for each."""

    def provide_destination_insights(self, destination: str) -> str:
        """Provide detailed destination insights and recommendations"""
        return f"""For {destination}, here are my expert insights:

**Best Time to Visit:**
- Weather patterns and seasonal considerations
- Peak vs. off-season pricing and crowds
- Local events and festivals during your dates

**Hidden Gems & Local Tips:**
- Lesser-known attractions that locals love
- Authentic dining experiences beyond tourist traps
- Transportation hacks to save time and money
- Cultural etiquette and customs to be aware of

**Practical Considerations:**
- Current safety situation and travel advisories
- Visa requirements and entry procedures
- Currency, payment methods, and ATM availability
- Health and vaccination recommendations

**Budget Optimization:**
- Cost-saving strategies without sacrificing quality
- Free/cheap activities and attractions
- Best value accommodations and dining options

I'll tailor these insights to your specific travel dates and preferences!"""

    def suggest_itinerary(self, destination: str, days: int) -> str:
        """Suggest a day-by-day itinerary"""
        return f"""Here's a suggested {days}-day itinerary for {destination}:

**Day-by-Day Breakdown:**
- **Day 1:** Arrival and orientation - settle in, explore nearby
- **Day 2:** Major attractions and landmarks
- **Day 3:** Cultural experiences and local markets
- **Day 4:** Adventure activities or day trips
- **Day 5:** Shopping, relaxation, and departure prep

**Flexible Elements:**
- Weather-dependent activities with alternatives
- Rest time built into the schedule
- Options for different energy levels
- Backup plans for closures or crowds

**Customization Notes:**
- This is a template that can be adjusted based on your interests
- Opening hours and seasonal availability considered
- Transportation between activities planned
- Meal times and local cuisine integrated

I can modify this itinerary based on your specific preferences and any constraints!"""