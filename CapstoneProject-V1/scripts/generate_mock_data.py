"""
scripts/generate_mock_data.py
Generates all three input CSV files for the Feedback Intelligence pipeline:

  data/input/app_store_reviews.csv        (50 rows)
  data/input/support_emails.csv           (30 rows)
  data/input/expected_classifications.csv (80 rows)

Run: python scripts/generate_mock_data.py
"""
from __future__ import annotations

import csv
import os
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "data" / "input"
INPUT_DIR.mkdir(parents=True, exist_ok=True)

NOW = datetime.now()
VERSIONS = ["2.1.3", "3.0.1", "3.1.0", "3.0.5"]
PLATFORMS = ["Google Play", "App Store"]
USERNAMES = [
    "alice_m", "bob_j", "carol_k", "dave_r", "eve_s", "frank_t",
    "grace_l", "henry_w", "iris_p", "jake_n", "karen_o", "leo_b",
    "mia_c", "noah_d", "olivia_f", "peter_g", "quinn_h", "rachel_i",
    "sam_q", "tina_u",
]
DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "company.com", "work.io"]


def iso_date(days_back: int = 90) -> str:
    return (NOW - timedelta(days=random.randint(0, days_back))).strftime("%Y-%m-%d")


def iso_ts(days_back: int = 90) -> str:
    delta = timedelta(days=random.randint(0, days_back),
                      hours=random.randint(0, 23), minutes=random.randint(0, 59))
    return (NOW - delta).strftime("%Y-%m-%dT%H:%M:%S")


def rnd_email() -> str:
    return f"{random.choice(USERNAMES)}@{random.choice(DOMAINS)}"


# ─────────────────────────────────────────────────────────────────────────────
# Source data
# ─────────────────────────────────────────────────────────────────────────────

_BUG_REVIEWS = [
    (1, "App crashes every time I open my profile since the 3.0.1 update. "
        "Steps: 1) Open app 2) Tap Profile icon 3) App freezes and closes. "
        "iPhone 14, iOS 16.5. Very frustrating!"),
    (1, "Cannot login after updating to v3.1.0. Enter credentials, spinner spins forever. "
        "Tried uninstall/reinstall — still broken. Samsung Galaxy S22, Android 13."),
    (1, "Data sync completely broken. Notes not syncing between phone and iPad since 3.0.5. "
        "Losing important work data. This is critical."),
    (2, "App freezes on the home screen after about 30 seconds. Must force-close every time. "
        "Pixel 7, Android 14."),
    (1, "Crash on startup after latest update. Cleared cache — no help. "
        "Galaxy Note 20, Android 12. Steps: just open the app."),
    (2, "Push notifications stopped working on iOS 17. Missing important alerts. "
        "iPhone 15 Pro, app version 3.1.0."),
    (1, "Search returns no results even for exact matches. Broken since v3.0.5. "
        "OnePlus 10 Pro, Android 13."),
    (2, "Video upload fails with a generic error. Tried on WiFi and LTE. "
        "iPhone 13, iOS 16.6, app v3.0.1."),
    (1, "Offline mode broken — app shows 'No connection' even with full WiFi. "
        "Pixel 6a, Android 12, v3.0.5."),
    (2, "Battery drain extreme after 3.1.0 — phone loses 30%/hr with app in background. "
        "iPhone 15, iOS 17.1."),
    (1, "Cannot attach files in messages. Tap attachment icon — nothing happens. "
        "Galaxy S21, Android 13, v3.0.1."),
    (2, "App shows blank white screen after splash. Must reopen 3-4 times before it loads. "
        "iPhone 12 Mini, iOS 16.4, v3.1.0."),
]

_FEATURE_REVIEWS = [
    (4, "Please add dark mode! My eyes hurt at night. Would be a huge improvement."),
    (3, "Would love a calendar view for tasks. The list gets overwhelming."),
    (4, "Export data to PDF directly from the app would be fantastic."),
    (3, "Please add fingerprint/Face ID login. Typing password every time is annoying."),
    (4, "Widget support for the home screen showing daily summary would be great."),
    (3, "Multiple account support for switching between work and personal would be amazing."),
    (4, "Siri shortcut integration so I can open items hands-free, please!"),
    (3, "Bulk action feature to archive or delete multiple items would save time."),
    (4, "Reminder/snooze feature for tasks is desperately needed."),
    (4, "Collaboration features so teams can share and edit together would be perfect."),
]

