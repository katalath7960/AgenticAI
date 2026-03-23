# Known Issues — FlowTask

## Critical (P0) — Active Incidents

### KI-001 · Data Loss After v3.0.5 Update
- **Severity:** Critical
- **Affected versions:** 3.0.5, 3.1.0
- **Affected platforms:** Android 14 (Pixel 7, Samsung S23)
- **Description:** Task and note history before the update date disappears from the
  History tab after upgrading to 3.0.5. Data exists in the backend but is not
  displayed due to a pagination cursor bug in the migration script.
- **Workaround:** Contact support@flowtask.io — engineering can restore the view
  manually per account.
- **Fix target:** v3.1.1 (in testing)

### KI-002 · 2FA SMS Codes Not Delivered
- **Severity:** Critical
- **Affected versions:** 3.0.5, 3.1.0
- **Affected platforms:** Android 12+ (Samsung Galaxy A-series, some Pixel devices)
- **Description:** SMS OTP codes are not delivered when 2FA is enabled. The issue
  is intermittent on some carriers and consistent on others (T-Mobile MVNO networks).
  Affects ~3% of 2FA users.
- **Workaround:** Disable 2FA in account settings, log in, then re-enable 2FA.
- **Fix target:** v3.1.1 (SMS provider fallback in staging)

## High (P1) — Active Bugs

### KI-003 · Login Failure After v3.0.1 Update
- **Severity:** High
- **Affected versions:** 3.0.1, 3.0.5
- **Affected platforms:** Android 13 (Samsung Galaxy S22)
- **Description:** Sign-in spinner dismisses without completing authentication.
  Caused by a race condition in the token refresh handler introduced in v3.0.1.
- **Workaround:** Force-close app, clear app cache, and retry. Usually resolves
  after 2-3 attempts.
- **Fix target:** v3.1.1

### KI-004 · Push Notifications Not Working on iOS 17
- **Severity:** High
- **Affected versions:** 3.1.0
- **Affected platforms:** iOS 17.0, 17.1, 17.4 (iPhone 14 Pro, iPhone 15)
- **Description:** After updating to iOS 17, the APNs device token is not
  re-registered because the app does not request notification permission again.
  Users miss all task reminders and due-date alerts.
- **Workaround:** Go to iOS Settings → Notifications → FlowTask → toggle off and
  back on, then reopen the app.
- **Fix target:** v3.1.1

### KI-005 · Cross-Device Sync Failure (iOS ↔ iPad)
- **Severity:** High
- **Affected versions:** 3.0.5
- **Affected platforms:** iOS 16.6 + iPadOS 16.6 same account
- **Description:** Tasks created on iPhone do not appear on iPad. The WebSocket
  connection for the secondary device drops silently and is not re-established.
- **Workaround:** Pull-to-refresh on the iPad after creating a task on iPhone.
  If this doesn't work, force-close and reopen on iPad.
- **Fix target:** v3.1.1

### KI-006 · App Freezes on Android 14 During Fast Scroll
- **Severity:** High
- **Affected versions:** 3.1.0
- **Affected platforms:** Android 14 (Samsung Galaxy S23, Pixel 8)
- **Description:** Rapid scrolling on the Dashboard triggers an uncaught
  RecyclerView layout exception that freezes the UI thread.
- **Workaround:** Scroll slowly or use the search/filter to navigate to items.
- **Fix target:** v3.2.0

## Medium (P2) — Active Bugs

### KI-007 · Search Index Stale After Sync Conflict
- **Severity:** Medium
- **Affected versions:** 3.0.5+
- **Description:** After a sync conflict resolution the full-text search index is
  not immediately updated. Search may return no results for up to 60 seconds.
- **Workaround:** Wait 60 seconds and retry search.
- **Fix target:** v3.2.0

### KI-008 · Battery Drain Regression in v3.1.0
- **Severity:** Medium
- **Affected versions:** 3.1.0
- **Affected platforms:** iOS 17.x (iPhone 15)
- **Description:** Background refresh interval was accidentally reduced from
  15 minutes to 30 seconds in v3.1.0, causing excessive battery drain.
- **Workaround:** Disable background app refresh in iOS Settings for FlowTask.
- **Fix target:** v3.1.1

### KI-009 · File Upload Crash for Files >10MB
- **Severity:** Medium
- **Affected versions:** 3.0.1+
- **Affected platforms:** iOS (iPhone 13 Pro and older with <3GB RAM)
- **Description:** Memory pressure during multipart upload causes the app to be
  terminated by iOS when attaching files larger than ~10MB.
- **Workaround:** Compress files before attaching, or use the web app at
  app.flowtask.io for large file uploads.
- **Fix target:** v3.2.0

### KI-010 · Analytics "Data Unavailable" for Large Accounts
- **Severity:** Medium
- **Affected versions:** 3.0.1+
- **Description:** Accounts with >5,000 tasks timeout on the analytics query,
  displaying "Data unavailable" on the Analytics page.
- **Workaround:** None available. Engineering is rewriting the query with
  pagination.
- **Fix target:** v3.2.0

## Low (P3) — Known Issues

### KI-011 · Home Screen Widget Crashes Launcher on Android 14
- **Severity:** Low
- **Affected versions:** 3.1.0
- **Affected platforms:** Android 14 (Pixel 7a, Samsung Galaxy S24)
- **Description:** Adding the FlowTask widget to the home screen causes the
  Android launcher to crash. Under investigation — likely a Glance API
  compatibility issue.
- **Workaround:** Do not use the widget on Android 14.
- **Fix target:** v3.2.0

### KI-012 · Attachment Button Unresponsive in Messages
- **Severity:** Low
- **Affected versions:** 3.0.1
- **Affected platforms:** Android 13
- **Description:** Tapping the attachment icon in task comments has no effect.
  The file picker intent is not launched.
- **Workaround:** Use the note attachment feature as an alternative.
- **Fix target:** v3.2.0
