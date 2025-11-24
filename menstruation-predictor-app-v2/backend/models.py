from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import DateTime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    age = Column(Integer, nullable=True)
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)

    goal = Column(String, nullable=True)  # track_cycle, conceive, avoid_pregnancy, perimenopause
    contraceptive_method = Column(String, nullable=True)

    language = Column(String, nullable=True)
    region = Column(String, nullable=True)
    theme = Column(String, nullable=True, default="pink")

    data_sharing_consent = Column(Boolean, default=False)
    app_lock_enabled = Column(Boolean, default=False)
    wearable_integration_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    settings = relationship(
        "CycleSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    notifications = relationship(
        "NotificationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    periods = relationship(
        "PeriodLog", back_populates="user", cascade="all, delete-orphan"
    )


class CycleSettings(Base):
    __tablename__ = "cycle_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    average_cycle_length = Column(Integer, nullable=False, default=28)
    average_period_length = Column(Integer, nullable=False, default=5)
    first_period_start_date = Column(Date, nullable=True)
    uses_hormonal_contraceptives = Column(Boolean, default=False)

    show_fertile_window = Column(Boolean, default=True)
    irregular_cycle_mode = Column(Boolean, default=False)
    pregnancy_mode = Column(Boolean, default=False)
    lactation_mode = Column(Boolean, default=False)

    tracked_symptoms = Column(String, nullable=True)  # comma-separated

    user = relationship("User", back_populates="settings")


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    notify_period = Column(Boolean, default=True)
    period_reminder_days_before = Column(Integer, default=2)
    notify_period_end = Column(Boolean, default=False)

    notify_fertile_window = Column(Boolean, default=True)
    notify_ovulation = Column(Boolean, default=True)

    notify_daily_log = Column(Boolean, default=False)
    daily_log_time = Column(String, nullable=True)  # '08:00'

    notify_medication = Column(Boolean, default=False)
    medication_time = Column(String, nullable=True)

    user = relationship("User", back_populates="notifications")


class PeriodLog(Base):
    __tablename__ = "period_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    flow_intensity = Column(String, nullable=True)
    exclude_from_stats = Column(Boolean, default=False)

    user = relationship("User", back_populates="periods")

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)

    user = relationship("User")