_PRAISE_REVIEWS = [
    (5, "Absolutely love this app! Transformed how I manage daily tasks. Clean UI."),
    (5, "Best productivity app I've ever used. New dashboard in 3.1.0 is gorgeous."),
    (5, "Amazing update! Everything is snappy and the new design is really polished."),
    (4, "Great app overall. Really helped me stay organized. Minor bugs aside, 5-star quality."),
    (5, "Love the new features in 3.0.1. The team clearly listens to feedback. Keep it up!"),
    (4, "Excellent app. Support team very responsive. Had an issue resolved quickly."),
    (5, "Outstanding! Tried 10 other apps — this blows them all out of the water."),
    (4, "Really solid update. App feels much faster and onboarding is much improved."),
    (5, "Game changer for my workflow. Highly recommend to anyone in project management."),
    (4, "Impressive how much the team has improved the app over 6 months. Great work!"),
]

_COMPLAINT_REVIEWS = [
    (2, "Premium subscription price is way too high. Competitors offer more for less."),
    (1, "App is very slow to load. Takes 10+ seconds every time. Unacceptable."),
    (2, "Customer support takes days to respond. Had an issue two weeks with no resolution."),
    (2, "Onboarding is confusing and there are no tutorial videos."),
    (3, "Too many ads in the free tier. They interrupt my workflow constantly."),
    (1, "Cancelled subscription because app keeps losing my data. Completely unreliable."),
    (2, "App uses over 500MB storage on my phone. Ridiculous for what it does."),
    (2, "Interface is cluttered — too many menus buried inside menus."),
    (1, "No offline support whatsoever. Useless without internet."),
    (2, "Analytics section never loads properly. Always shows 'Data unavailable'."),
]

_SPAM_REVIEWS = [
    (5, "Download my free app at freeapps247.com! Best deals on premium apps!!!"),
    (1, "WORST APP EVER!!!! DO NOT DOWNLOAD!!! SCAM SCAM SCAM!!!!"),
    (5, "asdfghjkl this app is ok i guess lol whatever never mind forget it"),
    (3, "I am not a robot. This review is genuine. Buy crypto now at bit-invest.net"),
    (4, "Good app good app good app good app good app good app good app good"),
    (2, "jkjkjkjkjkjkjk nope nope nope 123456789 test test"),
    (5, "Follow me on Instagram @cooluser2024 for lifestyle tips! Great app too"),
    (1, "This review is for another app I accidentally downloaded. Wrong page."),
]

