"""
generate_mock_data.py
Generates mock CSV files for the Feedback Intelligence pipeline:
  - data/input/app_store_reviews.csv  (50 rows)
  - data/input/support_emails.csv     (30 rows)
  - data/input/expected_classifications.csv  (80 rows)
"""

import csv
import os
import random
from datetime import datetime, timedelta

random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "input")
os.makedirs(BASE_DIR, exist_ok=True)

TODAY = datetime.now()
VERSIONS = ["2.1.3", "3.0.1", "3.1.0", "3.0.5"]
PLATFORMS = ["Google Play", "App Store"]
USER_NAMES = [
    "alice_m", "bob_j", "carol_k", "dave_r", "eve_s",
    "frank_t", "grace_l", "henry_w", "iris_p", "jake_n",
    "karen_o", "leo_b", "mia_c", "noah_d", "olivia_f",
    "peter_g", "quinn_h", "rachel_i", "sam_q", "tina_u",
]


def random_date(days_back: int = 90) -> str:
    delta = timedelta(days=random.randint(0, days_back))
    return (TODAY - delta).strftime("%Y-%m-%d")


# ─────────────────────────────────────────────
# App Store Reviews  (50 rows)
# ─────────────────────────────────────────────
BUG_REVIEWS = [
    (1, "App crashes every time I try to open my profile since the 3.0.1 update. "
        "Steps: 1) Open app 2) Tap Profile icon 3) App freezes and closes immediately. "
        "iPhone 14, iOS 16.5. Very frustrating!"),
    (1, "Can't login after updating to v3.1.0. I enter my credentials and the spinner "
        "just keeps going forever. Had to uninstall and reinstall but still broken. "
        "Samsung Galaxy S22, Android 13."),
    (1, "Data sync completely broken. My notes are not syncing between my phone and "
        "iPad. Started after 3.0.5 update. Losing important work."),
    (2, "App freezes on the home screen after about 30 seconds. I have to force-close "
        "it every time. Pixel 7, Android 14."),
    (1, "Crash on startup after latest update. Tried clearing cache, didn't help. "
        "Galaxy Note 20, Android 12. Steps to reproduce: just open the app."),
    (2, "Push notifications stopped working completely on iOS 17. I'm missing important "
        "alerts. iPhone 15 Pro, app version 3.1.0."),
    (1, "The search feature returns no results even for exact matches. Broken since v3.0.5. "
        "OnePlus 10 Pro, Android 13."),
    (2, "Video upload fails with a generic error message. Tried on WiFi and LTE. "
        "iPhone 13, iOS 16.6, app v3.0.1."),
    (1, "Offline mode is completely broken. App shows 'No connection' even with full WiFi. "
        "Pixel 6a, Android 12, v3.0.5."),
    (2, "Battery drain is extreme after 3.1.0 update. Phone gets hot and loses 30% battery "
        "per hour just with the app running in background. iPhone 15, iOS 17.1."),
    (1, "Cannot attach files in messages. Tap the attachment icon and nothing happens. "
        "Galaxy S21, Android 13, v3.0.1."),
    (2, "App shows blank white screen after splash. Have to reopen 3-4 times before it loads. "
        "iPhone 12 Mini, iOS 16.4, v3.1.0."),
]

FEATURE_REVIEWS = [
    (4, "Please add dark mode! My eyes hurt using the app at night. Would be a huge improvement."),
    (3, "Would love to see a calendar view for tasks. The list view gets overwhelming."),
    (4, "It would be great if you could export data to PDF directly from the app."),
    (3, "Please add fingerprint / Face ID login support. Typing password every time is annoying."),
    (4, "Would love widget support for the home screen showing daily summary."),
    (3, "Multiple account support would be amazing for switching between work and personal."),
    (4, "Please add a Siri shortcut integration so I can open items hands-free."),
    (3, "A bulk action feature to archive or delete multiple items at once would save so much time."),
    (4, "Can you add a reminder / snooze feature for tasks? Currently there's no way to delay."),
    (4, "Would be great to have collaboration features so teams can share and edit together."),
]

