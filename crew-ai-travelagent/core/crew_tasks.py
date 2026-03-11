from crewai import Task
from agents.customer_service_agent import CustomerServiceAgent
from agents.travel_advisor_agent import TravelAdvisorAgent
from agents.booking_agent import BookingAgent
from typing import Dict, Any, List

class TravelBookingTasks:
    def __init__(self):
        self.customer_agent = CustomerServiceAgent()
        self.advisor_agent = TravelAdvisorAgent()
        self.booking_agent = BookingAgent()

    def create_initial_greeting_task(self, customer_query: str) -> Task:
        """Task for initial customer greeting and understanding their needs"""
        return Task(
            description=f"""Analyze the customer's initial query and provide a friendly, professional greeting.

Customer Query: "{customer_query}"

Your tasks:
1. Greet the customer warmly and acknowledge their inquiry
2. Understand what they're looking for (flight booking, hotel, trip planning, etc.)
3. Gather any missing essential information
4. Determine if this needs to be routed to a travel advisor or can be handled directly
5. Provide initial helpful information or next steps

Be conversational, helpful, and ensure the customer feels valued.""",
            agent=self.customer_agent.get_agent(),
            expected_output="A friendly greeting with understanding of customer needs and clear next steps."
        )

    def create_trip_planning_task(self, customer_requirements: Dict[str, Any]) -> Task:
        """Task for comprehensive trip planning and recommendations"""
        return Task(
            description=f"""Create a comprehensive trip plan based on customer requirements.

Customer Requirements:
{self._format_requirements(customer_requirements)}

Your tasks:
1. Analyze the customer's preferences, budget, and constraints
2. Research and recommend suitable destinations if not specified
3. Find optimal flight options within budget
4. Recommend hotels/accommodations that match preferences
5. Create a day-by-day itinerary with activities and dining
6. Consider weather, seasonal factors, and current events
7. Provide total cost breakdown and value assessment
8. Suggest alternatives and backup options

Focus on creating a personalized, memorable travel experience.""",
            agent=self.advisor_agent.get_agent(),
            expected_output="A detailed trip itinerary with recommendations, cost breakdown, and booking options."
        )

    def create_flight_search_task(self, search_criteria: Dict[str, Any]) -> Task:
        """Task for searching and analyzing flight options"""
        return Task(
            description=f"""Search for and analyze flight options based on specific criteria.

Search Criteria:
{self._format_search_criteria(search_criteria)}

Your tasks:
1. Search for flights matching the exact criteria
2. Compare airlines, prices, and flight times
3. Consider layovers, total travel time, and convenience
4. Check for flexibility in dates if requested options are expensive
5. Analyze airline ratings and recent performance
6. Provide 3-5 best options with clear pros/cons
7. Include booking links and next steps

Be thorough but concise in your analysis.""",
            agent=self.advisor_agent.get_agent(),
            expected_output="Detailed flight options analysis with recommendations and booking guidance."
        )

    def create_hotel_search_task(self, search_criteria: Dict[str, Any]) -> Task:
        """Task for searching and recommending hotels"""
        return Task(
            description=f"""Find and recommend hotels based on customer preferences.

Search Criteria:
{self._format_search_criteria(search_criteria)}

Your tasks:
1. Search hotels in the specified location and date range
2. Filter by budget, amenities, and customer preferences
3. Analyze guest reviews and ratings
4. Consider location convenience (airport, city center, attractions)
5. Check cancellation policies and flexibility
6. Provide 3-4 top recommendations with photos and details
7. Include total costs and any additional fees

Focus on value for money and guest satisfaction.""",
            agent=self.advisor_agent.get_agent(),
            expected_output="Curated hotel recommendations with detailed analysis and booking options."
        )

    def create_booking_task(self, booking_details: Dict[str, Any]) -> Task:
        """Task for processing actual bookings"""
        return Task(
            description=f"""Process a travel booking with complete accuracy and verification.

Booking Details:
{self._format_booking_details(booking_details)}

Your tasks:
1. Verify all customer and travel information
2. Double-check availability and pricing
3. Process the booking through appropriate channels
4. Generate confirmation numbers and documentation
5. Send booking confirmation to customer
6. Provide important travel information and next steps
7. Note any special requirements or follow-up needed

Accuracy is critical - triple-check all details before confirming.""",
            agent=self.booking_agent.get_agent(),
            expected_output="Confirmed booking with all details, confirmation numbers, and follow-up instructions."
        )

    def create_customer_followup_task(self, booking_info: Dict[str, Any]) -> Task:
        """Task for following up on customer bookings and satisfaction"""
        return Task(
            description=f"""Follow up with customer to ensure satisfaction and provide additional support.

Booking Information:
{self._format_booking_info(booking_info)}

Your tasks:
1. Confirm customer received booking confirmation
2. Ask about satisfaction with recommendations and process
3. Provide additional travel tips and information
4. Check if customer needs any modifications or additions
5. Offer travel insurance or other services
6. Provide emergency contact information
7. Schedule any necessary follow-up calls

Ensure the customer feels completely supported throughout their journey.""",
            agent=self.customer_agent.get_agent(),
            expected_output="Customer satisfaction confirmation and any additional support provided."
        )

    def _format_requirements(self, requirements: Dict[str, Any]) -> str:
        """Format customer requirements for task descriptions"""
        formatted = []
        for key, value in requirements.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)

    def _format_search_criteria(self, criteria: Dict[str, Any]) -> str:
        """Format search criteria for task descriptions"""
        formatted = []
        for key, value in criteria.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)

    def _format_booking_details(self, details: Dict[str, Any]) -> str:
        """Format booking details for task descriptions"""
        formatted = []
        for key, value in details.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)

    def _format_booking_info(self, info: Dict[str, Any]) -> str:
        """Format booking information for task descriptions"""
        formatted = []
        for key, value in info.items():
            formatted.append(f"- {key.replace('_', ' ').title()}: {value}")
        return "\n".join(formatted)

    def get_all_tasks_for_workflow(self, workflow_type: str, data: Dict[str, Any]) -> List[Task]:
        """Get the appropriate sequence of tasks for different workflow types"""
        if workflow_type == "new_customer_inquiry":
            return [
                self.create_initial_greeting_task(data.get("query", "")),
                self.create_trip_planning_task(data.get("requirements", {}))
            ]
        elif workflow_type == "flight_booking":
            return [
                self.create_flight_search_task(data.get("search_criteria", {})),
                self.create_booking_task(data.get("booking_details", {})),
                self.create_customer_followup_task(data.get("booking_info", {}))
            ]
        elif workflow_type == "hotel_booking":
            return [
                self.create_hotel_search_task(data.get("search_criteria", {})),
                self.create_booking_task(data.get("booking_details", {})),
                self.create_customer_followup_task(data.get("booking_info", {}))
            ]
        elif workflow_type == "complete_trip":
            return [
                self.create_trip_planning_task(data.get("requirements", {})),
                self.create_flight_search_task(data.get("flight_criteria", {})),
                self.create_hotel_search_task(data.get("hotel_criteria", {})),
                self.create_booking_task(data.get("booking_details", {})),
                self.create_customer_followup_task(data.get("booking_info", {}))
            ]
        else:
            return [self.create_initial_greeting_task(data.get("query", ""))]