_EMAIL_DATA = [
    # ── Bugs (10 — all with full technical detail)
    {"subject": "App Crash Report — iPhone 15 iOS 17.4",
     "body": ("Hi Support,\n\nI'm experiencing repeated crashes on iPhone 15 running iOS 17.4, "
              "app version 3.1.0.\n\nSteps:\n1. Open app\n2. Go to Settings tab\n"
              "3. Tap 'Account Details'\n4. App crashes immediately\n\n"
              "Device: iPhone 15 | OS: iOS 17.4 | App: 3.1.0\n\nPlease fix ASAP.\nJohn"),
     "_cat": "Bug", "_pri": "High"},
    {"subject": "Login Issue Since v3.0.1 Update",
     "body": ("Hello,\n\nSince v3.0.1 I cannot log in. Enter credentials, spinner appears "
              "for 5 seconds then vanishes — not logged in.\n\n"
              "Device: Samsung Galaxy S22 | OS: Android 13 | App: 3.0.1\n\n"
              "Steps:\n1. Open app\n2. Enter valid credentials\n3. Tap Sign In\n"
              "4. Spinner vanishes — not logged in\n\nTried password reset — same issue."),
     "_cat": "Bug", "_pri": "High"},
    {"subject": "Data Loss Problem — Urgent",
     "body": ("URGENT — Lost 3 weeks of data after the 3.0.5 update. All notes/task history "
              "before March 2024 are gone. History tab shows empty state.\n\n"
              "Device: Google Pixel 7 | OS: Android 14 | App: 3.0.5\n\n"
              "Steps:\n1. Update to 3.0.5\n2. Open app\n3. Navigate to History\n"
              "4. All previous entries gone\n\nCritical — need that data for work."),
     "_cat": "Bug", "_pri": "Critical"},
    {"subject": "Notification Bug — Not Receiving Alerts",
     "body": ("Hi,\n\nPush notifications stopped working after iOS 17.1 upgrade.\n\n"
              "Device: iPhone 14 Pro | OS: iOS 17.1 | App: 3.1.0\n\n"
              "Steps:\n1. Enable notifications in app and iOS Settings\n"
              "2. Set reminder 5 minutes from now\n3. Wait — no notification arrives\n\n"
              "Tried toggling permissions. No improvement.\nSarah"),
     "_cat": "Bug", "_pri": "Medium"},
    {"subject": "Sync Failure Between iPad and iPhone",
     "body": ("Hello Support,\n\nData not syncing between iPhone and iPad. Create item on "
              "iPhone — never appears on iPad after 30 minutes.\n\n"
              "iPhone 13, iOS 16.6, App v3.0.5\niPad Pro, iPadOS 16.6, App v3.0.5\n\n"
              "Steps:\n1. Create task on iPhone\n2. Open iPad (same account)\n"
              "3. Task missing\n4. Pull to refresh — still missing\n\nBoth on same WiFi."),
     "_cat": "Bug", "_pri": "High"},
    {"subject": "App Freezes on Android 14 — Galaxy S23",
     "body": ("Hi,\n\nApp freezes completely on Galaxy S23 running Android 14.\n\n"
              "Device: Samsung Galaxy S23 | OS: Android 14 | App: 3.1.0\n\n"
              "Steps:\n1. Open app\n2. Go to Dashboard\n3. Scroll down rapidly\n"
              "4. App becomes unresponsive — must force-kill\n\nClearing cache does not help."),
     "_cat": "Bug", "_pri": "High"},
    {"subject": "Search Not Returning Results",
     "body": ("Hi,\n\nSearch completely broken. Type exact phrases that are in my notes — "
              "get zero results.\n\nDevice: OnePlus 10 Pro | OS: Android 13 | App: 3.0.5\n\n"
              "Steps:\n1. Navigate to Search\n2. Type 'meeting notes'\n"
              "3. Results: 'No items found' (I have 20 notes with that phrase)\n\nPlease help."),
     "_cat": "Bug", "_pri": "Medium"},
    {"subject": "Crash When Uploading Large Files",
     "body": ("Hello,\n\nApp crashes uploading files >10MB.\n\n"
              "Device: iPhone 13 Pro | OS: iOS 16.6 | App: 3.0.1\n\n"
              "Steps:\n1. Tap '+' to add attachment\n2. Select 15MB PDF from Files\n"
              "3. Upload progress bar appears\n4. At ~60% progress, app crashes\n\n"
              "Consistent across multiple files and network conditions.\nTom"),
     "_cat": "Bug", "_pri": "Medium"},
    {"subject": "Two-Factor Authentication Not Working",
     "body": ("Hi Support,\n\n2FA SMS codes not delivered. Cannot log in at all.\n\n"
              "Device: Samsung Galaxy A52 | OS: Android 12 | App: 3.0.5\n\n"
              "Steps:\n1. Open app\n2. Enter email + password\n"
              "3. 2FA screen appears — wait for SMS\n4. SMS never arrives (checked spam, "
              "tried resend 5×)\n\nThis is a blocker — cannot access account.\nDavid"),
     "_cat": "Bug", "_pri": "Critical"},
    {"subject": "Widget Crashes Home Screen",
     "body": ("Hello,\n\nHome screen widget crashes launcher when I try to add it.\n\n"
              "Device: Pixel 7a | OS: Android 14 | App: 3.1.0\n\n"
              "Steps:\n1. Long press home screen\n2. Select Widgets\n"
              "3. Find app widget\n4. Drag to home screen — launcher crashes\n\nEvery time."),
     "_cat": "Bug", "_pri": "Low"},
    # ── Feature Requests (8)
    {"subject": "Feature Request: Dark Mode Support",
     "body": ("Hello,\n\nI love the app but really need dark mode. Use it late at night "
              "and the bright white is hard on my eyes. Many apps have this now.\n\nLaura"),
     "_cat": "Feature Request", "_pri": "Medium"},
    {"subject": "Request: Export to PDF Functionality",
     "body": ("Hi Team,\n\nExporting task lists and notes as PDF directly from the app would "
              "be incredibly useful. I share progress reports with my manager and currently "
              "copy everything manually.\n\nA simple export button would save 30 mins/week."),
     "_cat": "Feature Request", "_pri": "Medium"},
    {"subject": "Suggestion: Biometric Login",
     "body": ("Hello,\n\nFace ID / fingerprint login support would improve daily usability. "
              "Typing my long password every time is inconvenient, especially on mobile.\nThanks"),
     "_cat": "Feature Request", "_pri": "Low"},
    {"subject": "Suggestion for Improvement: Calendar Integration",
     "body": ("Hi,\n\nCalendar integration (Google/Apple) would make this app a complete "
              "productivity solution. Currently switch between two apps to manage tasks and "
              "calendar. Even a read-only calendar view would be great.\n\nBest regards"),
     "_cat": "Feature Request", "_pri": "Medium"},
    {"subject": "Feature Request: Team Collaboration",
     "body": ("Dear Team,\n\nOur company is evaluating the app for enterprise use. One key "
              "missing feature is real-time collaboration — multiple users editing the same "
              "project simultaneously. This is a deal-breaker for us.\n\nEnterprise Team"),
     "_cat": "Feature Request", "_pri": "High"},
    {"subject": "Feedback: Offline Mode Would Be Great",
     "body": ("Hello,\n\nI travel frequently and often have no internet. Full offline mode "
              "with sync when back online would make this perfect for frequent travelers.\n\nThanks"),
     "_cat": "Feature Request", "_pri": "Medium"},
    {"subject": "Request: Apple Watch App",
     "body": ("Hello,\n\nAn Apple Watch companion app would be a great addition. Checking "
              "and ticking off tasks from my wrist would save a lot of time.\n\nThank you"),
     "_cat": "Feature Request", "_pri": "Low"},
    {"subject": "Suggestion: Custom Themes",
     "body": ("Hi Team,\n\nCustom color themes beyond light/dark would let users personalise "
              "the experience. Custom accent colors would be a nice touch.\n\nKeep up the work!"),
     "_cat": "Feature Request", "_pri": "Low"},
    # ── Complaints (6)
    {"subject": "Subscription Price Too High",
     "body": ("Hello,\n\nThe recent price increase to $15/month is too much. Competitors "
              "charge $5-8/month for more features. Considering cancelling.\n\nThanks"),
     "_cat": "Complaint", "_pri": "Medium"},
    {"subject": "Very Slow App Performance",
     "body": ("Hi,\n\nThe app has become extremely slow. Dashboard takes 8-10 seconds to load, "
              "switching tabs takes 3-4 seconds. Considering switching to a competitor.\n\nFrustrated"),
     "_cat": "Complaint", "_pri": "Medium"},
    {"subject": "Poor Customer Support Experience",
     "body": ("To Whom It May Concern,\n\nSubmitted a ticket 2 weeks ago about a billing issue "
              "and received only one automated response. I am a premium subscriber and this "
              "level of support is unacceptable.\n\nDisappointed"),
     "_cat": "Complaint", "_pri": "High"},
    {"subject": "Too Many Ads in Free Tier",
     "body": ("Hello,\n\nAds appear every 2-3 actions in the free tier. This makes the app "
              "nearly unusable without paying. Excessive.\n\nRegards"),
     "_cat": "Complaint", "_pri": "Low"},
    {"subject": "App Uses Too Much Storage",
     "body": ("Hi,\n\nThe app uses 600MB on my phone. Far too much. Please add a 'Clear Cache' "
              "option in settings or reduce the storage footprint.\n\nThanks"),
     "_cat": "Complaint", "_pri": "Low"},
    {"subject": "No Refund for Cancelled Subscription",
     "body": ("Hello,\n\nI cancelled my annual subscription mid-year and was told I would not "
              "receive a refund for unused months. This is against consumer protection rules "
              "in my country. I expect a pro-rata refund.\n\nRegards"),
     "_cat": "Complaint", "_pri": "High"},
    # ── Praise (6)
    {"subject": "Love the New Dashboard Design!",
     "body": ("Hi Team,\n\nThe new dashboard in v3.1.0 is absolutely beautiful. The redesign "
              "made everything so much more intuitive. Great work by your design team!\n\nThanks!"),
     "_cat": "Praise", "_pri": "Low"},
    {"subject": "Outstanding App — Highly Recommend",
     "body": ("Hello,\n\nBeen using the app for 18 months and it keeps getting better. "
              "v3.0.1 was especially impressive. Performance improvements are noticeable.\n\nBest"),
     "_cat": "Praise", "_pri": "Low"},
    {"subject": "Great Customer Support Experience",
     "body": ("Hi,\n\nHad a billing issue last week and your support team resolved it within "
              "2 hours. Exceptional service. The rep (Alex) was courteous and efficient.\n\nKind regards"),
     "_cat": "Praise", "_pri": "Low"},
    {"subject": "App Has Transformed My Productivity",
     "body": ("Hi,\n\nThis app has genuinely changed how I work. Used to miss deadlines and "
              "feel overwhelmed. After 6 months with your app, I'm on top of everything.\n\nThank you!"),
     "_cat": "Praise", "_pri": "Low"},
    {"subject": "Impressed by the Accessibility Features",
     "body": ("Hello Team,\n\nAs someone with low vision, thank you for excellent accessibility "
              "support. Dynamic text sizing and VoiceOver work flawlessly.\n\nKeep it up!"),
     "_cat": "Praise", "_pri": "Low"},
    {"subject": "Quick Question About Storage Limits",
     "body": ("Hi,\n\nI'm a free user — what is the storage limit before I need to upgrade? "
              "Can't find this information in the app. Also, love the app — very well designed!\nThanks"),
     "_cat": "Complaint", "_pri": "Low"},
]