PRAISE_REVIEWS = [
    (5, "Absolutely love this app! It's transformed how I manage my daily tasks. Clean UI too."),
    (5, "Best productivity app I've ever used. The new dashboard in 3.1.0 is gorgeous."),
    (5, "Amazing update! Everything is snappy and the new design is really polished."),
    (4, "Great app overall. Really helped me stay organized. Minor bugs aside, 5-star quality."),
    (5, "Love the new feature in 3.0.1. The team clearly listens to user feedback. Keep it up!"),
    (4, "Excellent app. Support team is also very responsive. Had an issue and it was resolved quickly."),
    (5, "Outstanding! I've tried 10 other apps and this blows them all out of the water."),
    (4, "Really solid update. App feels much faster and the onboarding flow is much improved."),
    (5, "This app is a game changer for my workflow. Highly recommend to anyone in project management."),
    (4, "Impressive how much the team has improved the app in the last 6 months. Great work!"),
]

COMPLAINT_REVIEWS = [
    (2, "The premium subscription price is way too high for what you get. Competitors offer more for less."),
    (1, "App is very slow to load. Takes 10+ seconds every time I open it. Unacceptable."),
    (2, "Customer support takes days to respond. Had an issue for two weeks with no resolution."),
    (2, "The onboarding is confusing and there are no tutorial videos. Hard to figure out."),
    (3, "Too many ads in the free tier. They interrupt my workflow constantly."),
    (1, "Cancelled my subscription because the app keeps losing my data. Completely unreliable."),
    (2, "The app uses too much storage on my phone. Over 500MB for what it does is ridiculous."),
    (2, "Interface is cluttered and unintuitive. Way too many menus buried inside menus."),
    (1, "No offline support whatsoever. Useless without internet. This is a basic feature."),
    (2, "The analytics section never loads properly. Always shows 'Data unavailable'. Useless."),
]

SPAM_REVIEWS = [
    (5, "Download my free app at freeapps247.com! Best deals on premium apps!!!"),
    (1, "WORST APP EVER!!!! 👎👎👎👎👎 DO NOT DOWNLOAD!!! SCAM SCAM SCAM!!!!"),
    (5, "asdfghjkl this app is ok i guess lol whatever never mind forget it"),
    (3, "I am not a robot. This review is genuine. Buy crypto now at bit-invest.net"),
    (4, "Good app good app good app good app good app good app good app good"),
    (2, "jkjkjkjkjkjkjkjkjkjkjkjkjk nope nope nope nope 123456789 test test"),
    (5, "Follow me on Instagram @cooluser2024 for lifestyle tips! Great app too I guess"),
    (1, "This review is for another app I accidentally downloaded. Wrong store page."),
]

review_rows = []
review_id = 1

def make_review(text, rating, category):
    global review_id
    row = {
        "review_id": f"REV-{review_id:04d}",
        "platform": random.choice(PLATFORMS),
        "rating": rating,
        "review_text": text,
        "user_name": random.choice(USER_NAMES),
        "date": random_date(),
        "app_version": random.choice(VERSIONS),
        "_category": category,  # internal, removed before writing
    }
    review_id += 1
    return row

for rating, text in BUG_REVIEWS:
    r = make_review(text, rating, "Bug")
    if len(review_rows) < 6:
        r["platform"] = "App Store"
    else:
        r["platform"] = "Google Play"
    review_rows.append(r)

for rating, text in FEATURE_REVIEWS:
    r = make_review(text, rating, "Feature Request")
    review_rows.append(r)

for rating, text in PRAISE_REVIEWS:
    r = make_review(text, rating, "Praise")
    review_rows.append(r)

for rating, text in COMPLAINT_REVIEWS:
    r = make_review(text, rating, "Complaint")
    review_rows.append(r)

for rating, text in SPAM_REVIEWS:
    r = make_review(text, rating, "Spam")
    review_rows.append(r)

# Shuffle and assign platforms ~50/50
random.shuffle(review_rows)
for i, r in enumerate(review_rows):
    r["platform"] = "App Store" if i % 2 == 0 else "Google Play"

REVIEW_FIELDS = ["review_id", "platform", "rating", "review_text", "user_name", "date", "app_version"]
REVIEW_CATEGORIES = {r["review_id"]: r["_category"] for r in review_rows}

