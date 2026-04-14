# Tech Stack
    - Streamlit
    - Python FastAPI
    - Csv
    - Excel Handling: pandas / openpyxl / xlsxm
    - Email: SMTP (Gmail)
    - Barcode Generation: libraries like python-barcode, qrcode, or JsBarcode
    - Barcode Scanning: html5-qrcode or similar free JS libraries
    - Frontend: React + Bootstrap
    - Langgraph
    - Docker


# Requirements

WFGEventScanner Project 
1 
Project: Build Event Barcode Emailing System + Scanner Web App
Business Problem 
An event with approximately 1,000 attendees requires a fast, accurate, and organized check-in process. Currently, managing guest entry and directing them to their assigned tables based on predefined categories (color codes) is manual, time-consuming, and prone to errors.

The event organizers maintain an Excel sheet with attendee details, including names, email addresses, and color-coded table assignments. However, there is no automated system to:

Distribute personalized entry credentials to attendees in advance
Verify attendees efficiently at the venue
Quickly identify and direct guests to the correct tables
Track which invitations have been sent and completed

Objective

Design and implement a streamlined, automated solution that:

Sends personalized, scannable entry credentials (barcodes) to all attendees
Enables quick and reliable check-in through barcode scanning
Instantly displays attendee details and table assignment (color code)
Tracks invitation status and completion in a centralized system

Your Task: Complete Project Implementation 
Design, implement, and demonstrate a complete AI system that: 

I need to build an automated system with the following requirements:

📊 Input Data
I have an Excel sheet containing:
Invitee Name
Email Address
Color Code (used for table assignment)
Status column (e.g., “Complete”)
It is stored under Data\Input and the name of the file is WFHAttendees.csv

🎯 Goal
Create an automated workflow (Agent) and a simple web app to manage event check-in using barcodes.

⚙️ Part 1: Automation Agent

Build an agent that:
Reads the Excel file.
For each invitee:
Generates a unique barcode (using a free barcode generator library/API).
Barcode should encode: Name + Color Code (or a unique ID mapped to them).
Sends an email to each invitee:
Includes the barcode (image or attachment).
Includes basic event instructions.
Updates the Excel file:
Marks the “Status” column as Complete after email is sent.

Constraints:
Use only free/open-source tools or APIs.
Should handle bulk sending reliably.
Prefer Python or Node.js for backend automation.

🌐 Part 2: Scanner Web App
Build a simple web application with:

Frontend:
Use React + Bootstrap.
Clean UI for event staff.

Features:
Barcode Scanner:
Use a free library (e.g., camera-based scanning).
On scan:
Decode barcode.
Display:
Invitee Name
Color Code
Event Name

# Team 
- Product Manager
- Backend Dev focused on DB, INfra
- Backend Dev focused on API, Coding
- Frontend Dev focused on Streamlit
- QA Eng for writing automated test 