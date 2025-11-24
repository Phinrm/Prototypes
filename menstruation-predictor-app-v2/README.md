# PinkCycle – Menstrual Cycle Prediction & Tracking App

PinkCycle is a full-stack menstrual cycle tracking and prediction app built with:

- **Frontend:** React + Vite
- **Backend:** FastAPI (Python) + SQLite
- **AI Assistant:** Gemini 2.5 Flash (Google Generative AI)
- **Email:** Gmail API (for password reset)

It allows users to:

- Create an account and log in
- Track their periods
- See predicted next period, fertile window, and ovulation
- Customize detailed cycle and notification settings
- Export / delete their data
- Ask an AI assistant FAQs about menstrual health and how to use the app
- Enjoy a pink, butterfly-themed UI tailored for a feminine, friendly vibe 🦋

---

## Features

### 🔐 Accounts & Authentication

- Email + password registration
- Login with persisted `user_id` in `localStorage`
- Optional **App Lock** (toggle in Settings)
  - When enabled, requires the user’s password to unlock the app
- Password reset via email:
  - User clicks **“Forgot password?”**
  - Backend sends a password reset link using the Gmail API
  - User visits `/reset-password?token=...` to set a new password

> **Note:** This is a demo implementation, not production-grade auth. In production you’d typically use JWTs, refresh tokens, stronger hashing, etc.

---

### 📊 Cycle Tracking & Prediction

- Log periods with:
  - Start date
  - End date
  - Flow intensity (light / medium / heavy)
  - “Exclude from stats” flag (for irregular cycles due to travel, illness, etc.)
- Cycle history table:
  - Period start/end
  - Period length
  - Cycle length to next period
  - Whether that cycle is included in statistics
- Prediction engine (backend):
  - Uses logged periods (excluding “excluded from stats”) and/or initial settings to estimate:
    - Next period start and end
    - Approximate ovulation day
    - Fertile window (ovulation ± 2 days)
    - Today’s cycle day
  - Respects flags like:
    - **Irregular cycle mode**
    - **Pregnancy mode**
    - **Lactation mode**
    - **Show/hide fertile window**

Dashboard shows:

- “Your cycle at a glance” card with:
  - Today’s cycle day
  - Next predicted period (date + length)
  - Fertile window & ovulation (if enabled)
  - Cycle length used, average period length
- Banners for:
  - **Irregular cycles**
  - **Pregnancy/Lactation mode**
- Calendar view:
  - Monthly calendar with:
    - Predicted period days highlighted
    - Fertile window highlighted (optional)
    - “Today” indicator
  - Legend for period/fertile/today

---

### ⚙️ Settings (Fully Wired)

Accessible via the **Settings** tab. Settings are persisted and affect behavior.

#### 1. Account & Profile

- Email (read-only)
- Age
- Height (cm)
- Weight (kg)
- Goal:
  - Track cycle
  - Try to conceive
  - Avoid pregnancy
  - Perimenopause
- Contraceptive method:
  - None, Pill, IUD, Implant, Injection

These values can be used by the prediction logic and the AI FAQ context.

#### 2. Cycle Tracking & Prediction Settings

- First day of last period
- Average cycle length (days)
- Average period length (days)
- “I use hormonal contraceptives” (toggle)
- “Show fertile window on calendar” (toggle)
- “My cycles are irregular” (toggle)
- Pregnancy mode (toggle)
- Lactation mode (toggle)
- Tracked symptoms (comma-separated list; e.g., `cramps,bloating,headache,mood_swings`)

These settings directly influence predictions and how the UI displays.

#### 3. Notifications & Reminders (Preferences)

Notification preferences stored in the backend:

- **Period notifications**
  - Toggle + “Days before period” (0–5)
- “Remind me to log when my period ends”
- Fertile window reminders
- Ovulation day reminder
- Daily log reminders
  - Toggle + time
- Medication / pill reminders
  - Toggle + time

> **Note:** In this demo, notifications aren’t yet wired to real push / OS notifications. They’re stored as preferences ready to be hooked into a scheduler or mobile push system.

#### 4. Privacy & Security

- App lock enabled (toggle)
  - When enabled, a lock overlay appears on startup and requires the user’s password to unlock (via `/login`).
- Data sharing consent (toggle)
  - For anonymized analytics/improvements (stored flag)
- Privacy policy text placeholder