reviews_path = os.path.join(BASE_DIR, "app_store_reviews.csv")
with open(reviews_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
    writer.writeheader()
    for r in review_rows:
        writer.writerow({k: r[k] for k in REVIEW_FIELDS})

print(f"✓ Written {len(review_rows)} reviews → {reviews_path}")


# ─────────────────────────────────────────────
# Support Emails  (30 rows)
# ─────────────────────────────────────────────
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "work.io"]

def random_email():
    user = random.choice(USER_NAMES)
    domain = random.choice(DOMAINS)
    return f"{user}@{domain}"

def random_timestamp(days_back: int = 90) -> str:
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return (TODAY - delta).strftime("%Y-%m-%dT%H:%M:%S")

def random_priority():
    weights = [0.30, 0.35, 0.25, 0.10]  # blank, High, Medium, Low
    choices = ["", "High", "Medium", "Low"]
    return random.choices(choices, weights=weights)[0]

EMAIL_DATA = [
    # Bug emails (technical, with device/OS/steps)
    {
        "subject": "App Crash Report — iPhone 15 iOS 17.4",
        "body": (
            "Hi Support Team,\n\n"
            "I'm experiencing repeated crashes on my iPhone 15 running iOS 17.4 with app version 3.1.0.\n\n"
            "Steps to reproduce:\n"
            "1. Open the app\n"
            "2. Navigate to the Settings tab\n"
            "3. Tap on 'Account Details'\n"
            "4. App crashes immediately with no error message\n\n"
            "This happens 100% of the time. I've tried reinstalling but the issue persists.\n\n"
            "Device: iPhone 15\nOS: iOS 17.4\nApp Version: 3.1.0\n\n"
            "Please fix ASAP as I rely on this app for work.\n\nBest,\nJohn"
        ),
        "_category": "Bug", "_priority_label": "High",
    },
    {
        "subject": "Login Issue Since v3.0.1 Update",
        "body": (
            "Hello,\n\n"
            "Since updating to v3.0.1 last week I cannot log in to my account.\n\n"
            "When I enter my email and password and tap 'Sign In', the loading spinner appears "
            "for about 5 seconds then disappears without logging me in or showing an error.\n\n"
            "Device: Samsung Galaxy S22\nOS: Android 13\nApp Version: 3.0.1\n\n"
            "Steps to reproduce:\n"
            "1. Open app\n"
            "2. Enter valid credentials\n"
            "3. Tap Sign In\n"
            "4. Spinner appears then vanishes — not logged in\n\n"
            "I've tried resetting my password, still same issue.\n\nThanks"
        ),
        "_category": "Bug", "_priority_label": "High",
    },
    {
        "subject": "Data Loss Problem — Urgent",
        "body": (
            "URGENT — I have lost 3 weeks of data after the 3.0.5 update.\n\n"
            "All my notes and task history before March 2024 are gone. "
            "The app shows an empty state when I tap on History.\n\n"
            "Device: Google Pixel 7\nOS: Android 14\nApp Version: 3.0.5\n\n"
            "Steps:\n"
            "1. Update app to 3.0.5\n"
            "2. Open app\n"
            "3. Navigate to History tab\n"
            "4. All previous entries gone\n\n"
            "This is critical — I need that data for work. Please escalate immediately."
        ),
        "_category": "Bug", "_priority_label": "Critical",
    },
    {
        "subject": "Notification Bug — Not Receiving Alerts",
        "body": (
            "Hi,\n\n"
            "Push notifications stopped working after I upgraded to iOS 17.1.\n\n"
            "Device: iPhone 14 Pro\nOS: iOS 17.1\nApp Version: 3.1.0\n\n"
            "Steps:\n"
            "1. Enable notifications in app settings (confirmed allowed in iOS Settings too)\n"
            "2. Set a reminder for 5 minutes from now\n"
            "3. Wait — no notification arrives\n\n"
            "Tried toggling permissions off and on. No improvement.\n\nRegards, Sarah"
        ),
        "_category": "Bug", "_priority_label": "Medium",
    },
    {
        "subject": "Sync Failure Between iPad and iPhone",
        "body": (
            "Hello Support,\n\n"
            "My data is not syncing between my iPhone and iPad. I create an item on iPhone "
            "and it never appears on iPad, even after waiting 30 minutes.\n\n"
            "iPhone 13, iOS 16.6, App v3.0.5\niPad Pro 11', iPadOS 16.6, App v3.0.5\n\n"
            "Steps:\n"
            "1. Create new task on iPhone\n"
            "2. Open iPad (signed into same account)\n"
            "3. Task does not appear\n"
            "4. Pull to refresh — still missing\n\n"
            "Both devices are on the same WiFi network.\n\nThank you"
        ),
        "_category": "Bug", "_priority_label": "High",
    },
    {
        "subject": "App Freezes on Android 14 — Galaxy S23",
        "body": (
            "Hi,\n\nThe app freezes completely on my Galaxy S23 running Android 14.\n\n"
            "Device: Samsung Galaxy S23\nOS: Android 14\nApp Version: 3.1.0\n\n"
            "Steps to reproduce:\n"
            "1. Open app\n"
            "2. Go to the Dashboard\n"
            "3. Scroll down rapidly\n"
            "4. App becomes unresponsive — must force-kill\n\n"
            "Happens consistently. Clearing cache does not help.\n\nBest, Mike"
        ),
        "_category": "Bug", "_priority_label": "High",
    },
    {
        "subject": "Search Not Returning Results",
        "body": (
            "Hi support,\n\nThe search feature is completely broken for me. I type in exact "
            "words that I know are in my notes and get zero results.\n\n"
            "Device: OnePlus 10 Pro\nOS: Android 13\nApp Version: 3.0.5\n\n"
            "Steps:\n"
            "1. Open app and navigate to Search\n"
            "2. Type 'meeting notes' (I have 20 notes with this phrase)\n"
            "3. Results show: 'No items found'\n\n"
            "Please help — search is critical for my use.\n\nRegards"
        ),
        "_category": "Bug", "_priority_label": "Medium",
    },
    # Feature Request emails
    {
        "subject": "Feature Request: Dark Mode Support",
        "body": (
            "Hello,\n\nI love the app but I would really appreciate a dark mode option. "
            "I use the app late at night and the bright white background is hard on my eyes. "
            "Many apps have this feature now and it would greatly improve my experience.\n\n"
            "Thank you for considering this!\n\nBest, Laura"
        ),
        "_category": "Feature Request", "_priority_label": "Medium",
    },
    {
        "subject": "Request: Export to PDF Functionality",
        "body": (
            "Hi Team,\n\n"
            "It would be incredibly useful to export my task lists and notes as PDF files "
            "directly from the app. I often need to share progress reports with my manager "
            "and currently I have to copy everything manually.\n\n"
            "A simple export button would save me 30 minutes every week.\n\nThank you"
        ),
        "_category": "Feature Request", "_priority_label": "Medium",
    },
    {
        "subject": "Suggestion: Biometric Login",
        "body": (
            "Hello,\n\nI'd love to see Face ID / fingerprint login support. "
            "Typing my long password every time is inconvenient, especially on mobile. "
            "Almost every other app of this type supports biometrics now.\n\n"
            "Would really improve day-to-day usability.\n\nThanks!"
        ),
        "_category": "Feature Request", "_priority_label": "Low",
    },
    {
        "subject": "Suggestion for Improvement: Calendar Integration",
        "body": (
            "Hi,\n\nI think adding calendar integration (Google Calendar / Apple Calendar) "
            "would make this app a complete productivity solution. Right now I have to switch "
            "between two apps to manage my tasks and calendar.\n\n"
            "Even a read-only calendar view inside the app would be great.\n\nBest regards"
        ),
        "_category": "Feature Request", "_priority_label": "Medium",
    },
    {
        "subject": "Feature Request: Team Collaboration",
        "body": (
            "Dear Team,\n\nOur company is evaluating your app for team use. One key missing "
            "feature is real-time collaboration — multiple users editing the same project "
            "simultaneously. This is a deal-breaker for us at the enterprise level.\n\n"
            "If this is on the roadmap, please let us know the ETA.\n\nRegards, Enterprise Team"
        ),
        "_category": "Feature Request", "_priority_label": "High",
    },
    {
        "subject": "Feedback: Offline Mode Would Be Great",
        "body": (
            "Hello,\n\nI travel frequently and often have no internet access. "
            "Having full offline mode with sync when back online would make this app "
            "perfect for frequent travelers like me.\n\n"
            "Currently the app is unusable without connection.\n\nThanks for considering!"
        ),
        "_category": "Feature Request", "_priority_label": "Medium",
    },
    # Complaints
    {
        "subject": "Subscription Price Too High",
        "body": (
            "Hello,\n\nI've been a user for 2 years and the recent price increase to $15/month "
            "is simply too much for what's offered. Competitors charge $5-8/month for the same "
            "or more features. I'm considering cancelling unless pricing is reviewed.\n\nThanks"
        ),
        "_category": "Complaint", "_priority_label": "Medium",
    },
    {
        "subject": "Very Slow App Performance",
        "body": (
            "Hi,\n\nThe app has become extremely slow over the past few months. "
            "Loading the dashboard takes 8-10 seconds. Switching tabs takes 3-4 seconds. "
            "This was not an issue before. I'm considering switching to a competitor if "
            "performance doesn't improve.\n\nFrustrated user"
        ),
        "_category": "Complaint", "_priority_label": "Medium",
    },
    {
        "subject": "Poor Customer Support Experience",
        "body": (
            "To Whom It May Concern,\n\nI submitted a support ticket 2 weeks ago about a billing "
            "issue and have received only one automated response. No real human has contacted me. "
            "I am a premium subscriber and this level of support is unacceptable.\n\nDisappointed"
        ),
        "_category": "Complaint", "_priority_label": "High",
    },
    {
        "subject": "Too Many Ads in Free Tier",
        "body": (
            "Hello,\n\nThe number of ads in the free tier has increased drastically and they now "
            "appear every 2-3 actions. This makes the app nearly unusable without paying. "
            "I understand monetization but this is excessive.\n\nRegards"
        ),
        "_category": "Complaint", "_priority_label": "Low",
    },
    {
        "subject": "App Uses Too Much Storage",
        "body": (
            "Hi,\n\nI noticed the app is using 600MB of storage on my phone which is far too much. "
            "I have limited storage and this app is taking up a disproportionate amount. "
            "Please optimize storage usage or add a 'Clear Cache' option in settings.\n\nThanks"
        ),
        "_category": "Complaint", "_priority_label": "Low",
    },
    # Praise emails
    {
        "subject": "Love the New Dashboard Design!",
        "body": (
            "Hi Team,\n\nJust wanted to say the new dashboard in v3.1.0 is absolutely beautiful. "
            "The redesign made everything so much more intuitive. Great work by your design team!\n\n"
            "Keep up the excellent work. This is my go-to productivity app.\n\nThanks!"
        ),
        "_category": "Praise", "_priority_label": "Low",
    },
    {
        "subject": "Outstanding App — Highly Recommend",
        "body": (
            "Hello,\n\nI've been using your app for 18 months and it keeps getting better. "
            "The v3.0.1 update was especially impressive. Performance improvements are noticeable "
            "and the new features are exactly what I needed.\n\n"
            "Please keep it up! Recommending it to my entire team.\n\nBest"
        ),
        "_category": "Praise", "_priority_label": "Low",
    },
    {
        "subject": "Great Customer Support Experience",
        "body": (
            "Hi,\n\nI had a billing issue last week and your support team resolved it within 2 hours. "
            "That's exceptional service. The rep (Alex) was courteous and efficient.\n\n"
            "Just wanted to share positive feedback. Keep it up!\n\nKind regards"
        ),
        "_category": "Praise", "_priority_label": "Low",
    },
    # More bugs to meet minimum 5 technical bug emails
    {
        "subject": "Crash When Uploading Large Files",
        "body": (
            "Hello,\n\nThe app crashes every time I try to upload files larger than 10MB.\n\n"
            "Device: iPhone 13 Pro\nOS: iOS 16.6\nApp Version: 3.0.1\n\n"
            "Steps:\n"
            "1. Tap the '+' button to add attachment\n"
            "2. Select a 15MB PDF from Files\n"
            "3. Upload progress bar appears\n"
            "4. At ~60% progress, app crashes\n\n"
            "Consistent across multiple files and network conditions.\n\nRegards, Tom"
        ),
        "_category": "Bug", "_priority_label": "Medium",
    },
    {
        "subject": "Two-Factor Authentication Not Working",
        "body": (
            "Hi Support,\n\nThe 2FA SMS codes are not being delivered to my phone. "
            "I enabled 2FA last week and now I cannot log in at all because I never receive the code.\n\n"
            "Device: Samsung Galaxy A52\nOS: Android 12\nApp Version: 3.0.5\n\n"
            "Steps:\n"
            "1. Open app\n"
            "2. Enter email and password\n"
            "3. 2FA screen appears — wait for SMS\n"
            "4. SMS never arrives (checked spam, tried resend 5 times)\n\n"
            "This is a blocker — I cannot access my account.\n\nUrgently, David"
        ),
        "_category": "Bug", "_priority_label": "Critical",
    },
    {
        "subject": "Widget Crashes Home Screen",
        "body": (
            "Hello,\n\nThe home screen widget crashes my launcher when I try to add it. "
            "Goes directly back to home screen after selecting widget.\n\n"
            "Device: Pixel 7a\nOS: Android 14\nApp Version: 3.1.0\n\n"
            "Steps:\n"
            "1. Long press home screen\n"
            "2. Select Widgets\n"
            "3. Find app widget\n"
            "4. Drag to home screen — launcher crashes\n\n"
            "Reproducible every time.\n\nThanks"
        ),
        "_category": "Bug", "_priority_label": "Low",
    },
    # More feature requests
    {
        "subject": "Request: Apple Watch App",
        "body": (
            "Hello,\n\nAn Apple Watch companion app would be a fantastic addition. "
            "Being able to check and check-off tasks from my wrist would save a lot of time. "
            "Many of your competitors already have this. Please consider adding it!\n\nThank you"
        ),
        "_category": "Feature Request", "_priority_label": "Low",
    },
    {
        "subject": "Suggestion: Custom Themes",
        "body": (
            "Hi Team,\n\nIt would be great if users could choose from different color themes "
            "beyond just light and dark mode. Custom accent colors would let users personalize "
            "the experience.\n\nJust a thought — keep up the good work!\n\nBest"
        ),
        "_category": "Feature Request", "_priority_label": "Low",
    },
    # More complaints
    {
        "subject": "No Refund for Cancelled Subscription",
        "body": (
            "Hello,\n\nI cancelled my annual subscription mid-year and was told I would not "
            "receive a refund for the unused months. This is unacceptable and against consumer "
            "protection rules in my country. I expect a pro-rata refund.\n\nRegards"
        ),
        "_category": "Complaint", "_priority_label": "High",
    },
    # More praise
    {
        "subject": "App Has Transformed My Productivity",
        "body": (
            "Hi,\n\nI just wanted to say this app has genuinely changed how I work. "
            "I used to miss deadlines and feel overwhelmed. After 6 months with your app, "
            "I'm on top of everything. The recurring tasks feature is a lifesaver.\n\nThank you!"
        ),
        "_category": "Praise", "_priority_label": "Low",
    },
    {
        "subject": "Impressed by the Accessibility Features",
        "body": (
            "Hello Team,\n\nAs someone with low vision, I want to thank you for excellent "
            "accessibility support. The dynamic text sizing and VoiceOver compatibility work "
            "flawlessly. Very few apps get this right.\n\nKeep it up!"
        ),
        "_category": "Praise", "_priority_label": "Low",
    },
    {
        "subject": "Quick Question About Storage Limits",
        "body": (
            "Hi,\n\nI'm a free user and wanted to know what the storage limit is before "
            "I need to upgrade to premium. I can't find this information clearly in the app.\n\n"
            "Also, love the app — very well designed!\n\nThanks"
        ),
        "_category": "Complaint", "_priority_label": "Low",
    },
]

