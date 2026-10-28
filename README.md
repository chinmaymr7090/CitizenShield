# CitizenShield — Smart Citizen Safety Portal

CitizenShield is a web-based platform that lets citizens report public safety and civic issues, track the progress of their complaints, share their location (with permission), and helps administrators review and resolve those issues.

> **Safety notice:** CitizenShield is for *non-emergency* civic complaints only. If you or someone else is in immediate danger, contact your local emergency services right away (in India: **112**). Do not rely on this platform for urgent help.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Objectives](#objectives)
3. [Technology Stack](#technology-stack)
4. [Main Features](#main-features)
5. [System Architecture](#system-architecture)
6. [Database Structure](#database-structure)
7. [Project Structure](#project-structure)
8. [Installation Instructions](#installation-instructions)
9. [Firebase Configuration](#firebase-configuration)
10. [Security and Privacy](#security-and-privacy)
11. [Testing Instructions](#testing-instructions)
12. [Deployment Instructions](#deployment-instructions)
13. [Limitations](#limitations)
14. [Future Enhancements](#future-enhancements)
15. [Presenting the Project (College Demo / Viva)](#presenting-the-project-college-demo--viva)

---

## Problem Statement

Public issues such as damaged roads, broken streetlights, garbage accumulation, and water leakage are often reported through scattered, informal channels (phone calls, word of mouth, social media). Citizens rarely know whether their complaint was received, and authorities lack a single place to view, prioritise, and resolve problems.

There is a need for a centralised, easy-to-use, secure platform where citizens can report issues, follow their progress, and where administrators can manage them efficiently.

## Objectives

- Provide a simple, responsive web portal for reporting public issues.
- Let citizens register, log in, and view only their own reports.
- Allow location sharing through the browser Geolocation API, **only with the user's consent**.
- Give citizens transparent tracking of report status through a report ID.
- Give authorised administrators a dashboard to review reports, update statuses, and add remarks.
- Enforce security on the server side using Firebase Authentication and Firestore Security Rules.
- Clearly distinguish routine civic complaints from emergencies.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript (ES modules) |
| Authentication | Firebase Authentication |
| Database | Cloud Firestore |
| File storage (optional) | Firebase Storage |
| Hosting | Firebase Hosting |
| Browser APIs | Geolocation API |
| Maps (optional) | Map integration, if configured |
| Tools | Visual Studio Code, Node.js, Firebase CLI |

## Main Features

**For citizens**
- Registration, login, logout, persistent sessions, password visibility toggle
- Report an issue with title, category, description, address, GPS location, and optional image
- Review a report before submitting; unique report ID generated per report
- Dashboard with totals (pending, under review, resolved), filters, and sorting
- Track a report by ID and view its status timeline

**For administrators**
- Separate admin dashboard with counts by status and by category
- Search, filter, and sort all reports
- Update status, add remarks, and record timestamped status history
- View submitted images (when authorised)

**General**
- Responsive design (mobile, tablet, desktop)
- Loading indicators, toast notifications, confirmation dialogs, and empty states
- Accessible forms and keyboard navigation
- Safe rendering of user-submitted content

**Report categories:** Roads and Transport · Streetlights and Electricity · Garbage and Sanitation · Water and Drainage · Public Infrastructure · Public Safety · Other

**Report statuses:** Submitted → Under Review → In Progress → Resolved (or Rejected)

## System Architecture

```
┌──────────────────────────────┐
│   Browser (Frontend)         │
│   index.html / style.css /   │
│   app.js                     │
│   - UI and form validation   │
│   - Geolocation API          │
└──────────────┬───────────────┘
               │ Firebase Web SDK (HTTPS)
┌──────────────▼───────────────┐
│   Firebase                   │
│   - Authentication (users)   │
│   - Cloud Firestore (data)   │
│   - Storage (images)         │
│   - Security Rules (access)  │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│   Firebase Hosting           │
│   (serves the web app)       │
└──────────────────────────────┘
```

**Who enforces what**

- **Enforced by Firebase (server side):** who is logged in, who owns a report, who is an administrator, which fields may be written.
- **Implemented in the frontend (user experience only):** form validation messages, showing/hiding menu items, loading states. Frontend checks are *never* the real security layer — they can be bypassed, so Firestore Security Rules always make the final decision.

## Database Structure

### Collection: `reports`

| Field | Description |
|---|---|
| `reportId` | Unique, human-readable reference number |
| `userId` | UID of the citizen who submitted the report |
| `title` | Short title |
| `category` | One of the defined categories |
| `description` | Detailed description |
| `location` | Address or manual location text |
| `latitude`, `longitude` | Optional GPS coordinates (only if user consents) |
| `imageUrl` | Optional image URL from Firebase Storage |
| `status` | Submitted / Under Review / In Progress / Resolved / Rejected |
| `createdAt`, `updatedAt` | Server timestamps |
| `adminRemarks` | Remarks added by administrators |
| `statusHistory` | List of status changes with timestamps |

### Collection: `users`

| Field | Description |
|---|---|
| `uid` | Firebase Authentication UID |
| `displayName` | User's name |
| `email` | User's email |
| `createdAt` | Registration time |

> Passwords are **never** stored in Firestore or local storage; Firebase Authentication handles them securely.

### Administrator authorisation

Admin rights are granted through **Firebase custom claims** (e.g., `admin: true`) or a server-controlled role mechanism. Ordinary users cannot grant themselves admin rights, and no admin password is hardcoded in frontend code.

## Project Structure

```
citizenshield/
├── index.html          # Page structure and views
├── style.css           # Styling and responsive layout
├── app.js              # Application logic and Firebase integration
├── firestore.rules     # Firestore security rules
├── storage.rules       # Storage security rules (if images are used)
├── firebase.json       # Firebase Hosting configuration
└── README.md           # This file
```

## Installation Instructions

These steps are for **Windows with Visual Studio Code**.

1. **Install Visual Studio Code** from <https://code.visualstudio.com>.
2. **Install Node.js (LTS)** from <https://nodejs.org>. Verify in the VS Code terminal:
   ```bash
   node --version
   npm --version
   ```
3. **Open the project folder** in VS Code (File → Open Folder).
4. **Install the Firebase CLI:**
   ```bash
   npm install -g firebase-tools
   ```
5. **Log in to Firebase:**
   ```bash
   firebase login
   ```
6. **Run locally.** Geolocation requires HTTPS or `localhost`. Use the VS Code *Live Server* extension, or:
   ```bash
   firebase serve
   ```
   (or `firebase emulators:start` if emulators are configured).

## Firebase Configuration

Do all of the following in the **Firebase Console** (<https://console.firebase.google.com>):

1. **Project settings → Your apps → Web app:** register a web app and copy the `firebaseConfig` object.
2. Paste the config into `app.js`. **Never invent values** — copy only what the console shows. (Web API keys are identifiers, not secrets; security comes from Security Rules.)
3. **Build → Authentication → Sign-in method:** enable **Email/Password**.
4. **Build → Firestore Database:** create a database (start in production mode).
5. **Build → Storage** (optional): enable if you support image uploads.
6. Deploy security rules (see below).

**Deploying rules (VS Code terminal):**
```bash
firebase deploy --only firestore:rules
firebase deploy --only storage
```

**Never** put service account private keys in frontend code or commit them to Git.

## Security and Privacy

- Authentication through Firebase Authentication
- Firestore Security Rules enforcing: logged-in access only, ownership checks, admin-only status updates, and blocking of unrestricted public read/write
- Citizens cannot change `status` or `adminRemarks`
- Input validation on forms and in rules
- User-submitted text is rendered safely (using `textContent`, not `innerHTML`)
- File type and size validation for uploads
- Location is requested only when the user clicks "Get My Location"; manual entry is always available; precise location is not displayed publicly
- Duplicate submissions prevented by disabling the submit button during saving
- Success messages are shown only after Firebase confirms the write

## Testing Instructions

Test each of the following and check the browser console (F12) for errors:

| Area | What to check |
|---|---|
| Registration / login | Valid signup, valid login, wrong password, invalid email |
| Report submission | Success, missing required fields, repeated clicks, offline behaviour |
| Location | Permission granted, permission denied, timeout, manual entry |
| Dashboard | Counts, filters, sorting, only own reports visible |
| Tracking | Search by valid and invalid report ID |
| Admin | Non-admin blocked; admin can update status and remarks |
| Security rules | Try reading another user's report (should fail) |
| Responsive layout | Test in browser device mode at phone, tablet, desktop widths |

## Deployment Instructions

1. Make sure the app works locally and rules are tested.
2. Initialise hosting (once):
   ```bash
   firebase init hosting
   ```
   Choose your existing Firebase project and set the public directory to the folder containing `index.html`.
3. Deploy:
   ```bash
   firebase deploy
   ```
4. Open the Hosting URL printed in the terminal and repeat the key tests (login, report submission, location, admin access) on the live site.

## Limitations

- Not an emergency service and does not replace police, fire, or medical help.
- Requires an internet connection.
- Geolocation accuracy depends on the device and browser.
- Image uploads depend on Firebase Storage being configured.
- No direct integration with government systems.
- Basic analytics only.

## Future Enhancements

- Email or SMS notifications on status changes
- Interactive map view of reports
- Multi-language support (e.g., English, Kannada, Hindi)
- Progressive Web App (offline support, installable)
- Role levels (department staff vs. super admin)
- Advanced analytics and exportable reports
- Duplicate-report detection and upvoting of issues

## Presenting the Project (College Demo / Viva)

**Suggested demo flow (5–7 minutes)**

1. **Problem:** explain why a central reporting platform is needed.
2. **Home page:** show the branding, the "Report an Issue" button, and the emergency safety notice.
3. **Register and log in** as a citizen.
4. **Submit a report** using GPS (and show manual entry as a fallback); review it before submitting; show the generated report ID.
5. **Dashboard and tracking:** show your report, filters, and tracking by report ID.
6. **Log in as admin:** update the status and add remarks.
7. **Back as citizen:** show the status change in the timeline.
8. **Security:** explain (or show) that a normal user cannot access admin actions or others' reports because of Firestore Security Rules.

**Likely viva questions and short answers**

- *Why Firebase?* It provides authentication, a database, hosting, and security rules without managing a server — ideal for a beginner-friendly, scalable project.
- *Is the Firebase API key a secret?* No. It only identifies the project; access is controlled by Authentication and Security Rules.
- *How do you stop users becoming admin?* Admin rights come from custom claims set by a trusted server-side process, and Security Rules verify them.
- *How do you protect against XSS?* User input is treated as untrusted and rendered with `textContent`, never inserted directly as HTML.
- *How is privacy handled?* Location is collected only with consent, manual entry is available, and precise coordinates are not shown publicly.
- *What is the difference between frontend and server-side validation?* Frontend validation improves usability; Security Rules enforce the real restrictions.
- *What would you improve next?* Notifications, a map view, and multi-language support.

---

*Built as a CSE project to demonstrate full-stack web development, cloud services, and secure application design.*
