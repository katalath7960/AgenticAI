from crewai.tools import BaseTool
from typing import Type, Optional, Dict, List, Any
import requests
import json
from datetime import datetime, timedelta
from config.settings import settings

class FlightSearchTool(BaseTool):
    name: str = "Flight Search Tool"
    description: str = "Search for available flights based on origin, destination, dates, and passenger count"

    def _run(self, origin: str, destination: str, departure_date: str,
             return_date: Optional[str] = None, passengers: int = 1) -> str:
        """Search for flights between two cities"""
        try:
            # Mock flight search data
            flights = [
                {
                    "flight_number": "AA101",
                    "airline": "American Airlines",
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_time": f"{departure_date}T08:00:00",
                    "arrival_time": f"{departure_date}T12:00:00",
                    "duration": "4h 0m",
                    "price": 299.99,
                    "seats_available": 45
                },
                {
                    "flight_number": "UA202",
                    "airline": "United Airlines",
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_time": f"{departure_date}T14:30:00",
                    "arrival_time": f"{departure_date}T18:45:00",
                    "duration": "4h 15m",
                    "price": 349.99,
                    "seats_available": 23
                },
                {
                    "flight_number": "DL303",
                    "airline": "Delta Airlines",
                    "origin": origin.upper(),
                    "destination": destination.upper(),
                    "departure_time": f"{departure_date}T19:15:00",
                    "arrival_time": f"{departure_date}T23:30:00",
                    "duration": "4h 15m",
                    "price": 279.99,
                    "seats_available": 67
                }
            ]

            if return_date:
                # Add return flights
                return_flights = [
                    {
                        "flight_number": "AA102",
                        "airline": "American Airlines",
                        "origin": destination.upper(),
                        "destination": origin.upper(),
                        "departure_time": f"{return_date}T10:00:00",
                        "arrival_time": f"{return_date}T14:00:00",
                        "duration": "4h 0m",
                        "price": 299.99,
                        "seats_available": 38
                    }
                ]
                flights.extend(return_flights)

            return json.dumps({
                "search_criteria": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": departure_date,
                    "return_date": return_date,
                    "passengers": passengers
                },
                "flights": flights,
                "total_results": len(flights)
            }, indent=2)

        except Exception as e:
            return f"Error searching flights: {str(e)}"

class HotelSearchTool(BaseTool):
    name: str = "Hotel Search Tool"
    description: str = "Search for available hotels in a destination city with filters"

    def _run(self, destination: str, check_in_date: str, check_out_date: str,
             guests: int = 1, budget_max: Optional[float] = None) -> str:
        """Search for hotels in a destination"""
        try:
            hotels = [
                {
                    "hotel_name": "Grand Hotel Plaza",
                    "location": destination,
                    "rating": 4.5,
                    "price_per_night": 199.99,
                    "total_price": 199.99 * self._calculate_nights(check_in_date, check_out_date),
                    "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
                    "rooms_available": 12
                },
                {
                    "hotel_name": "City Center Inn",
                    "location": destination,
                    "rating": 4.0,
                    "price_per_night": 149.99,
                    "total_price": 149.99 * self._calculate_nights(check_in_date, check_out_date),
                    "amenities": ["WiFi", "Breakfast", "Parking"],
                    "rooms_available": 25
                },
                {
                    "hotel_name": "Luxury Resort & Spa",
                    "location": destination,
                    "rating": 5.0,
                    "price_per_night": 299.99,
                    "total_price": 299.99 * self._calculate_nights(check_in_date, check_out_date),
                    "amenities": ["WiFi", "Pool", "Spa", "Restaurant", "Gym", "Room Service"],
                    "rooms_available": 8
                }
            ]

            if budget_max:
                hotels = [h for h in hotels if h["price_per_night"] <= budget_max]

            return json.dumps({
                "search_criteria": {
                    "destination": destination,
                    "check_in_date": check_in_date,
                    "check_out_date": check_out_date,
                    "guests": guests,
                    "budget_max": budget_max
                },
                "hotels": hotels,
                "total_results": len(hotels)
            }, indent=2)

        except Exception as e:
            return f"Error searching hotels: {str(e)}"

    def _calculate_nights(self, check_in: str, check_out: str) -> int:
        """Calculate number of nights between dates"""
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
        return (check_out_dt - check_in_dt).days