#### 5. Integrations & Appearance

- Language (currently `en`)
- Region (e.g. `KE`)
- Theme:
  - Pink butterflies (default)
  - Midnight glow (dark theme)
  - Soft pastels
- Wearable integration enabled (toggle; placeholder for future Apple Watch/Fitbit integrations)

Themes apply via `className="app-root theme-..."` and CSS variants.

#### 6. Data Management

- Export my data (JSON)
  - Calls `/export-data?user_id=` and downloads `pinkcycle-export.json`
  - Contains user, cycle settings, notification settings, and period logs
- Delete account & data
  - Calls `/account?user_id=` and deletes all associated data
  - Clears local storage and reloads

---

### 💬 AI FAQ Assistant (Gemini 2.5 Flash Integration)

Under the **AI FAQ** tab, users can:

- Type questions about:
  - Menstrual cycles
  - PMS symptoms
  - Fertile windows
  - Using PinkCycle features
- Receive friendly, general guidance generated by **Gemini 2.5 Flash**

Backend:

- `POST /ai/faq` – uses `google-genai` client with `gemini-2.5-flash`
- Uses prompts with:
  - Safety instructions (not a doctor, no diagnosis)
  - Optional context from user’s goal & contraceptive status

Frontend:

- `FaqAssistant` React component:
  - Chat-style UI with bubbles
  - Loading state
  - Error handling
  - Clear disclaimer: not a replacement for a doctor

---

### 💌 Password Reset (Gmail API)

When a user clicks **“Forgot password?”**:

1. Frontend calls `POST /request-password-reset` with their email.
2. Backend:
   - Generates a one-time token (stored in `PasswordResetToken` table).
   - Builds a reset URL:  
     `http://127.0.0.1:5173/reset-password?token=...`
   - Sends an email via **Gmail API** (using a service account).
3. User clicks the link → `ResetPasswordScreen`:
   - Submits new password → `POST /reset-password`
   - Backend validates token and updates the password.

> **Note:** You must configure a Gmail API-enabled Google Cloud project, service account, and `service-account.json` file for this to work.

---

## Project Structure

Rough layout:

```txt
menstruation-predictor-app/
  backend/
    main.py
    models.py
    schemas.py
    crud.py
    ai_client.py
    email_utils.py
    database.py (if present)
    requirements.txt
    .env                # holds GOOGLE_AI_API_KEY, etc.
    service-account.json (for Gmail API; do NOT commit)
  frontend/
    index.html
    vite.config.js
    package.json
    src/
      main.jsx
      App.jsx
      api.js
      styles.css
      components/
        AuthScreen.jsx
        Dashboard.jsx
        CalendarView.jsx
        PeriodForm.jsx
        HistoryView.jsx
        SettingsScreen.jsx
        ButterflyBackground.jsx
        AppLockOverlay.jsx
        ResetPasswordScreen.jsx
        FaqAssistant.jsx

##Usage Flow

Start backend (uvicorn main:app --reload).

Start frontend (npm run dev).

Open http://127.0.0.1:5173 in your browser.

Sign up with email + password + optional age/height/weight/goal.

After login:

Go to Settings and configure cycle basics (average cycle length, last period).

Optionally toggle app lock, theme, notifications, etc.

Use Log Period to track your periods over several cycles.

View Dashboard for predictions & calendar.

View History for a table of your period logs.

Use Settings for fine-tuning and data management.

Use AI FAQ to ask questions:

“How does PinkCycle predict my next period?”

“What is a fertile window?”

“Can I track irregular cycles?”

## Safety & Disclaimer

The app is intended for educational and tracking purposes only.

Predictions are estimates, not guarantees.

The AI FAQ assistant (Gemini 2.5 Flash) is configured to:

Avoid diagnosis and prescriptions.

Encourage users to see a healthcare professional for concerning symptoms.

This codebase is not ready for medical or production use without further security, privacy, and compliance work (e.g., HIPAA/GDPR).


##Future Enhancements (Ideas)

True notification scheduler (email, push, or mobile notifications).

Detailed symptom logging per day (mood, cramps, sleep, BBT, etc.).

More advanced prediction algorithm (e.g., ML or statistical models).

Multi-language UI and localized educational content.

Real wearable integration (Apple Health, Fitbit, Oura, etc.).

Role-based data sharing with clinicians (read-only dashboards).