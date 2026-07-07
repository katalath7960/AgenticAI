I want you to build an intelligent AI-powered automated testing framework that can execute test cases written in Excel against a web application.

Objective

Build a solution that reads test cases from Excel files stored in a folder, executes them against the website, captures the results, and updates the same Excel file with the execution status and evidence.

Website Under Test
https://qafjdforum.courts.phila.gov/

The login credentials (username and password) will be provided separately.

Functional Requirements
1. Read Test Cases
Read every Excel (.xlsx) file from a configurable folder.
Each workbook may contain one or more sheets.
Preserve all existing formatting and columns.
Process every test case in sequence.
2. Understand the Test Cases

The AI should intelligently interpret each row instead of relying only on hardcoded automation.

Examples of steps include:

Login
Click button
Click menu
Enter text
Select dropdown value
Select radio button
Check checkbox
Upload file
Download file
Search records
Add new record
Edit record
Delete record
Save
Cancel
Validate message
Validate page title
Validate URL
Validate field values
Validate table contents
Validate error messages
Validate mandatory fields
Validate navigation
Validate workflow
Logout

The AI should understand natural language instructions wherever possible.

3. Execute the Tests

Use Playwright (preferred) or Selenium.

The framework should:

Launch browser
Login
Execute every step
Wait intelligently for page loads
Handle AJAX loading
Handle dynamic controls
Handle popups
Handle modal dialogs
Handle multiple tabs
Handle file uploads
Handle downloads
Handle date pickers
Handle calendars
Handle rich text editors
4. Capture Evidence

For every failed step:

Take screenshot
Capture browser console errors
Capture page HTML if needed
Record exception details

For passed steps:

Optionally capture screenshots.
5. Update the Excel File

Do NOT create another results file.

Instead, append new columns such as:

| Result | Status | Actual Result | Error | Screenshot | Execution Time |

Example:

Test Case	Expected Result	Status	Actual Result	Screenshot
Login	User logged in	PASS	Successfully logged in	login.png
Save Case	Case saved	FAIL	Save button disabled	save_fail.png
6. Produce an Execution Summary

After execution generate:

Total Test Cases
Passed
Failed
Skipped
Pass Percentage
Total Execution Time

Also generate:

HTML Report
PDF Report
JSON Report
7. AI Intelligence

Rather than being a simple automation script, the framework should:

Understand natural language test steps.
Identify UI controls automatically.
Use labels instead of fixed XPath whenever possible.
Recover from minor UI changes.
Suggest alternative locators.
Retry intelligently.
Learn from previous executions.
Detect flaky tests.
Provide probable reasons for failures.
8. Framework Architecture

Use:

Python
Playwright
pandas
openpyxl
pytest
asyncio where applicable

Organize the project into modules:

config/

excel_reader/

executor/

playwright/

ai_engine/

reports/

screenshots/

logs/

utilities/

main.py
9. Configuration

Use a configuration file containing:

URL
Username
Password
Browser
Headless mode
Timeout
Screenshot folder
Excel folder
Report folder

No hardcoded values.

10. Logging

Create detailed logs including:

Start Time
End Time
Test Name
Executed Step
Result
Errors
Stack Trace
11. Error Handling

The framework should never stop after one failure.

Continue executing remaining test cases and report all failures.

12. Deliverables

Produce:

Complete source code
Installation guide
README
Requirements file
Sample configuration
Sample Excel template
HTML Report
PDF Report
Updated Excel files
Folder structure
Documentation
13. Future Enhancements

Design the framework so it can later support:

Multiple browsers (Chrome, Edge, Firefox)
Parallel execution
Cross-browser testing
CI/CD integration (GitHub Actions, Azure DevOps, Jenkins)
BrowserStack or Sauce Labs integration
AI-generated test cases from screenshots or requirements
AI-generated regression suites
Self-healing locators
Visual regression testing
Accessibility testing
Performance testing
API testing
Database validation
Email execution reports
Slack or Microsoft Teams notifications
Test execution scheduling
Expected Outcome

The final solution should function as an AI-powered test automation framework that can:

Read manual test cases from Excel.
Interpret the test steps using AI.
Execute them on the target website.
Validate expected versus actual results.
Capture screenshots and logs.
Update the original Excel file with execution results.
Generate comprehensive execution reports.
Be modular, scalable, and production-ready for enterprise use.