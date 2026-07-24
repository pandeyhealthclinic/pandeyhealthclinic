# Pandey Health Clinic — Website & Management System

**Status: all 6 planned phases complete.** Public landing page,
patient accounts, appointment booking, medicine e-commerce, a full
admin panel, and online consultation + notifications — all served
from one Flask app.

## Stack
- Flask (Python) backend, Jinja2 templates
- Vanilla HTML/CSS/JS frontend (no build step)
- Firebase Firestore/Auth/Storage (wired in progressively — landing
  page runs fine without credentials, using local seed content)

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # fill in Firebase values when ready
```

## Run

```bash
python wsgi.py
```

Visit http://localhost:5000 — this launches the complete site. No
manual HTML file opening required.

## Project structure

```
pandey-clinic/
├── wsgi.py                   # entrypoint (local: python wsgi.py; prod: gunicorn wsgi:app)
├── config.py                # env-driven configuration
├── requirements.txt
├── .env.example
└── app/
    ├── __init__.py           # app factory, registers blueprints
    ├── firebase.py            # Firebase Admin bootstrap (graceful offline fallback)
    ├── blueprints/
    │   └── main/routes.py     # landing page + service detail routes
    ├── utils/
    │   ├── content_service.py # Firestore-first, seed-data-fallback content layer
    │   └── seed_content.py    # local fallback content (mirrors future Firestore collections)
    ├── templates/
    │   ├── base.html, index.html, service_detail.html, 404.html, 500.html
    │   └── partials/navbar.html, footer.html
    └── static/
        ├── css/style.css
        ├── js/main.js
        └── images/            # add real clinic/doctor photos here (see filenames below)
```

## Adding real images

Drop files into `app/static/images/` using these names (the templates
already reference them, with placeholder fallbacks if missing):
`doctor-hero.jpg`, `doctor-thumb.jpg`, `doctor-full.jpg`,
`clinic-interior.jpg`, `service-*.jpg` (see `seed_content.py` for the
full list), `gallery-*.jpg`.

## Deploying to Render (GitHub-connected)

### 1. Push to GitHub first
Everything in `.gitignore` (`.env`, `firebase-service-account.json`,
`venv/`, `__pycache__/`) stays off GitHub automatically — do not
manually add or force-push those files. Nothing else in this project
needs to change before pushing.

### 2. Create the Render service
- New → Web Service → connect your GitHub repo.
- Render auto-detects `render.yaml` in the repo root and pre-fills
  most settings. If you set it up manually instead, use:
  - **Build Command:** `pip install -r requirements.txt`
  - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60`
- Render sets `$PORT` itself — don't hardcode a port anywhere.

