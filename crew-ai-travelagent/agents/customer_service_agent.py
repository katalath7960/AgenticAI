from crewai import Agent
from crewai_tools import SerperDevTool
from config.settings import settings
from tools.travel_tools import TravelInfoTool, WeatherTool

class CustomerServiceAgent:
    def __init__(self):
        self.agent = Agent(
            role="Customer Service Representative",
            goal="Provide excellent customer service, understand customer needs, and route them to appropriate specialists",
            backstory="""You are a friendly and professional customer service representative for a travel booking platform.
            Your primary responsibilities include:
            - Greeting customers warmly and understanding their travel needs
            - Gathering essential information about their trip requirements
            - Providing basic travel information and answering common questions
            - Routing complex inquiries to travel advisors or booking specialists
            - Maintaining a helpful and patient demeanor throughout interactions
            - Ensuring customer satisfaction and smooth communication flow""",
            verbose=settings.verbose,
            allow_delegation=True,
            temperature=settings.customer_service_temperature,
            tools=[
                TravelInfoTool(),
                WeatherTool()
            ]
        )

    def get_agent(self):
        return self.agent

    def handle_customer_inquiry(self, inquiry: str) -> str:
        """Handle initial customer inquiry and determine next steps"""
        return f"""Based on the customer's inquiry: "{inquiry}"

I need to:
1. Understand what the customer is asking for
2. Gather any missing information
3. Provide initial assistance or route to specialists
4. Ensure clear communication throughout the process

Let me analyze this request and provide the most helpful response possible."""

    def gather_trip_requirements(self) -> str:
        """Prompt for essential trip planning information"""
        return """To help you plan the perfect trip, I'll need some key information:

**Essential Details:**
- Travel dates (departure and return)
- Destination(s) you're interested in
- Number of travelers
- Budget range
- Type of trip (business/leisure/family/adventure)
- Preferred accommodation type
- Any special requirements (accessibility, dietary, etc.)

**Optional but helpful:**
- Departure city/airport
- Preferred airlines or hotel chains
- Specific activities or attractions you're interested in

Please provide as much detail as you can, and I'll connect you with our travel experts!"""

    def provide_basic_info(self, destination: str) -> str:
        """Provide basic information about a destination"""
        return f"""I'd be happy to share some basic information about {destination}!

Using our travel information tools, I can provide:
- General destination overview
- Visa requirements
- Currency and language information
- Best time to visit
- Popular attractions

Would you like me to look up specific information about {destination}?"""