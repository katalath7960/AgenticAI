#!/usr/bin/env python3
"""
Travel Booking Crew AI System
A multi-agent system for handling customer interactions in a travel booking platform.
"""

import os
import sys
from dotenv import load_dotenv
from core.travel_booking_crew import TravelBookingCrew

# Load environment variables
load_dotenv()

def setup_environment():
    """Setup the environment and check for required API keys"""
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables.")
        print("   Please set your OpenAI API key to enable AI functionality.")
        print("   You can still run the system with limited functionality.\n")

def main():
    """Main entry point for the Travel Booking Crew AI System"""
    print("🌟 Travel Booking Crew AI System")
    print("=" * 50)

    # Setup environment
    setup_environment()

    # Initialize the crew
    try:
        crew = TravelBookingCrew()
        print("✅ Crew AI system initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize crew system: {e}")
        sys.exit(1)

    # Run interactive session
    try:
        crew.run_interactive_session()
    except KeyboardInterrupt:
        print("\n\n👋 Session interrupted. Thank you for using Travel Booking Crew AI!")
    except Exception as e:
        print(f"\n❌ An error occurred during the session: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()