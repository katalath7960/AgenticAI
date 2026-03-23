# API Reference — FlowTask Backend v2

Base URL: `https://api.flowtask.io/api/v2`

All endpoints require `Authorization: Bearer <access_token>` except `/auth/*`.

---

## Authentication

### POST /auth/login
Authenticate user and receive tokens.
```json
Request:  { "email": "user@example.com", "password": "secret" }
Response: { "access_token": "...", "refresh_token": "...", "expires_in": 900 }
```
**Error codes:**
- `401` — invalid credentials
- `403` — 2FA required (follow up with `/auth/2fa/verify`)
- `429` — rate limited (5 failed attempts per minute)

### POST /auth/2fa/verify
```json
Request:  { "session_token": "...", "otp_code": "123456" }
Response: { "access_token": "...", "refresh_token": "..." }
```
**Known issue:** SMS delivery may be delayed 60-120s on some carrier networks.

### POST /auth/refresh
```json
Request:  { "refresh_token": "..." }
Response: { "access_token": "...", "expires_in": 900 }
```

### POST /auth/logout
Revokes the current refresh token. Returns `204 No Content`.

---

## Tasks

### GET /tasks
Returns paginated task list for the authenticated user.

Query params: `project_id`, `status`, `priority`, `tag`, `due_before`, `due_after`, `page`, `page_size` (default 50, max 200)

```json
Response: {
  "items": [ { "id": "t_abc123", "title": "...", "status": "open", "priority": "High", ... } ],
  "total": 142,
  "page": 1,
  "page_size": 50
}
```

### POST /tasks
Create a new task.
```json
Request: {
  "title": "Fix login bug",
  "description": "Users cannot login on Android 13",
  "project_id": "p_xyz",
  "priority": "High",
  "due_date": "2024-04-15T09:00:00Z",
  "tags": ["android", "login"]
}
Response: 201 Created, full task object
```

### GET /tasks/{task_id}
Returns single task with sub-tasks and attachments.

### PATCH /tasks/{task_id}
Partial update. Supported fields: `title`, `description`, `status`, `priority`, `due_date`, `tags`, `assignee_id`.

### DELETE /tasks/{task_id}
Soft-deletes task. Returns `204 No Content`.

### POST /tasks/{task_id}/subtasks
Create a sub-task under the given task.

### GET /tasks/{task_id}/attachments
List file attachments for a task.

### POST /tasks/{task_id}/attachments
Returns a pre-signed S3 URL for direct upload. Client uploads file to S3, then calls `PATCH /tasks/{task_id}/attachments/{attachment_id}/confirm`.

**Error codes:**
- `413` — file size exceeds tier limit (5MB free, 100MB premium)

---

## Projects

### GET /projects
List all projects for the user.

### POST /projects
```json
Request: { "name": "Q2 Launch", "color": "#4A90D9", "icon": "rocket" }
```

### PATCH /projects/{project_id}
Update name, color, icon, or archive status.

### DELETE /projects/{project_id}
Archive project (tasks preserved). Hard-delete requires `?permanent=true`.

---

## Sync

### WebSocket: wss://sync.flowtask.io/v2/connect
Authentication via query param: `?token=<access_token>`

**Client → Server messages:**
```json
{ "type": "push", "mutations": [ { "entity": "task", "id": "t_abc", "op": "update", "data": {...}, "ts": 1711234567 } ] }
{ "type": "pull", "cursor": 1711234000 }
```

**Server → Client messages:**
```json
{ "type": "delta", "mutations": [...], "cursor": 1711234600 }
{ "type": "conflict", "entity": "task", "id": "t_abc", "server_version": {...} }
{ "type": "error", "code": "TOKEN_EXPIRED" }
```

**Reconnect strategy:** Exponential back-off starting at 1s, max 30s. Always send `pull` with last known cursor on reconnect to catch missed mutations.

---

## Notifications

### GET /notifications/settings
Returns per-category notification preferences.

### PATCH /notifications/settings
```json
Request: { "task_due": true, "task_overdue": true, "team_mention": false, "quiet_hours_start": "22:00", "quiet_hours_end": "08:00" }
```

### POST /notifications/register-device
Register APNs or FCM device token.
```json
Request: { "platform": "ios", "token": "apns_device_token_here", "app_version": "3.1.0" }
```
**Note:** Must be called every time the app receives a new device token from APNs/FCM, including after app updates.

---

## Search

### GET /search?q={query}
Full-text search across tasks and notes.

Query params: `q` (required), `type` (`task`|`note`|`all`), `project_id`, `page`, `page_size`

**Performance note:** Index rebuild after bulk imports may cause stale results for up to 60 seconds.

---

## Analytics (Premium)

### GET /analytics/summary
Returns task completion stats for the past 30 days.
**Known issue:** Times out for accounts with >5,000 tasks. Returns `503 Service Unavailable` with `Retry-After: 60`.

### GET /analytics/trends
Returns weekly rollup data for charts.

---

## Error Response Format
```json
{ "error": { "code": "VALIDATION_ERROR", "message": "title is required", "details": {...} } }
```

Common error codes: `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `RATE_LIMITED`, `SERVICE_UNAVAILABLE`