PRIORITIES = ["High", "Medium", "Low", "Critical"]
email_rows = []

for i, ed in enumerate(EMAIL_DATA):
    pri = ed.get("_priority_label", random_priority())
    email_rows.append({
        "email_id": f"EML-{i+1:04d}",
        "subject": ed["subject"],
        "body": ed["body"],
        "sender_email": random_email(),
        "timestamp": random_timestamp(),
        "priority": pri if random.random() > 0.30 else "",
        "_category": ed["_category"],
        "_priority_label": pri,
    })

# Ensure ~30% blank priority
for j in range(len(email_rows)):
    if j % 3 == 2:
        email_rows[j]["priority"] = ""

EMAIL_FIELDS = ["email_id", "subject", "body", "sender_email", "timestamp", "priority"]
EMAIL_CATEGORIES = {r["email_id"]: (r["_category"], r["_priority_label"]) for r in email_rows}

emails_path = os.path.join(BASE_DIR, "support_emails.csv")
with open(emails_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=EMAIL_FIELDS)
    writer.writeheader()
    for r in email_rows:
        writer.writerow({k: r[k] for k in EMAIL_FIELDS})

print(f"✓ Written {len(email_rows)} emails  → {emails_path}")


# ─────────────────────────────────────────────
# Expected Classifications  (50 + 30 = 80 rows)
# ─────────────────────────────────────────────
PRIORITY_MAP = {
    "Bug": {
        "crash": "Critical", "data loss": "Critical", "data is not syncing": "High",
        "login": "High", "freeze": "High", "sync": "High", "broken": "High",
        "slow": "Medium", "notification": "Medium", "search": "Medium", "upload": "Medium",
        "cosmetic": "Low", "widget": "Low", "battery": "Medium",
    },
    "Feature Request": "Medium",
    "Complaint": "Medium",
    "Praise": "Low",
    "Spam": "Low",
}

