# Feature Catalog — FlowTask v3.1.0

## Authentication & Account

### Login / Sign-Up
- Email + password authentication
- Google OAuth (iOS and Android)
- Apple Sign-In (iOS only)
- **Two-Factor Authentication (2FA):** SMS-based OTP; introduced in v3.0.0
- Password reset via email link
- **Known issue:** 2FA SMS delivery delays reported on some carriers after v3.0.5

### Account Management
- Profile: display name, avatar, timezone
- Connected accounts (Google, Apple)
- Subscription management (upgrade/downgrade/cancel)
- Data export (JSON format; CSV export is a requested feature)

## Task Management

### Tasks
- Create, edit, delete tasks
- Title (required), description (optional, markdown supported)
- Due date and time with timezone support
- Priority levels: Critical, High, Medium, Low
- Status: Open, In Progress, Done, Archived
- Recurring tasks: daily, weekly, monthly, custom intervals
- Sub-tasks (up to 3 levels deep)
- **Tags:** free-form labels for filtering

### Projects
- Group tasks into projects
- Project colour and icon
- Project-level progress bar (% tasks done)
- Archive projects

### Views
- **List view:** default; tasks sorted by due date
- **Board view:** Kanban-style columns by status
- **Calendar view:** NOT YET IMPLEMENTED — frequently requested feature
- **Today view:** tasks due today + overdue

## Notes
- Rich text editor (bold, italic, lists, headings, code blocks)
- Attach files to notes (Free: 5MB/file, 50MB total; Premium: 100MB/file, 1GB total)
- Link notes to tasks
- Note history (Premium only)

## Search
- Full-text search across tasks and notes
- Filter by: project, tag, due date range, priority, status
- **Known issue:** Search index rebuild required after large bulk imports; search may return stale results for up to 60 seconds after a sync conflict resolution (introduced v3.0.5)

## Sync & Offline

### Cloud Sync
- Real-time sync via WebSocket when online
- Conflict resolution: last-write-wins with conflict log
- Sync status indicator in toolbar (green = synced, yellow = syncing, red = error)

### Offline Mode
- Full read access when offline
- Write operations queued locally and synced on reconnection
- **Known issue:** Offline queue occasionally fails to flush after network reconnection on Android 14 (v3.0.5+); workaround is to force-close and reopen the app

## Notifications
- Push notifications for: task due reminders, overdue alerts, shared task updates
- Notification settings: per-category enable/disable, quiet hours
- **Known issue:** iOS 17+ push notifications fail to register after app update if the user has not re-opened notification permission prompt (v3.1.0)

## Analytics Dashboard (Premium)
- Tasks completed per week/month
- Overdue task rate
- Average task completion time
- Project progress over time
- **Known issue:** Analytics page fails to load for accounts with >5,000 tasks — returns "Data unavailable" error (introduced v3.0.1)

## File Attachments
- Attach files to tasks and notes
- Supported types: PDF, images (JPG, PNG, GIF), Office documents, zip
- Preview in-app for images and PDFs
- **Known issue:** File upload crashes for files >10MB on iOS devices with <2GB RAM (iPhone 12 Mini and older) — v3.0.1

## Team Collaboration (Team tier)
- Invite team members by email
- Assign tasks to team members
- Real-time presence indicators
- Comment threads on tasks
- **NOT YET IMPLEMENTED for lower tiers:** Real-time collaborative editing — requested by enterprise prospects

## Home Screen Widget
- Shows today's tasks count and next due task
- Tap to open app at Today view
- **Known issue:** Widget addition crashes the launcher on Android 14 (v3.1.0) — under investigation

## Accessibility
- VoiceOver (iOS) and TalkBack (Android) fully supported
- Dynamic Type / font scaling
- High contrast mode
- Keyboard navigation on iPad

## Planned Features (Roadmap Q2-Q3 2024)
- Dark mode (in development, targeting v3.2.0)
- Calendar view integration (Google Calendar sync)
- Biometric login (Face ID / Touch ID / Fingerprint)
- PDF export
- Apple Watch companion app
- Custom themes / accent colours
