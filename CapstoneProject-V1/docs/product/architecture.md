# System Architecture — FlowTask

## Overview

FlowTask is a mobile-first productivity application with a REST + WebSocket
backend, native iOS and Android clients, and a web client. All clients sync
data through a central cloud API backed by PostgreSQL and Redis.

```
┌─────────────────────────────────────────────┐
│                  Clients                    │
│  iOS App (Swift)  │  Android App (Kotlin)   │
│  Web App (React)  │  Admin Panel (React)    │
└────────────┬────────────────────────────────┘
             │  HTTPS / WSS
┌────────────▼────────────────────────────────┐
│            API Gateway (AWS ALB)            │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│           Backend Services                  │
│  Auth Service  │  Task Service              │
│  Sync Service  │  Notification Service      │
│  Analytics     │  File Storage (S3)         │
└────────────┬────────────────────────────────┘
             │
┌────────────▼────────────────────────────────┐
│              Data Layer                     │
│  PostgreSQL (primary)  │  Redis (cache)     │
│  Elasticsearch (search) │  S3 (files)       │
└─────────────────────────────────────────────┘
```

## Core Services

### Auth Service
- Issues JWT access tokens (15-minute TTL) and refresh tokens (30-day TTL)
- Handles OAuth 2.0 flows for Google and Apple Sign-In
- Manages 2FA via Twilio SMS
- Endpoint: `POST /auth/login`, `POST /auth/refresh`, `POST /auth/2fa/verify`

### Task Service
- CRUD for tasks, sub-tasks, projects, tags
- Business logic for recurring task generation
- Endpoint prefix: `/api/v2/tasks`, `/api/v2/projects`

### Sync Service
- WebSocket server handling real-time sync (Socket.IO on Node.js)
- Conflict resolution: last-write-wins per field with server timestamp authority
- Offline queue: client queues mutations locally; flushes on reconnect
- Each device maintains a `sync_cursor` (lamport timestamp) for delta sync

### Notification Service
- APNs (Apple Push Notification Service) for iOS
- FCM (Firebase Cloud Messaging) for Android
- Scheduled reminder jobs via Celery + Redis
- **Architecture note:** APNs token refresh must be triggered on every app
  update via `UIApplication.registerForRemoteNotifications()` — missed in
  v3.1.0 build

### File Storage
- Files uploaded directly to S3 via pre-signed URLs
- Max file size enforced client-side AND server-side (5MB free, 100MB premium)
- Virus scan via ClamAV before file is made available

### Analytics Service
- Aggregates task completion events into daily/weekly rollups
- Stored in separate read-replica PostgreSQL database
- **Performance issue:** Full-account aggregation query is O(n) in task count —
  fails for accounts with >5,000 tasks (timeout at 30s)

## Mobile App Architecture

### iOS (Swift / SwiftUI)
- Architecture: MVVM + Combine
- Local storage: Core Data with CloudKit backup (deprecated — migrating to
  custom sync)
- Networking: URLSession + custom retry logic
- Background sync: BGAppRefreshTask (15-minute intervals — accidentally set to
  30s in v3.1.0)

### Android (Kotlin)
- Architecture: MVVM + LiveData + Room (SQLite ORM)
- Background sync: WorkManager periodic task
- Push: Firebase Messaging Service

## App Versioning

| Version | Release Date | Key Changes |
|---------|-------------|-------------|
| 2.1.3 | 2023-06-12 | Stability fixes, performance improvements |
| 3.0.0 | 2023-10-01 | Full UI redesign, 2FA, new sync engine |
| 3.0.1 | 2023-11-15 | Analytics dashboard (Premium), file attachments |
| 3.0.5 | 2024-01-20 | Offline mode improvements, search index rebuild — introduced KI-001, KI-002, KI-007 |
| 3.1.0 | 2024-03-01 | Android 14 support, home screen widget, UI polish — introduced KI-004, KI-006, KI-008, KI-011 |

## Feature Flags

Feature flags are managed via LaunchDarkly and read at app startup:

| Flag | Description | Current State |
|------|-------------|--------------|
| `dark_mode` | Enables dark mode toggle in Settings | 10% rollout (beta) |
| `calendar_view` | Shows Calendar tab in navigation | Off (not implemented) |
| `biometric_login` | Enables Face ID / fingerprint login | Off (in development) |
| `pdf_export` | Export notes/tasks to PDF | Off (planned Q3) |
| `team_collab_free` | Real-time collab for free tier | Off (Team tier only) |
