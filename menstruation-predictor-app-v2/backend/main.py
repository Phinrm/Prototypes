from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from email_utils import send_password_reset_email
from urllib.parse import urlencode
from ai_client import answer_faq

import models, schemas, crud
from database import Base, engine, SessionLocal

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Menstruation Predictor API (Accounts + Settings)")

# CORS for local frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_or_404(db: Session, user_id: int):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Auth & profile ---------------------------------------------------------

@app.post("/register", response_model=schemas.UserProfile)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        user = crud.create_user(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return user


@app.post("/login", response_model=schemas.UserProfile)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


@app.get("/me", response_model=schemas.UserProfile)
def get_profile(user_id: int = Query(...), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    return user


@app.put("/me", response_model=schemas.UserProfile)
def update_profile(
    profile: schemas.UserBase,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    user = get_user_or_404(db, user_id)
    user = crud.update_user_profile(db, user, profile)
    return user


# Settings ---------------------------------------------------------------

@app.get("/settings", response_model=schemas.CycleSettingsResponse)
def read_settings(user_id: int = Query(...), db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    settings = crud.get_cycle_settings(db, user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not configured yet")
    return settings


@app.post("/settings", response_model=schemas.CycleSettingsResponse)
def set_settings(
    settings_in: schemas.CycleSettingsCreate,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)
    settings = crud.upsert_cycle_settings(db, user_id, settings_in)
    return settings


@app.get("/notification-settings", response_model=schemas.NotificationSettingsResponse)
def read_notification_settings(
    user_id: int = Query(...), db: Session = Depends(get_db)
):
    get_user_or_404(db, user_id)
    settings = crud.get_notification_settings(db, user_id)
    if not settings:
        raise HTTPException(status_code=404, detail="Notification settings not found")
    return settings


@app.post("/notification-settings", response_model=schemas.NotificationSettingsResponse)
def set_notification_settings(
    settings_in: schemas.NotificationSettingsCreate,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)
    settings = crud.upsert_notification_settings(db, user_id, settings_in)
    return settings


# Periods & history ------------------------------------------------------

@app.post("/periods", response_model=schemas.PeriodLogResponse)
def add_period(
    period_in: schemas.PeriodLogCreate,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)
    if period_in.end_date < period_in.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be before start date")
    period = crud.create_period_log(db, user_id, period_in)
    return period


@app.get("/periods", response_model=List[schemas.PeriodLogResponse])
def list_periods(user_id: int = Query(...), db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    periods = crud.list_period_logs(db, user_id)
    return periods


@app.patch("/periods/{period_id}", response_model=schemas.PeriodLogResponse)
def update_period(
    period_id: int,
    updates: schemas.PeriodLogUpdate,
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    get_user_or_404(db, user_id)
    period = crud.update_period_log(db, user_id, period_id, updates)
    if not period:
        raise HTTPException(status_code=404, detail="Period log not found")
    return period


# Predictions ------------------------------------------------------------

def compute_cycle_stats(db: Session, user_id: int):
    settings = crud.get_cycle_settings(db, user_id)
    if not settings:
        raise HTTPException(status_code=400, detail="Settings must be configured before predictions")

    periods = crud.list_period_logs(db, user_id)

    # Determine cycle length from included logs
    included_periods = [p for p in periods if not p.exclude_from_stats]

    cycle_length = settings.average_cycle_length
    period_length = settings.average_period_length

    if len(included_periods) >= 2:
        diffs = []
        for prev, nxt in zip(included_periods, included_periods[1:]):
            diffs.append((nxt.start_date - prev.start_date).days)
        if diffs:
            cycle_length = int(round(sum(diffs) / len(diffs)))

    if included_periods:
        lengths = [
            (p.end_date - p.start_date).days + 1
            for p in included_periods
        ]
        if lengths:
            period_length = int(round(sum(lengths) / len(lengths)))

    if periods:
        last_period_start = periods[-1].start_date
    else:
        if not settings.first_period_start_date:
            raise HTTPException(
                status_code=400,
                detail="No period logs or first period start date set",
            )
        last_period_start = settings.first_period_start_date

    return settings, cycle_length, period_length, last_period_start


@app.get("/predictions", response_model=schemas.PredictionResponse)
def get_predictions(user_id: int = Query(...), db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    settings, cycle_length, period_length, last_period_start = compute_cycle_stats(db, user_id)

    # If pregnancy or irregular mode is active, we still compute, but mark flags
    if settings.irregular_cycle_mode:
        irregular = True
    else:
        irregular = False

    next_period_start = last_period_start + timedelta(days=cycle_length)
    next_period_end = next_period_start + timedelta(days=period_length - 1)

    ovulation_day = last_period_start + timedelta(days=cycle_length - 14)
    fertile_window_start = ovulation_day - timedelta(days=2)
    fertile_window_end = ovulation_day + timedelta(days=2)

    today = date.today()
    cycle_day_today = (today - last_period_start).days + 1

    return schemas.PredictionResponse(
        next_period_start=next_period_start,
        next_period_end=next_period_end,
        ovulation_day=ovulation_day,
        fertile_window_start=fertile_window_start,
        fertile_window_end=fertile_window_end,
        cycle_day_today=max(cycle_day_today, 0),
        cycle_length_used=cycle_length,
        period_length_used=period_length,
        irregular_cycle_mode=irregular,
        pregnancy_mode=settings.pregnancy_mode,
        lactation_mode=settings.lactation_mode,
        show_fertile_window=settings.show_fertile_window,
    )


@app.get("/cycle-history", response_model=schemas.CycleHistoryResponse)
def cycle_history(user_id: int = Query(...), db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    periods = crud.list_period_logs(db, user_id)
    items: list[schemas.CycleHistoryItem] = []

    for idx, p in enumerate(periods):
        cycle_length = None
        if idx + 1 < len(periods):
            cycle_length = (periods[idx + 1].start_date - p.start_date).days
        items.append(
            schemas.CycleHistoryItem(
                start_date=p.start_date,
                end_date=p.end_date,
                cycle_length=cycle_length,
                excluded_from_stats=p.exclude_from_stats,
            )
        )

    return schemas.CycleHistoryResponse(periods=items)


# Export & delete --------------------------------------------------------

@app.get("/export-data", response_model=schemas.ExportBundle)
def export_data(user_id: int = Query(...), db: Session = Depends(get_db)):
    user = get_user_or_404(db, user_id)
    cycle_settings = crud.get_cycle_settings(db, user_id)
    notification_settings = crud.get_notification_settings(db, user_id)
    periods = crud.list_period_logs(db, user_id)

    return schemas.ExportBundle(
        user=user,
        cycle_settings=cycle_settings,
        notification_settings=notification_settings,
        periods=periods,
    )


@app.delete("/account")
def delete_account(user_id: int = Query(...), db: Session = Depends(get_db)):
    get_user_or_404(db, user_id)
    crud.delete_user_and_data(db, user_id)
    return {"status": "deleted"}

@app.post("/request-password-reset")
def request_password_reset(
    payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)
):
    user = crud.get_user_by_email(db, payload.email)
    if not user:
        # Don't reveal whether email exists
        return {"status": "ok"}

    prt = crud.create_password_reset_token(db, user, ttl_minutes=30)

    # Build reset link – adjust base URL to match your frontend
    base_frontend_url = "http://127.0.0.1:5173/reset-password"
    query = urlencode({"token": prt.token})
    reset_link = f"{base_frontend_url}?{query}"

    # Send via Gmail API
    try:
        send_password_reset_email(user.email, reset_link)
    except Exception as e:
        print("Error sending reset email:", e)
        # You might want to log this; still don't leak details to client

    return {"status": "ok"}


@app.post("/reset-password")
def reset_password(
    payload: schemas.PasswordResetConfirm, db: Session = Depends(get_db)
):
    prt = crud.get_valid_reset_token(db, payload.token)
    if not prt:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = crud.get_user(db, prt.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")

    crud.set_user_password(db, user, payload.new_password)
    crud.mark_reset_token_used(db, prt)
    return {"status": "password_updated"}

@app.post("/ai/faq", response_model=schemas.FAQResponse)
def ai_faq(payload: schemas.FAQRequest, db: Session = Depends(get_db)):
    """
    Answer FAQs about menstruation and how to use PinkCycle
    using Gemini 2.5 Flash.
    """
    app_context = None

    # Optional: personalize with user settings (goal, etc.)
    if payload.user_id:
        user = crud.get_user(db, payload.user_id)
        if user:
            app_context = (
                f"User goal: {user.goal}. "
                f"Uses hormonal contraceptives: {getattr(user, 'uses_hormonal_contraceptives', False)}. "
                "Answer at a general educational level and remind them to see a doctor for medical issues."
            )

    try:
        ans = answer_faq(payload.question, app_context=app_context)
    except Exception as e:
        print("AI FAQ error:", e)
        raise HTTPException(status_code=500, detail="AI assistant is currently unavailable.")

    return schemas.FAQResponse(answer=ans)