### 3. Environment variables — set these in Render's dashboard (Environment tab), never in the repo
| Variable | Where it comes from |
|---|---|
| `FLASK_ENV` | set to `production` |
| `FLASK_DEBUG` | set to `0` |
| `SECRET_KEY` | any long random string (Render can auto-generate this — see `render.yaml`) |
| `FIREBASE_API_KEY` | Firebase Console → Project Settings → General → your web app's config |
| `FIREBASE_AUTH_DOMAIN` | same place |
| `FIREBASE_PROJECT_ID` | same place |
| `FIREBASE_STORAGE_BUCKET` | same place |
| `FIREBASE_MESSAGING_SENDER_ID` | same place |
| `FIREBASE_APP_ID` | same place |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase Console → Project Settings → Service Accounts → Generate new private key. **Paste the entire downloaded JSON file's contents** as this variable's value (not a file path — Render doesn't have your local filesystem). This is the one thing that's handled differently in production vs. local dev; see `app/firebase.py` for exactly how it's read. |

Do **not** set `FIREBASE_SERVICE_ACCOUNT_PATH` on Render — that one's
only for local development, where the JSON file actually exists on
your disk. On Render, `FIREBASE_SERVICE_ACCOUNT_JSON` is checked first
and takes priority automatically.

### 4. Deploy
Push to your connected branch — Render builds and deploys
automatically from there. First boot will log a warning if any
Firebase env var is missing/malformed and fall back to seed data
instead of crashing, so a misconfigured env var won't take the whole
site down — check Render's logs if the store/booking/admin pages look
like they're showing demo content instead of your real data.

### 5. After first deploy
Promote your own account to admin the same way as local dev, just
pointed at production — either run
`python -m app.utils.promote_admin your-email@example.com` from
Render's shell (Dashboard → your service → Shell), or run it locally
with the same `FIREBASE_SERVICE_ACCOUNT_JSON`/`FIREBASE_PROJECT_ID`
env vars set temporarily, since it talks to the same Firebase project
either way.

## Firebase setup (when ready)

1. Create a Firebase project → enable Firestore, Authentication, Storage.
2. Project Settings > General → copy the client config values into `.env`.
3. Project Settings > Service Accounts → generate a private key, save
   as `firebase-service-account.json` in the project root (already
   gitignored).
4. Restart the app — `app/firebase.py` will detect the credentials and
   switch from seed data to live Firestore reads automatically. No
   code changes needed elsewhere.

## Phase 6: Online consultation, notifications, SEO polish, UX polish

**Online consultation** — once an admin confirms an `online` appointment
(`/admin/appointments`), the system auto-generates a free Jitsi Meet
video/audio link (`meet.jit.si/PandeyHealthClinic-{id}`, no API key or
paid telephony needed) and unlocks a text chat thread between the
patient and clinic staff at `/appointments/<id>/consult`. Messages are
stored in Firestore under `appointments/{id}/messages`.

**Admin-side consultation inbox** (`/admin/consultations`) — a
dedicated section listing every online consultation as its own
thread: patient, service, last message preview, and an unread-count
badge (also shown next to "Consultations" in the sidebar). Clicking
a row opens `/admin/consultations/<id>`, a per-appointment thread
that's completely separate from every other patient's chat — nothing
mixes together. Opening a thread auto-marks the patient's messages as
read; replying there notifies the patient and posts into the same
Firestore thread the patient sees on their end.

**Notifications** — `app/utils/notifications.py` writes to a
`notifications` Firestore collection whenever an admin changes an
appointment or order status. Patients see an unread-count bell in the
navbar (any page) and a full list at `/dashboard/notifications`
(visiting it marks everything read).

**SEO** — `/robots.txt` and a dynamically generated `/sitemap.xml`
(covers the homepage, every service, and every medicine), a canonical
`<link>` tag on every page, and `MedicalClinic`/`Physician` JSON-LD
structured data on the homepage.

**Fixed: duplicate chat/form submissions.** Every form on the site
(chat, booking, checkout, admin forms) now disables its submit button
the instant it's clicked, so a double-click or a slow response can't
fire the same request twice. This was the cause of duplicate messages
appearing in the consultation chat.

**Modern loading feel.** A thin progress bar animates across the top
of the page on every navigation/form submit (`app/static/js/main.js`),
and pages fade in via a pure-CSS animation — no JS dependency, so it
never risks leaving a page invisible if a script fails to load.

**Notification sound.** While a patient has any page open, the browser
polls `/dashboard/notifications/unread-count` every 20 seconds; if the
unread count goes up, it plays a short in-browser beep (generated with
the Web Audio API — no audio file needed) and updates the bell badge
live, without a page refresh.

**Fuller responsive coverage.** Added breakpoints for very small
phones (≤400px) and large desktops (≥1440px), and the admin sidebar
now becomes a horizontally-scrollable top bar on mobile instead of
cramped wrapping.

**Fixed: patient pages had no way back.** The dashboard, profile,
booking, cart/checkout, and consultation pages relied entirely on the
browser's back button — there was no way to jump to Home, the store,
or booking from inside them. All of these now include a small
quick-nav bar (Home / Dashboard / Medicine Store / Book Appointment /
My Profile) right at the top, with the current page highlighted.

**Added: order-details popup.** The dashboard used to show only an
order ID and a tracker — no way to see what was actually ordered.
Clicking "View Details" now opens a modal with the full item list,
quantities, prices, delivery address, payment method, and a
prescription-required notice where relevant. Built as a pure-CSS
`:target` modal (no JavaScript dependency at all) — given the
login-form bug from earlier, anything that can work without depending
on JS timing gets built that way now.

**Fixed: a real security bug in login/register/forgot-password.** None
of these three forms had a `method` attribute, so they defaulted to
`GET`. The only thing stopping a native browser submission was an
inline `onsubmit="clinicAuth.xxx(...)"` — if the JS module was still
loading (slow connection, or the nested Firebase CDN import got
blocked) at the moment someone clicked submit, that inline handler
threw before `preventDefault()` could run, and the browser fell back
to its default GET submission — putting the email and password
straight into the URL bar and browser history. Fixed two ways: (1)
every auth form now has `method="post"`, so even a total JS failure
can no longer leak credentials into a URL; (2) the submit handlers are
now bound via `addEventListener` from inside the JS module itself
(atomic with the module's own execution) instead of an inline HTML
attribute referencing a global that might not exist yet. If the form
ever does POST without JS (network hiccup, JS disabled), the server
now shows a clear "please refresh and try again" message instead of a
raw 405 or silent failure.

**Fixed: dead navigation links.** "Medicines" in the navbar, "Order
Medicines" and "Consult Online" on the homepage, and both quick-action
cards used to point to `#anchor` fragments — one of which (`#consult`)
didn't even exist as a section, and the medicine ones only scrolled to
a teaser instead of opening the real store. All of these now link
directly to the real store/booking routes (booking links pre-select
online/offline as appropriate).

**Added: patient profile editing** at `/dashboard/profile/edit` (name
+ phone; email is tied to Firebase Auth login and shown read-only).

**Redesigned: toast notifications, cart, and order tracking.**
- Flash messages are now proper auto-dismissing toast cards (top-right,
  icon, slide animation) instead of plain stacked bars.
- The cart page has quantity +/− steppers, a real order-summary
  breakdown, and a proper empty-state instead of a bare line of text.
- A visual step indicator (Cart → Checkout → Confirmation) runs across
  the buying flow, and a Pending → Confirmed → Packed → Dispatched →
  Delivered pipeline tracker shows on the confirmation page and in the
  patient dashboard's order list.

**Added: silent auto-refresh** (no page reload, no lost scroll
position) on the patient dashboard, both consultation chat threads,
and the admin appointments/orders/consultations lists — each polls a
small HTML-fragment endpoint (`/dashboard/refresh`,
`/admin/appointments/table`, `/admin/orders/table`,
`/admin/consultations/table`, `/appointments/<id>/consult/messages`,
`/admin/consultations/<id>/messages`) every 4–6 seconds and swaps just
that section's content. Chat threads also auto-scroll and play the
notification sound when a new message arrives. Polling intervals are
a few seconds rather than exactly 2, to keep Firestore read costs
reasonable — each poll is a real database read, so a very aggressive
interval multiplies your Firestore usage fast. Adjust
`data-refresh-interval` (milliseconds) on any of the wrapper `<div>`s
in the templates above if you want it faster or slower.

## Phase 5: Admin panel

Everything under `/admin` requires `role == "admin"` on the logged-in
user's Firestore profile (see `app/utils/promote_admin.py` to grant
that role — there's no self-serve signup for admin accounts, by
design).

- **Dashboard** (`/admin/`) — patient count, pending appointments,
  total order revenue, low-stock medicine count, recent appointments/orders
- **Services** (`/admin/services`) — full CRUD, backed by the `services` Firestore collection
- **Medicines** (`/admin/medicines`) — full CRUD including stock, MRP/offer price, prescription flag
- **Appointments** (`/admin/appointments`) — filter by status, change status inline (pending/confirmed/completed/cancelled), view uploaded reports
- **Orders** (`/admin/orders`) — filter by status, move through the full pipeline (pending → confirmed → packed → dispatched → delivered, or cancelled/refunded)
- **Testimonials** (`/admin/testimonials`) — approve/hide/delete; only `approved: true` testimonials show on the public site
- **Gallery** (`/admin/gallery`) — upload photos straight to Firebase Storage, delete them
- **Patients** (`/admin/patients`) — read-only roster of registered patients
- **Website Content** (`/admin/content`) — edit hero/about/doctor/contact text live on the homepage (list-based fields like trust badges and vision points aren't covered by this simple form yet — edit those directly in the `site_content` Firestore documents)

All of this reads/writes the same `content_service.py` layer from
Phase 1 — so once you add data through the admin panel, the public
site immediately serves it instead of the seed fallback, with zero
template changes needed elsewhere.

## Phase 4: Medicine store

Routes under `/medicines`:
- `GET /medicines/` — catalog with `q` (search), `category`, `sort` (price_low/price_high/rating/name), `page`
- `GET /medicines/<id>` — detail page with qty selector, Buy Now, wishlist toggle, related products
- `POST /medicines/cart/add|update`, `POST /medicines/cart/remove`, `GET /medicines/cart`
- `POST /medicines/wishlist/toggle`, `GET /medicines/wishlist`
- `GET|POST /medicines/checkout` (login required) → creates a Firestore `orders` doc, flags `needs_prescription`
- `GET /medicines/order-confirmation/<id>`

Cart and wishlist are stored server-side in the Flask session (not
Firestore) so anonymous visitors can browse and add items before
creating an account — login is only required at checkout, where the
cart converts into a real order. Medicine catalog seed data lives in
`seed_content.py` (`MEDICINES`) the same way services do, and will
switch to live Firestore reads the moment the `medicines` collection
has documents.

## Phase 3: Appointment booking

Routes added under `/appointments`:
- `GET /appointments/book` — booking form (service, date, time, online/offline, symptoms, optional report upload)
- `POST /appointments/book` — creates the appointment in Firestore (`appointments` collection)
- `GET /appointments/confirmation/<id>` — confirmation page
- `POST /appointments/<id>/cancel`, `GET|POST /appointments/<id>/reschedule` — patient self-service, both ownership-checked

Report uploads go to Firebase Storage under `reports/{uid}/...` via
`app/utils/storage_service.py` — this silently no-ops if Storage isn't
configured yet, so booking still works without file uploads.

**Firestore index note:** the double-booking check queries
`date == ? AND time == ? AND status in [...]`. Firestore will ask you
to create a composite index the first time this runs against a real
project — click the link in the error log/console when it appears.
Until then, the check is skipped (booking still succeeds) rather than
failing the request.
