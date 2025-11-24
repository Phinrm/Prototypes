from typing import Optional, List
from datetime import date
import hashlib
import secrets
from datetime import datetime, timedelta
from models import PasswordResetToken


from sqlalchemy.orm import Session

import models
import schemas


# Password helpers (demo-level; use a stronger approach in production)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"{salt}${h}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
    except ValueError:
        return False
    new_h = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return secrets.compare_digest(new_h, h)


# Users

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    if get_user_by_email(db, user_in.email):
        raise ValueError("Email already registered")

    user = models.User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        age=user_in.age,
        height_cm=user_in.height_cm,
        weight_kg=user_in.weight_kg,
        goal=user_in.goal,
        contraceptive_method=user_in.contraceptive_method,
        language=user_in.language,
        region=user_in.region,
        theme=user_in.theme,
        data_sharing_consent=user_in.data_sharing_consent,
        app_lock_enabled=user_in.app_lock_enabled,
        wearable_integration_enabled=user_in.wearable_integration_enabled,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create default settings & notifications
    settings = models.CycleSettings(user_id=user.id)
    notifications = models.NotificationSettings(user_id=user.id)
    db.add(settings)
    db.add(notifications)
    db.commit()
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def update_user_profile(db: Session, user: models.User, profile: schemas.UserBase) -> models.User:
    for field, value in profile.dict().items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# Cycle settings

def get_cycle_settings(db: Session, user_id: int) -> Optional[models.CycleSettings]:
    return (
        db.query(models.CycleSettings)
        .filter(models.CycleSettings.user_id == user_id)
        .first()
    )


def upsert_cycle_settings(
    db: Session, user_id: int, data: schemas.CycleSettingsCreate
) -> models.CycleSettings:
    settings = get_cycle_settings(db, user_id)
    if not settings:
        settings = models.CycleSettings(user_id=user_id)
        db.add(settings)

    for field, value in data.dict().items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


# Notification settings

def get_notification_settings(db: Session, user_id: int) -> Optional[models.NotificationSettings]:
    return (
        db.query(models.NotificationSettings)
        .filter(models.NotificationSettings.user_id == user_id)
        .first()
    )


def upsert_notification_settings(
    db: Session, user_id: int, data: schemas.NotificationSettingsCreate
) -> models.NotificationSettings:
    settings = get_notification_settings(db, user_id)
    if not settings:
        settings = models.NotificationSettings(user_id=user_id)
        db.add(settings)

    for field, value in data.dict().items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings


# Period logs

def create_period_log(
    db: Session, user_id: int, period_in: schemas.PeriodLogCreate
) -> models.PeriodLog:
    period = models.PeriodLog(
        user_id=user_id,
        start_date=period_in.start_date,
        end_date=period_in.end_date,
        flow_intensity=period_in.flow_intensity,
        exclude_from_stats=period_in.exclude_from_stats,
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def list_period_logs(db: Session, user_id: int) -> list[models.PeriodLog]:
    return (
        db.query(models.PeriodLog)
        .filter(models.PeriodLog.user_id == user_id)
        .order_by(models.PeriodLog.start_date.asc())
        .all()
    )


def update_period_log(
    db: Session, user_id: int, period_id: int, updates: schemas.PeriodLogUpdate
) -> Optional[models.PeriodLog]:
    period = (
        db.query(models.PeriodLog)
        .filter(
            models.PeriodLog.id == period_id,
            models.PeriodLog.user_id == user_id,
        )
        .first()
    )
    if not period:
        return None

    data = updates.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(period, field, value)
    db.commit()
    db.refresh(period)
    return period


# Export / delete

def delete_user_and_data(db: Session, user_id: int) -> None:
    user = get_user(db, user_id)
    if not user:
        return
    db.delete(user)
    db.commit()


def create_password_reset_token(db: Session, user: models.User, ttl_minutes: int = 30) -> PasswordResetToken:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
    prt = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at,
        used=False,
    )
    db.add(prt)
    db.commit()
    db.refresh(prt)
    return prt


def get_valid_reset_token(db: Session, token: str) -> Optional[PasswordResetToken]:
    now = datetime.utcnow()
    return (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token == token,
            PasswordResetToken.used.is_(False),
            PasswordResetToken.expires_at > now,
        )
        .first()
    )


def mark_reset_token_used(db: Session, prt: PasswordResetToken) -> None:
    prt.used = True
    db.commit()

def set_user_password(db: Session, user: models.User, new_password: str) -> models.User:
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user