TECHNICAL_TEMPLATES = {
    "Bug": "Device/OS details and reproduction steps extracted from feedback text.",
    "Feature Request": "",
    "Complaint": "",
    "Praise": "",
    "Spam": "",
}

def guess_priority(category: str, text: str) -> str:
    text_lower = text.lower()
    if category == "Bug":
        if any(k in text_lower for k in ["crash", "data loss", "lost", "unable to open", "frozen", "blocker", "critical", "urgent"]):
            return "Critical"
        if any(k in text_lower for k in ["login", "sign in", "sync", "freeze", "broken", "cannot", "not working", "2fa", "two-factor"]):
            return "High"
        if any(k in text_lower for k in ["notification", "search", "upload", "battery", "slow", "blank"]):
            return "Medium"
        return "Low"
    if category == "Complaint":
        if any(k in text_lower for k in ["refund", "urgent", "unacceptable", "cancel"]):
            return "High"
        if any(k in text_lower for k in ["slow", "price", "support", "ads"]):
            return "Medium"
        return "Low"
    if category == "Feature Request":
        if any(k in text_lower for k in ["enterprise", "team", "collaboration", "deal-breaker"]):
            return "High"
        return "Medium"
    return "Low"

def make_title(category: str, text: str) -> str:
    text = text.strip()
    if category == "Bug":
        if "crash" in text.lower():
            return "Fix app crash on affected screen"
        if "login" in text.lower() or "sign in" in text.lower():
            return "Fix login failure after update"
        if "sync" in text.lower() or "data loss" in text.lower():
            return "Fix data sync and loss issue"
        if "notification" in text.lower():
            return "Fix push notifications not delivered"
        if "search" in text.lower():
            return "Fix search returning no results"
        if "freeze" in text.lower() or "frozen" in text.lower():
            return "Fix app freeze and unresponsiveness"
        if "upload" in text.lower():
            return "Fix file upload crash on large files"
        if "2fa" in text.lower() or "two-factor" in text.lower():
            return "Fix 2FA SMS codes not delivered"
        if "widget" in text.lower():
            return "Fix widget crash on home screen"
        return "Investigate and fix reported bug"
    if category == "Feature Request":
        if "dark mode" in text.lower():
            return "Add dark mode to app settings"
        if "pdf" in text.lower() or "export" in text.lower():
            return "Add PDF export functionality"
        if "biometric" in text.lower() or "face id" in text.lower() or "fingerprint" in text.lower():
            return "Add biometric login support"
        if "calendar" in text.lower():
            return "Add calendar integration feature"
        if "collaboration" in text.lower() or "team" in text.lower():
            return "Add real-time team collaboration"
        if "offline" in text.lower():
            return "Add full offline mode with sync"
        if "watch" in text.lower():
            return "Add Apple Watch companion app"
        if "theme" in text.lower():
            return "Add custom color themes"
        if "widget" in text.lower():
            return "Add home screen widget support"
        if "reminder" in text.lower() or "snooze" in text.lower():
            return "Add snooze and reminder feature"
        return "Evaluate and plan requested feature"
    if category == "Complaint":
        if "price" in text.lower() or "subscription" in text.lower() or "refund" in text.lower():
            return "Review pricing and refund policy"
        if "slow" in text.lower():
            return "Investigate and fix performance issues"
        if "support" in text.lower():
            return "Improve customer support response time"
        if "ads" in text.lower():
            return "Review ad frequency in free tier"
        if "storage" in text.lower():
            return "Reduce app storage footprint"
        return "Review and address user complaint"
    if category == "Praise":
        return "Log positive user feedback"
    return "Review spam submission"

