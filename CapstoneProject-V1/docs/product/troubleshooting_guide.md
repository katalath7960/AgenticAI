# Troubleshooting Guide — FlowTask Support Team

This guide maps common user-reported symptoms to known root causes
and resolution steps. Use it when triaging support tickets.

---

## Login & Authentication

### Symptom: Spinner appears then disappears without logging in
**Likely cause:** Token refresh race condition (KI-003) introduced in v3.0.1.
**Affected:** Android 13, Samsung Galaxy S22, app v3.0.1–3.0.5.
**Resolution:**
1. Ask user to force-close the app and clear app cache (Settings → Apps → FlowTask → Clear Cache).
2. Retry login. Usually resolves in 2–3 attempts.
3. If unresolved after 5 attempts, escalate to engineering (tag: `login-race-condition`).

### Symptom: 2FA SMS code never arrives
**Likely cause:** SMS delivery failure via Twilio on certain carrier networks (KI-002). Affects T-Mobile MVNOs and some prepaid carriers.
**Affected:** Android 12+, app v3.0.5+.
**Resolution:**
1. Ask user to check spam SMS folder.
2. Ask user to tap "Resend Code" up to 3 times with 30-second waits.
3. If still failing: advise user to temporarily disable 2FA (Settings → Security → Two-Factor Auth → Disable), log in, then re-enable.
4. Escalate to engineering if >3 users on same carrier report the issue simultaneously.

### Symptom: "Invalid credentials" even with correct password
**Likely cause:** Account may be locked after 5 failed login attempts. Lockout lasts 15 minutes.
**Resolution:** Advise user to wait 15 minutes or use password reset flow.

---

## Data & Sync

### Symptom: History/tasks appear empty after updating to v3.0.5
**Likely cause:** Data loss bug (KI-001). Data exists in backend but pagination cursor is corrupted.
**Affected:** Android 14 (Pixel 7, Samsung Galaxy S23), app v3.0.5.
**Resolution:**
1. Confirm by checking backend admin panel — if tasks exist server-side, this is KI-001.
2. Engineering can run the cursor reset script for the affected account.
3. Do NOT ask user to reinstall — this will not recover data.
4. Tag ticket: `KI-001-data-loss`. SLA: respond within 2 hours.

### Symptom: Changes on phone don't appear on tablet (or vice versa)
**Likely cause:** WebSocket sync failure — secondary device connection dropped silently (KI-005).
**Affected:** iOS 16.6 + iPadOS 16.6 same account, app v3.0.5.
**Resolution:**
1. Ask user to pull-to-refresh on the device not showing changes.
2. If still not syncing: force-close and reopen the app on the secondary device.
3. If persists after force-close: ask user to sign out and sign back in on the secondary device.

### Symptom: Search returns no results for items that clearly exist
**Likely cause:** Search index staleness after sync conflict (KI-007).
**Affected:** All platforms, app v3.0.5+.
**Resolution:**
1. Ask user to wait 60 seconds and try again.
2. If still failing after 60 seconds: ask user to sign out and back in (triggers full index rebuild on login).
3. Escalate if affecting >10 users — may indicate index service outage.

---

## Crashes & Freezes

### Symptom: App crashes immediately on opening (startup crash)
**Likely cause:** Corrupted local database after incomplete migration.
**Resolution:**
1. Ask for device model, OS version, and app version.
2. Ask user to try: Settings → Apps → FlowTask → Clear Data (WARNING: clears local cache, not cloud data — reassure user data is safe in cloud).
3. Reinstall the app.
4. If crash persists after reinstall: collect crash log from device and escalate to engineering.

### Symptom: App crashes when opening Settings → Account Details
**Likely cause:** Profile load crash (matches KI pattern for iPhone 14/15, iOS 16.5–17.4, v3.0.1–3.1.0).
**Resolution:**
1. Confirm device is iPhone 14 or iPhone 15 on iOS 16.5+ — this is a known targeted crash.
2. Workaround: access account settings via the web app at app.flowtask.io.
3. Tag ticket: `profile-crash-ios`. Fix targeted for v3.1.1.

### Symptom: App freezes during fast scrolling on Dashboard
**Likely cause:** RecyclerView layout crash on Android 14 (KI-006).
**Affected:** Android 14, Samsung Galaxy S23, Pixel 8.
**Resolution:**
1. Advise user to scroll slowly or use search/filter to find items.
2. Fix targeted for v3.2.0. Tag: `android14-scroll-freeze`.

---

## Notifications

### Symptom: No push notifications after iOS 17 update
**Likely cause:** APNs token not re-registered after app update (KI-004).
**Affected:** iPhone 14 Pro, iPhone 15 on iOS 17.0–17.4, app v3.1.0.
**Resolution:**
1. Ask user: Settings (iOS) → Notifications → FlowTask → toggle off, wait 5 seconds, toggle back on.
2. Force-close and reopen FlowTask.
3. If still not working: uninstall and reinstall FlowTask. (Safe — data is in cloud.)
4. Tag: `ios17-apns-token`. Fix in v3.1.1.

---

## Performance

### Symptom: App very slow, phone getting hot, battery draining fast
**Likely cause:** Background refresh interval regression — set to 30 seconds instead of 15 minutes (KI-008).
**Affected:** iPhone 15, iOS 17.x, app v3.1.0.
**Resolution:**
1. Workaround: iOS Settings → General → Background App Refresh → FlowTask → Off.
2. Fix in v3.1.1. Advise user to update when available.

### Symptom: Dashboard takes 8–10 seconds to load
**Likely cause:** General performance regression (no specific KI). Could also be slow network.
**Resolution:**
1. Ask user to check network connection quality.
2. Ask user to close and reopen the app (clears memory cache).
3. If affecting >5 users simultaneously: check status page — may indicate backend latency incident.

---

## File Attachments

### Symptom: App crashes when trying to attach a large file
**Likely cause:** Memory pressure during upload (KI-009).
**Affected:** iPhone 13 Pro and older (<3GB RAM), files >10MB.
**Resolution:**
1. Ask user to compress the file before attaching.
2. Alternative: use the web app (app.flowtask.io) for large file uploads — no size limit on web.
3. Tag: `large-file-upload-crash`.

---

## Billing & Subscriptions

### Symptom: Charged after cancelling subscription
**Policy:** Annual subscriptions are non-refundable. Monthly subscriptions stop at end of billing period.
**Resolution:**
1. Verify cancellation date in admin panel.
2. If cancellation was processed before the renewal date, issue a full refund for the incorrectly charged period.
3. Escalate billing disputes >$50 to finance team.

### Symptom: "Storage limit reached" on Premium plan
**Resolution:**
1. Confirm user is on Premium plan (1GB file storage limit).
2. Ask user to go to Settings → Storage → Review Attachments to delete unused files.
3. If user believes the count is incorrect, escalate to engineering (may be a quota calculation bug).

---

## Escalation Matrix

| Severity | Issue Type | Response SLA | Escalation Path |
|----------|------------|-------------|----------------|
| Critical | Data loss, account locked out | 2 hours | → Engineering on-call |
| High | Login failure, sync broken | 4 hours | → Engineering team |
| Medium | Feature broken, performance | 24 hours | → Product + Engineering |
| Low | Feature request, cosmetic | 72 hours | → Product backlog |