# ─────────────────────────────────────────────────────────────────────────────
# Build reviews
# ─────────────────────────────────────────────────────────────────────────────
review_rows: list[dict] = []
_rev_id = 1

_cat_labels = (
    ["Bug"] * len(_BUG_REVIEWS)
    + ["Feature Request"] * len(_FEATURE_REVIEWS)
    + ["Praise"] * len(_PRAISE_REVIEWS)
    + ["Complaint"] * len(_COMPLAINT_REVIEWS)
    + ["Spam"] * len(_SPAM_REVIEWS)
)
for (rating, text), cat in zip(
    _BUG_REVIEWS + _FEATURE_REVIEWS + _PRAISE_REVIEWS + _COMPLAINT_REVIEWS + _SPAM_REVIEWS,
    _cat_labels,
):
    review_rows.append({
        "review_id": f"REV-{_rev_id:04d}",
        "platform": "",
        "rating": rating,
        "review_text": text,
        "user_name": random.choice(USERNAMES),
        "date": iso_date(),
        "app_version": random.choice(VERSIONS),
        "_cat": cat,
    })
    _rev_id += 1

random.shuffle(review_rows)
for i, row in enumerate(review_rows):
    row["platform"] = "App Store" if i % 2 == 0 else "Google Play"

REV_FIELDS = ["review_id", "platform", "rating", "review_text", "user_name", "date", "app_version"]
_rev_cats = {r["review_id"]: r["_cat"] for r in review_rows}