def make_technical_details(category: str, text: str) -> str:
    if category != "Bug":
        return ""
    details = []
    text_lower = text.lower()
    if "iphone" in text_lower:
        details.append("Platform: iOS")
    elif "samsung" in text_lower or "pixel" in text_lower or "oneplus" in text_lower or "android" in text_lower:
        details.append("Platform: Android")
    else:
        details.append("Platform: Unknown")
    for device in ["iPhone 15", "iPhone 14", "iPhone 13", "iPhone 12", "Samsung Galaxy S23",
                   "Samsung Galaxy S22", "Samsung Galaxy S21", "Samsung Galaxy A52",
                   "Pixel 7a", "Pixel 7", "Pixel 6a", "OnePlus 10 Pro"]:
        if device.lower() in text_lower:
            details.append(f"Device: {device}")
            break
    else:
        details.append("Device: Unknown")
    for os_ver in ["iOS 17.4", "iOS 17.1", "iOS 16.6", "iOS 16.5", "iOS 16.4",
                   "Android 14", "Android 13", "Android 12"]:
        if os_ver.lower() in text_lower:
            details.append(f"OS: {os_ver}")
            break
    else:
        details.append("OS: Unknown")
    for ver in VERSIONS:
        if ver in text:
            details.append(f"App Version: {ver}")
            break
    else:
        details.append("App Version: Unknown")
    details.append("Steps to reproduce available in feedback text.")
    return " | ".join(details)


CLASS_FIELDS = ["source_id", "source_type", "category", "priority", "technical_details", "suggested_title"]
class_rows = []

for r in review_rows:
    category = r["_category"]
    text = r["review_text"]
    class_rows.append({
        "source_id": r["review_id"],
        "source_type": "review",
        "category": category,
        "priority": guess_priority(category, text),
        "technical_details": make_technical_details(category, text),
        "suggested_title": make_title(category, text),
    })

for r in email_rows:
    category = r["_category"]
    text = r["subject"] + " " + r["body"]
    class_rows.append({
        "source_id": r["email_id"],
        "source_type": "email",
        "category": category,
        "priority": guess_priority(category, text),
        "technical_details": make_technical_details(category, text),
        "suggested_title": make_title(category, text),
    })

class_path = os.path.join(BASE_DIR, "expected_classifications.csv")
with open(class_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=CLASS_FIELDS)
    writer.writeheader()
    writer.writerows(class_rows)

print(f"✓ Written {len(class_rows)} classifications → {class_path}")
print(f"\nSummary:")
from collections import Counter
cats = Counter(r["category"] for r in class_rows)
for cat, cnt in sorted(cats.items()):
    print(f"  {cat}: {cnt}")
