# Demo & Handover

## 5-minute walkthrough script

Record with OBS / Loom / Xbox Game Bar (`Win+Alt+R` on Windows). Resolution 1920×1080, mic on.

### 0:00 — Problem (20 s)
> "An event organizer has 1,000 invitees in an Excel sheet, each assigned to a color-coded table. They need to email every invitee a barcode, then scan them at the door and direct them to the right table. Doing that by hand takes two people an hour of pre-event work plus slow check-in lines."

Cut to: the source CSV (`data/input/WFHAttendees.csv`) in VS Code.

### 0:20 — Architecture (40 s)
Screenshot the ASCII diagram from README. Narrate:
> "Our system has four moving parts: a LangGraph agent that handles the bulk workflow, a FastAPI backend, a React scanner for staff phones, and a Streamlit admin dashboard. Everything is local-first — SQLite on disk, Gmail SMTP, no cloud account needed."

### 1:00 — Run the agent (60 s)
Show three terminals side by side.

Start API:
```bash
python run_api.py
```
Start Streamlit and React in the other two tabs.

Open Streamlit → "Run Agent" → click **Run Agent Now**. Narrate the progress bar:
> "The graph is running `read_csv → generate_barcodes → send_emails → update_status`. Each step commits per row, so it's resumable if anything crashes."

When it completes, show the state JSON: `imported: 1000, barcodes_generated: 1000, emails_sent: 1000`.

### 2:00 — Received email (40 s)
Switch to Gmail on a phone. Open the invite email. Show:
- Attendee's first name in the greeting
- Color-coded table line
- Inline barcode + QR code

> "Both codes are inline so the email client doesn't need to fetch attachments separately — works offline on the phone once the email is synced."

### 2:40 — Scan at the venue (80 s)
Point the laptop or phone camera at the barcode on the email (or a printed copy). Show the scanner page.

> "The camera is `html5-qrcode` running entirely in the browser. Two-second cooldown between scans so the scanner doesn't fire ten times on one barcode."

Scan succeeds → big green card with name + color swatch pops up. Scan again → yellow "already checked in" card.

> "Duplicate detection is a DB query on today's scan_log — first scan flips status to CheckedIn, subsequent scans are logged as duplicates but don't reset the timestamp."

### 4:00 — Admin view updates live (30 s)
Switch to Streamlit. Show:
- Metric cards: `Pending: 0, Sent: 1000, Checked in: 2, Scans today: 2`
- Bar chart by color
- Recent scans table

> "Streamlit polls the API every few seconds. An event runner can watch this on a second monitor and spot stuck queues or color imbalances in real time."

### 4:30 — What we built (30 s)
Quick slide/screen:
- 40 tasks across 10 phases
- 24 tests passing, 1,000-row run in 30 s (mocked SMTP), p95 scan latency 14 ms
- Stack: FastAPI · LangGraph · SQLite · React + Vite · Streamlit · Docker

> "Shipping path: a laptop on venue WiFi handles the event as-is. Scaling out, swap SQLite for Postgres, move SMTP to SendGrid, and deploy the three Dockerfiles to Azure Container Apps. The code is ready for both."

End card with links: GitHub, TASKS.md, DEPLOYMENT.md.

---

## Slide deck outline

10 slides, ~45 s each.

1. **Title** — "WFH Event Scanner · barcode-based check-in for 1,000 guests"
2. **Problem** — manual Excel lookup, slow queues, no visibility. One-sentence business impact.
3. **Solution at a glance** — 4-component diagram, same ASCII as README.
4. **Agent flow** — LangGraph node sequence + what each node does.
5. **Data model** — `attendees` + `scan_log` schema, sample row.
6. **Scanner UX** — screenshots of the three frontend pages; "2 m viewing distance" design constraint.
7. **Admin UX** — Streamlit dashboard screenshot.
8. **Testing & load numbers** — paste [docs/LOAD_REPORT.md](LOAD_REPORT.md) table.
9. **Deployment options** — local / Docker Compose / Azure Container Apps (two rows from [docs/DEPLOYMENT.md](DEPLOYMENT.md)).
10. **Next steps & handover** — Postgres migration, SendGrid, LDAP/SSO for staff auth, offline-first service worker for flaky venue WiFi.

---

## Handover checklist

- [ ] Fresh Gmail App Password issued to the event lead; old ones rotated.
- [ ] `.env` filled in on the event laptop (not committed).
- [ ] 3-row test CSV run end-to-end; test attendee confirms email + barcode.
- [ ] `docker compose up` boots the full stack on the event laptop.
- [ ] README walkthrough completed by someone who hasn't touched the repo.
- [ ] Load report attached to the handover package.
- [ ] Repo default branch protected; `main` requires PR review.
- [ ] On-call contact: PM / Backend lead phone numbers in the runbook.