reviews_path = INPUT_DIR / "app_store_reviews.csv"
with open(reviews_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=REV_FIELDS)
    w.writeheader()
    for r in review_rows:
        w.writerow({k: r[k] for k in REV_FIELDS})

print(f"Written {len(review_rows)} reviews -> {reviews_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Build emails
# ─────────────────────────────────────────────────────────────────────────────
email_rows: list[dict] = []
for i, ed in enumerate(sorted(_EMAIL_DATA, key=lambda x: x["_cat"])):
    email_rows.append({
        "email_id": f"EML-{i+1:04d}",
        "subject": ed["subject"],
        "body": ed["body"],
        "sender_email": rnd_email(),
        "timestamp": iso_ts(),
        "priority": ed["_pri"] if (i % 3 != 2) else "",   # ~33% blank
        "_cat": ed["_cat"],
        "_pri": ed["_pri"],
    })

EML_FIELDS = ["email_id", "subject", "body", "sender_email", "timestamp", "priority"]
_eml_cats = {r["email_id"]: (r["_cat"], r["_pri"]) for r in email_rows}

emails_path = INPUT_DIR / "support_emails.csv"
with open(emails_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=EML_FIELDS)
    w.writeheader()
    for r in email_rows:
        w.writerow({k: r[k] for k in EML_FIELDS})

print(f"Written {len(email_rows)} emails  -> {emails_path}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers for expected classifications
# ─────────────────────────────────────────────────────────────────────────────

def _priority(category: str, text: str) -> str:
    t = text.lower()
    if category == "Bug":
        if any(k in t for k in ["crash", "data loss", "lost", "unable", "frozen", "urgent", "critical", "blocker", "2fa"]):
            return "Critical"
        if any(k in t for k in ["login", "sign in", "sync", "freeze", "broken", "cannot", "not working"]):
            return "High"
        if any(k in t for k in ["notification", "search", "upload", "battery", "slow", "blank", "widget"]):
            return "Medium"
        return "Low"
    if category == "Complaint":
        if any(k in t for k in ["refund", "unacceptable", "critical"]):
            return "High"
        if any(k in t for k in ["support", "slow", "price"]):
            return "Medium"
        return "Low"
    if category == "Feature Request":
        if any(k in t for k in ["enterprise", "team", "deal-breaker", "collaboration"]):
            return "High"
        return "Medium"
    return "Low"


def _title(category: str, text: str) -> str:
    t = text.lower()
    if category == "Bug":
        if "crash" in t:             return "Fix app crash on affected screen"
        if "login" in t or "sign in" in t: return "Fix login failure after update"
        if "sync" in t or "data loss" in t: return "Fix data sync and loss issue"
        if "notification" in t:      return "Fix push notifications not delivered"
        if "search" in t:            return "Fix search returning no results"
        if "freeze" in t or "frozen" in t: return "Fix app freeze and unresponsiveness"
        if "upload" in t:            return "Fix file upload crash on large files"
        if "2fa" in t or "two-factor" in t: return "Fix 2FA SMS codes not delivered"
        if "widget" in t:            return "Fix widget crash on home screen"
        if "battery" in t:           return "Investigate battery drain regression"
        if "offline" in t:           return "Fix offline mode not working"
        if "attach" in t:            return "Fix file attachment not working"
        return "Investigate and fix reported bug"
    if category == "Feature Request":
        if "dark mode" in t:         return "Add dark mode to app settings"
        if "pdf" in t or "export" in t: return "Add PDF export functionality"
        if "biometric" in t or "face id" in t or "fingerprint" in t: return "Add biometric login support"
        if "calendar" in t:          return "Add calendar integration feature"
        if "collaboration" in t or "team" in t: return "Add real-time team collaboration"
        if "offline" in t:           return "Add full offline mode with sync"
        if "watch" in t:             return "Add Apple Watch companion app"
        if "theme" in t:             return "Add custom color themes"
        if "widget" in t:            return "Add home screen widget support"
        if "reminder" in t or "snooze" in t: return "Add snooze and reminder feature"
        return "Evaluate and plan requested feature"
    if category == "Complaint":
        if "price" in t or "subscription" in t or "refund" in t: return "Review pricing and refund policy"
        if "slow" in t:              return "Investigate and fix performance issues"
        if "support" in t:           return "Improve customer support response time"
        if "ads" in t:               return "Review ad frequency in free tier"
        if "storage" in t:           return "Reduce app storage footprint"
        return "Review and address user complaint"
    if category == "Praise":         return "Log positive user feedback"
    return "Review spam submission"


def _tech_details(category: str, text: str) -> str:
    if category != "Bug":
        return ""
    parts = []
    t = text.lower()
    if "iphone" in t or "ios" in t:
        parts.append("Platform: iOS")
    elif any(k in t for k in ["samsung", "pixel", "oneplus", "android", "galaxy"]):
        parts.append("Platform: Android")
    else:
        parts.append("Platform: Unknown")
    for d in ["iPhone 15 Pro", "iPhone 15", "iPhone 14 Pro", "iPhone 14",
              "iPhone 13 Pro", "iPhone 13", "iPhone 12 Mini", "iPhone 12",
              "Samsung Galaxy S23", "Samsung Galaxy S22", "Samsung Galaxy S21",
              "Samsung Galaxy A52", "Samsung Galaxy Note 20",
              "Pixel 7a", "Pixel 7", "Pixel 6a", "OnePlus 10 Pro"]:
        if d.lower() in t:
            parts.append(f"Device: {d}")
            break
    else:
        parts.append("Device: Unknown")
    for os in ["iOS 17.4", "iOS 17.1", "iOS 16.6", "iOS 16.5", "iOS 16.4",
               "Android 14", "Android 13", "Android 12"]:
        if os.lower() in t:
            parts.append(f"OS: {os}")
            break
    else:
        parts.append("OS: Unknown")
    for v in VERSIONS:
        if v in text:
            parts.append(f"App: {v}")
            break
    else:
        parts.append("App: Unknown")
    parts.append("Steps: available in feedback text")
    return " | ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Build expected classifications
# ─────────────────────────────────────────────────────────────────────────────
cls_rows: list[dict] = []

for r in review_rows:
    cat = r["_cat"]
    text = r["review_text"]
    cls_rows.append({
        "source_id": r["review_id"],
        "source_type": "review",
        "category": cat,
        "priority": _priority(cat, text),
        "technical_details": _tech_details(cat, text),
        "suggested_title": _title(cat, text),
    })

for r in email_rows:
    cat = r["_cat"]
    text = r["subject"] + " " + r["body"]
    cls_rows.append({
        "source_id": r["email_id"],
        "source_type": "email",
        "category": cat,
        "priority": _priority(cat, text),
        "technical_details": _tech_details(cat, text),
        "suggested_title": _title(cat, text),
    })

CLS_FIELDS = ["source_id", "source_type", "category", "priority", "technical_details", "suggested_title"]
cls_path = INPUT_DIR / "expected_classifications.csv"
with open(cls_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=CLS_FIELDS)
    w.writeheader()
    w.writerows(cls_rows)

print(f"Written {len(cls_rows)} classifications -> {cls_path}")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\nCategory breakdown:")
counts = Counter(r["category"] for r in cls_rows)
for cat, n in sorted(counts.items()):
    print(f"  {cat:<20} {n}")
print(f"  {'TOTAL':<20} {sum(counts.values())}")

# Validation
import pandas as pd  # noqa: E402
r_df = pd.read_csv(reviews_path)
e_df = pd.read_csv(emails_path)
c_df = pd.read_csv(cls_path)

assert r_df["review_id"].nunique() == len(r_df), "Duplicate review_ids!"
assert e_df["email_id"].nunique() == len(e_df), "Duplicate email_ids!"
assert len(c_df) == len(r_df) + len(e_df), "Classification row count mismatch!"
assert c_df["category"].isna().sum() == 0, "Missing categories!"
assert c_df["priority"].isna().sum() == 0, "Missing priorities!"
bug_cls = c_df[c_df["category"] == "Bug"]
assert (bug_cls["technical_details"] == "").sum() == 0, "Bug rows missing technical_details!"
print("\nAll validations passed.")
