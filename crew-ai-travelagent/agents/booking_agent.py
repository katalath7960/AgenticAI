from crewai import Agent
from config.settings import settings
from tools.travel_tools import FlightSearchTool, HotelSearchTool, BookingTool
from typing import Dict, List, Any

class BookingAgent:
    def __init__(self):
        self.agent = Agent(
            role="Booking Specialist",
            goal="Accurately process travel bookings, ensure all details are correct, and provide confirmation",
            backstory="""You are a meticulous booking specialist with years of experience in travel reservations.
            Your responsibilities include:
            - Processing flight and hotel bookings with 100% accuracy
            - Verifying all customer information and travel details
            - Ensuring booking compliance with airline/hotel policies
            - Providing clear booking confirmations and important details
            - Handling booking modifications and cancellations when needed
            - Maintaining detailed records of all transactions
            - Following up on booking status and any changes
            - Escalating complex issues to appropriate channels""",
            verbose=settings.verbose,
            allow_delegation=False,  # Booking agent works independently for accuracy
            temperature=settings.booking_agent_temperature,  # Lower temperature for precision
            tools=[
                FlightSearchTool(),
                HotelSearchTool(),
                BookingTool()
            ]
        )

    def get_agent(self):
        return self.agent

    def process_booking_request(self, booking_details: Dict[str, Any]) -> str:
        """Process a booking request with all necessary validations"""
        return f"""Processing booking request with the following details:

**Booking Information:**
- Type: {booking_details.get('type', 'Not specified')}
- Customer: {booking_details.get('customer_name', 'Not specified')}
- Travel Dates: {booking_details.get('dates', 'Not specified')}
- Destination: {booking_details.get('destination', 'Not specified')}

**Verification Steps:**
1. ✅ Validate customer information
2. 🔍 Check availability for requested dates
3. 💰 Verify pricing and calculate totals
4. 📋 Confirm booking policies and restrictions
5. 🔒 Process secure payment (if applicable)
6. 📧 Send confirmation and important details

I will ensure every detail is correct before confirming your booking."""

    def verify_booking_details(self) -> str:
        """Checklist for verifying booking details"""
        return """**Booking Verification Checklist:**

**Customer Information:**
- Full name (as it appears on ID)
- Contact phone number
- Email address
- Date of birth (if required)
- Passport/ID details

**Travel Details:**
- Departure/arrival airports
- Travel dates and times
- Number of passengers
- Seat preferences (if applicable)
- Special requests or requirements

**Payment Information:**
- Payment method verification
- Billing address confirmation
- Total amount calculation
- Tax and fee breakdown

**Policy Confirmation:**
- Cancellation policy review
- Change fee understanding
- Refund eligibility
- Travel insurance options

All details will be double-checked before processing."""

    def handle_booking_confirmation(self, booking_data: Dict[str, Any]) -> str:
        """Provide comprehensive booking confirmation"""
        return f"""🎉 **Booking Confirmed!**

**Confirmation Details:**
- Booking ID: {booking_data.get('booking_id', 'N/A')}
- Confirmation Number: {booking_data.get('confirmation_number', 'N/A')}
- Status: {booking_data.get('status', 'Confirmed')}

**Important Information:**
- **Check-in:** Please arrive 2-3 hours before international flights
- **Documents:** Bring valid passport and visa (if required)
- **Contact:** Keep this confirmation handy for any questions
- **Changes:** Contact us immediately if you need to modify this booking

**What's Next:**
1. You will receive an email confirmation shortly
2. Download the mobile app for easy access to your booking
3. Check travel requirements for your destination
4. Consider travel insurance for peace of mind

**Need Help?**
- Customer Service: Available 24/7
- Emergency Contact: For urgent travel changes
- App Support: Real-time booking management

Safe travels! ✈️"""

    def handle_modification_request(self, modification_type: str) -> str:
        """Handle booking modification requests"""
        modification_responses = {
            "date_change": """**Date Change Request**

I can help you change your travel dates. Please note:
- Airline change fees typically $200-500
- Hotel cancellation/rebooking policies vary
- Refunds may not be available depending on timing
- New availability is not guaranteed

Would you like me to check availability for your preferred new dates?""",

            "cancellation": """**Cancellation Request**

Before proceeding with cancellation:
- Review the cancellation policy for your booking
- Note any applicable fees or penalties
- Consider travel insurance coverage
- Check refund processing time (typically 7-14 days)

Are you sure you'd like to proceed with cancellation?""",

            "passenger_change": """**Passenger Information Change**

For passenger changes:
- Name changes may incur fees or require rebooking
- Age changes affect pricing and requirements
- Contact information updates are usually free
- Documentation changes may require verification

What specific passenger information needs to be updated?"""
        }

        return modification_responses.get(modification_type,
            "I can help you with booking modifications. Please specify what changes you need to make.")

    def check_booking_status(self, booking_id: str) -> str:
        """Check the current status of a booking"""
        return f"""**Booking Status Check for {booking_id}**

Checking your booking status...

**Current Status:** Confirmed ✓

**Flight Details:**
- Airline: [Airline Name]
- Flight: [Flight Number]
- Route: [Origin] → [Destination]
- Date/Time: [Departure Date/Time]
- Status: On Time

**Hotel Details:**
- Hotel: [Hotel Name]
- Check-in: [Check-in Date/Time]
- Check-out: [Check-out Date/Time]
- Confirmation: [Hotel Confirmation #]

**Next Steps:**
- No action required - your booking is confirmed
- Check-in reminder will be sent 24 hours before travel
- Travel documents will be available in the app

Is there anything specific about your booking you'd like me to check?"""