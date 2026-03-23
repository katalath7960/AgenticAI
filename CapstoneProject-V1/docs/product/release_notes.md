# Release Notes — FlowTask

---

## v3.1.0 (2024-03-01) — "Polished"

### New Features
- **Android 14 support** — tested on Pixel 8 and Samsung Galaxy S24
- **Home screen widget** — shows today's task count and next due task (iOS and Android)
  - ⚠️ Known issue: widget crashes launcher on Android 14 (KI-011) — fix in v3.1.1
- **UI polish pass** — updated colour palette, smoother animations, new onboarding flow
- **Improved search UI** — search suggestions and recent queries

### Improvements
- Sub-task drag-and-drop reordering
- Faster app startup time (~40% improvement on mid-range Android)
- Reduced APK size by 12%

### Bug Fixes
- Fixed: Occasional duplicate task creation on poor network connections
- Fixed: Calendar permissions dialog shown repeatedly on iOS
- Fixed: Tags not searchable on Android

### Known Regressions (introduced in this release)
- **KI-004** Push notifications not re-registered after update on iOS 17 → fix in v3.1.1
- **KI-006** App freezes during fast scroll on Android 14 → fix in v3.2.0
- **KI-008** Battery drain on iPhone 15 (background refresh set to 30s) → fix in v3.1.1
- **KI-011** Widget crashes Android 14 launcher → fix in v3.2.0

---

## v3.0.5 (2024-01-20) — "Stability"

### New Features
- Offline mode improvements — write operations now queued and reliably flushed on reconnect
- Conflict resolution log — users can now see and resolve sync conflicts manually
- Bulk task operations — select multiple tasks to archive, delete, or change status

### Improvements
- Sync engine rewrite — reduced sync latency from ~2s to ~300ms average
- Search index now rebuilds incrementally (not full-rebuild on every sync)
- Reduced background data usage by 35%

### Bug Fixes
- Fixed: App would spin indefinitely if auth token expired during a sync
- Fixed: Recurring tasks sometimes creating extra instances at midnight UTC

### Known Regressions (introduced in this release)
- **KI-001** Data loss on Android 14 after upgrade (pagination cursor bug) → fix in v3.1.1
- **KI-002** 2FA SMS not delivered on some carriers → fix in v3.1.1
- **KI-005** WebSocket sync failure on secondary devices (iOS + iPad) → fix in v3.1.1
- **KI-007** Search index stale for up to 60s after conflict resolution → fix in v3.2.0

---

## v3.0.1 (2023-11-15) — "Analytics"

### New Features
- **Analytics Dashboard (Premium)** — task completion trends, overdue rates, project progress
  - ⚠️ Known issue: times out for accounts >5,000 tasks (KI-010)
- **File Attachments** — attach PDFs, images, and Office docs to tasks and notes
  - ⚠️ Known issue: crash on files >10MB on older iOS devices (KI-009)
- **Note linking** — link notes to tasks for context

### Improvements
- Task list performance improved for accounts with >500 tasks
- Markdown rendering in task descriptions

### Bug Fixes
- Fixed: "Today" view sometimes showing tomorrow's tasks after midnight
- Fixed: Google OAuth sometimes requiring re-authentication every session

### Known Regressions
- **KI-003** Login spinner dismisses without completing auth on Android 13 (Samsung S22) → fixed in v3.1.0 partial, full fix in v3.1.1
- **KI-012** Attachment button unresponsive in task comments on Android 13 → fix in v3.2.0

---

## v3.0.0 (2023-10-01) — "Relaunch"

### New Features
- Complete UI redesign (Material 3 on Android, iOS 17 design language on iOS)
- **Two-Factor Authentication (2FA)** via SMS
- New sync engine based on WebSocket + lamport timestamps
- Team collaboration features (Team tier): assign tasks, comment threads, presence

### Breaking Changes
- Minimum iOS: 15.0 (was 13.0)
- Minimum Android: 12 (was 9)
- Old sync format deprecated — users on v2.x required to update

### Migration Notes
- All user data automatically migrated on first login after update
- Local SQLite database on Android rebuilt on first launch (takes 5-30 seconds for large accounts)

---

## v2.1.3 (2023-06-12) — "Maintenance"

### Bug Fixes
- Fixed critical crash on iPad when rotating device while task editor is open
- Fixed memory leak in note editor
- Fixed: Tasks with emoji in title not syncing correctly
- Performance: Reduced memory footprint by 20% on Android

### Known Issues at EOL (superseded by v3.x)
- No offline write support (read-only offline)
- No 2FA
- Sync conflicts not handled gracefully (last-write-wins silently)

---

## Upcoming: v3.1.1 (Target: 2024-04-15)

**Fixes planned:**
- KI-001 Data loss after v3.0.5 (Android 14)
- KI-002 2FA SMS delivery on carrier networks
- KI-003 Login race condition (Android 13)
- KI-004 iOS 17 push notification re-registration
- KI-005 WebSocket sync failure (iOS + iPad)
- KI-008 Battery drain regression (iPhone 15)

## Upcoming: v3.2.0 (Target: 2024-Q3)

**Features planned:**
- Dark mode (feature flag currently at 10% beta rollout)
- Calendar view (Google Calendar + Apple Calendar integration)
- Biometric login (Face ID, Touch ID, Fingerprint)
- PDF export for notes and task lists
- Performance fix for accounts >5,000 tasks (KI-010)