class BookingTool(BaseTool):
    name: str = "Booking Tool"
    description: str = "Create bookings for flights and hotels"

    def _run(self, booking_type: str, details: Dict[str, Any],
             customer_info: Dict[str, str]) -> str:
        """Create a booking reservation"""
        try:
            booking_id = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"

            booking = {
                "booking_id": booking_id,
                "booking_type": booking_type,
                "status": "confirmed",
                "created_at": datetime.now().isoformat(),
                "customer_info": customer_info,
                "details": details,
                "total_cost": details.get("total_price", 0),
                "confirmation_number": f"CONF{booking_id[2:]}"
            }

            return json.dumps({
                "success": True,
                "booking": booking,
                "message": f"Booking {booking_id} has been confirmed successfully!"
            }, indent=2)

        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Booking failed: {str(e)}"
            }, indent=2)

class TravelInfoTool(BaseTool):
    name: str = "Travel Info Tool"
    description: str = "Get travel information, visa requirements, and destination details"

    def _run(self, destination: str, info_type: str = "general") -> str:
        """Get travel information for a destination"""
        try:
            travel_info = {
                "Paris": {
                    "general": "Paris is the capital of France, known for its art, fashion, gastronomy and culture.",
                    "visa": "Most visitors need a Schengen visa. US citizens can stay up to 90 days without visa.",
                    "currency": "Euro (€)",
                    "language": "French",
                    "best_time_to_visit": "April to June, September to October",
                    "attractions": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Champs-Élysées"]
                },
                "Tokyo": {
                    "general": "Tokyo is Japan's capital, a bustling metropolis blending ultramodern and traditional.",
                    "visa": "Most visitors need a visa. US citizens can stay up to 90 days without visa.",
                    "currency": "Japanese Yen (¥)",
                    "language": "Japanese",
                    "best_time_to_visit": "March to May, September to November",
                    "attractions": ["Senso-ji Temple", "Shibuya Crossing", "Tokyo Skytree", "Meiji Shrine"]
                },
                "New York": {
                    "general": "New York City is a global hub of business, culture, and tourism.",
                    "visa": "Most international visitors need a visa. ESTA required for visa waiver countries.",
                    "currency": "US Dollar ($)",
                    "language": "English",
                    "best_time_to_visit": "April to June, September to November",
                    "attractions": ["Statue of Liberty", "Times Square", "Central Park", "Empire State Building"]
                }
            }

            if destination.title() in travel_info:
                info = travel_info[destination.title()].get(info_type, "Information not available")
            else:
                info = f"General travel information for {destination} not available in our database."

            return json.dumps({
                "destination": destination,
                "info_type": info_type,
                "information": info
            }, indent=2)

        except Exception as e:
            return f"Error retrieving travel info: {str(e)}"

class WeatherTool(BaseTool):
    name: str = "Weather Tool"
    description: str = "Get current weather and forecast for travel destinations"

    def _run(self, destination: str, days: int = 3) -> str:
        """Get weather forecast for a destination"""
        try:
            # Mock weather data
            weather_data = {
                "location": destination,
                "forecast": [
                    {
                        "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "condition": "Partly Cloudy" if i % 2 == 0 else "Sunny",
                        "high_temp": 22 + i,
                        "low_temp": 15 + i,
                        "precipitation": f"{i * 10}%"
                    } for i in range(days)
                ]
            }

            return json.dumps(weather_data, indent=2)

        except Exception as e:
            return f"Error retrieving weather data: {str(e)}"