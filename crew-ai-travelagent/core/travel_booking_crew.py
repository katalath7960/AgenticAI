from crewai import Crew
from agents.customer_service_agent import CustomerServiceAgent
from agents.travel_advisor_agent import TravelAdvisorAgent
from agents.booking_agent import BookingAgent
from core.crew_tasks import TravelBookingTasks
from config.settings import settings
from typing import Dict, Any, List, Optional
import json

class TravelBookingCrew:
    def __init__(self):
        self.customer_agent = CustomerServiceAgent()
        self.advisor_agent = TravelAdvisorAgent()
        self.booking_agent = BookingAgent()
        self.tasks = TravelBookingTasks()

        # Initialize the crew with all agents
        self.crew = Crew(
            agents=[
                self.customer_agent.get_agent(),
                self.advisor_agent.get_agent(),
                self.booking_agent.get_agent()
            ],
            tasks=[],  # Tasks will be added dynamically
            verbose=settings.verbose,
            max_iterations=settings.max_iterations
        )

    def handle_customer_inquiry(self, customer_query: str) -> Dict[str, Any]:
        """Handle a new customer inquiry and route appropriately"""
        print(f"\n🤖 Processing customer inquiry: '{customer_query}'")

        # Create initial greeting task
        initial_task = self.tasks.create_initial_greeting_task(customer_query)

        # Add task to crew and run
        self.crew.tasks = [initial_task]
        result = self.crew.kickoff()

        return {
            "response_type": "initial_greeting",
            "customer_query": customer_query,
            "response": str(result),
            "next_steps": self._determine_next_steps(customer_query)
        }

    def plan_complete_trip(self, trip_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Plan a complete trip with flights, hotels, and itinerary"""
        print("🗺️ Planning complete trip...")
        print(f"Trip Requirements: {json.dumps(trip_requirements, indent=2)}")

        # Create comprehensive trip planning tasks
        tasks = self.tasks.get_all_tasks_for_workflow("complete_trip", {
            "requirements": trip_requirements,
            "flight_criteria": {
                "origin": trip_requirements.get("origin", "New York"),
                "destination": trip_requirements.get("destination", "Paris"),
                "departure_date": trip_requirements.get("departure_date", "2024-06-15"),
                "return_date": trip_requirements.get("return_date", "2024-06-22"),
                "passengers": trip_requirements.get("passengers", 2)
            },
            "hotel_criteria": {
                "destination": trip_requirements.get("destination", "Paris"),
                "check_in_date": trip_requirements.get("departure_date", "2024-06-15"),
                "check_out_date": trip_requirements.get("return_date", "2024-06-22"),
                "guests": trip_requirements.get("passengers", 2),
                "budget_max": trip_requirements.get("budget", 5000) * 0.3  # 30% for accommodation
            },
            "booking_details": {
                "type": "complete_trip",
                "customer_info": trip_requirements.get("customer_info", {}),
                "total_cost": trip_requirements.get("budget", 0)
            },
            "booking_info": {
                "customer_name": trip_requirements.get("customer_info", {}).get("name", "Valued Customer"),
                "trip_type": "complete_package"
            }
        })

        # Execute tasks sequentially
        results = []
        for i, task in enumerate(tasks):
            print(f"\n📋 Executing task {i+1}/{len(tasks)}: {task.description[:50]}...")
            self.crew.tasks = [task]
            result = self.crew.kickoff()
            results.append(str(result))

        return {
            "response_type": "complete_trip_plan",
            "trip_requirements": trip_requirements,
            "task_results": results,
            "final_itinerary": results[-1] if results else "No results generated"
        }

    def search_flights(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search for and recommend flights"""
        print("✈️ Searching for flights...")
        print(f"Search Criteria: {json.dumps(search_criteria, indent=2)}")

        tasks = [
            self.tasks.create_flight_search_task(search_criteria),
            self.tasks.create_booking_task({
                "type": "flight_only",
                "customer_info": search_criteria.get("customer_info", {}),
                "details": search_criteria
            })
        ]

        results = []
        for task in tasks:
            self.crew.tasks = [task]
            result = self.crew.kickoff()
            results.append(str(result))

        return {
            "response_type": "flight_search",
            "search_criteria": search_criteria,
            "flight_options": results[0],
            "booking_options": results[1]
        }

    def search_hotels(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Search for and recommend hotels"""
        print("🏨 Searching for hotels...")     
        print(f"Search Criteria: {json.dumps(search_criteria, indent=2)}")

        tasks = [
            self.tasks.create_hotel_search_task(search_criteria),
            self.tasks.create_booking_task({
                "type": "hotel_only",
                "customer_info": search_criteria.get("customer_info", {}),
                "details": search_criteria
            })
        ]

        results = []
        for task in tasks:
            self.crew.tasks = [task]
            result = self.crew.kickoff()
            results.append(str(result))

        return {
            "response_type": "hotel_search",
            "search_criteria": search_criteria,
            "hotel_options": results[0],
            "booking_options": results[1]
        }

    def process_booking(self, booking_details: Dict[str, Any]) -> Dict[str, Any]:
        """Process a booking request"""
        print("📝 Processing booking...")
        print(f"Booking Details: {json.dumps(booking_details, indent=2)}")

        booking_task = self.tasks.create_booking_task(booking_details)
        followup_task = self.tasks.create_customer_followup_task({
            "booking_id": "TEMP_" + str(hash(str(booking_details))),
            "customer_name": booking_details.get("customer_info", {}).get("name", "Customer"),
            "booking_type": booking_details.get("type", "travel")
        })

        results = []
        for task in [booking_task, followup_task]:
            self.crew.tasks = [task]
            result = self.crew.kickoff()
            results.append(str(result))

        return {
            "response_type": "booking_processed",
            "booking_details": booking_details,
            "confirmation": results[0],
            "followup": results[1]
        }

    def _determine_next_steps(self, customer_query: str) -> List[str]:
        """Determine appropriate next steps based on customer query"""
        query_lower = customer_query.lower()

        next_steps = []

        if any(word in query_lower for word in ["book", "reserve", "purchase"]):
            next_steps.append("proceed_to_booking")
        elif any(word in query_lower for word in ["plan", "itinerary", "recommend"]):
            next_steps.append("create_trip_plan")
        elif any(word in query_lower for word in ["flight", "fly", "airline"]):
            next_steps.append("search_flights")
        elif any(word in query_lower for word in ["hotel", "stay", "accommodation"]):
            next_steps.append("search_hotels")
        elif any(word in query_lower for word in ["info", "information", "about"]):
            next_steps.append("provide_information")
        else:
            next_steps.append("gather_more_details")

        return next_steps

    def get_available_workflows(self) -> Dict[str, str]:
        """Get descriptions of available workflows"""
        return {
            "customer_inquiry": "Handle general customer inquiries and route to appropriate services",
            "complete_trip": "Plan a complete trip with flights, hotels, and itinerary",
            "flight_search": "Search for and book flights",
            "hotel_search": "Search for and book hotels",
            "booking": "Process booking requests",
            "followup": "Follow up on existing bookings"
        }

    def run_interactive_session(self):
        """Run an interactive session for testing the crew system"""
        print("🌟 Welcome to the Travel Booking Crew AI System!")
        print("=" * 60)

        workflows = self.get_available_workflows()
        print("\nAvailable Workflows:")
        for key, description in workflows.items():
            print(f"  • {key}: {description}")

        while True:
            print("\n" + "-" * 60)
            workflow = input("\nChoose a workflow (or 'quit' to exit): ").strip().lower()

            if workflow == "quit":
                print("👋 Thank you for using Travel Booking Crew AI!")
                break

            if workflow not in workflows:
                print(f"❌ Invalid workflow. Available: {', '.join(workflows.keys())}")
                continue

            # Handle different workflows
            if workflow == "customer_inquiry":
                query = input("Enter customer inquiry: ")
                result = self.handle_customer_inquiry(query)
                print(f"\n📝 Response: {result['response']}")

            elif workflow == "complete_trip":
                print("Enter trip requirements:")
                destination = input("Destination: ")
                departure_date = input("Departure date (YYYY-MM-DD): ")
                return_date = input("Return date (YYYY-MM-DD): ")
                passengers = int(input("Number of passengers: "))
                budget = float(input("Budget: "))

                requirements = {
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "passengers": passengers,
                    "budget": budget,
                    "customer_info": {"name": "Test Customer"}
                }

                result = self.plan_complete_trip(requirements)
                print(f"\n🗺️ Trip Plan: {result['final_itinerary']}")

            elif workflow == "flight_search":
                print("Enter flight search criteria:")
                origin = input("Origin: ")
                destination = input("Destination: ")
                departure_date = input("Departure date (YYYY-MM-DD): ")

                criteria = {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "passengers": 1
                }

                result = self.search_flights(criteria)
                print(f"\n✈️ Flight Options: {result['flight_options']}")

            elif workflow == "hotel_search":
                print("Enter hotel search criteria:")
                destination = input("Destination: ")
                check_in = input("Check-in date (YYYY-MM-DD): ")
                check_out = input("Check-out date (YYYY-MM-DD): ")

                criteria = {
                    "destination": destination,
                    "check_in_date": check_in,
                    "check_out_date": check_out,
                    "guests": 1
                }

                result = self.search_hotels(criteria)
                print(f"\n🏨 Hotel Options: {result['hotel_options']}")

            elif workflow == "booking":
                print("Enter booking details:")
                booking_type = input("Booking type (flight/hotel/trip): ")
                customer_name = input("Customer name: ")

                details = {
                    "type": booking_type,
                    "customer_info": {"name": customer_name},
                    "details": {"destination": "Test Destination"}
                }

                result = self.process_booking(details)
                print(f"\n📋 Booking Confirmation: {result['confirmation']}")
