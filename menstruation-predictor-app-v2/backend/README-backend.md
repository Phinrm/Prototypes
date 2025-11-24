# Menstruation Predictor Backend (v2: Accounts + Settings)

## Setup

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

API base URL: `http://127.0.0.1:8000`

## Core endpoints

### Auth & Profile
- `POST /register` – create account (email + password + profile)
- `POST /login` – login (returns user profile with `id`)
- `GET /me?user_id=` – get profile / health details
- `PUT /me?user_id=` – update profile, privacy, language, theme

### Settings
- `GET /settings?user_id=` – menstrual tracking & prediction settings
- `POST /settings?user_id=` – create/update cycle settings
- `GET /notification-settings?user_id=` – notification preferences
- `POST /notification-settings?user_id=` – update notification preferences

### Period Logs & Predictions
- `POST /periods?user_id=` – add a period entry
- `GET /periods?user_id=` – list period logs
- `PATCH /periods/{period_id}?user_id=` – mark period as excluded from stats
- `GET /predictions?user_id=` – next period, fertile window, ovulation, cycle day
- `GET /cycle-history?user_id=` – history plus cycle length to next

### Data Management
- `GET /export-data?user_id=` – export all data (JSON bundle)
- `DELETE /account?user_id=` – delete account and all health data
