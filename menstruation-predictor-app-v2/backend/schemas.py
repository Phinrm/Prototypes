from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# User & Account

class UserBase(BaseModel):
    email: EmailStr
    age: Optional[int] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    goal: Optional[str] = None
    contraceptive_method: Optional[str] = None
    language: Optional[str] = None
    region: Optional[str] = None
    theme: Optional[str] = "pink"
    data_sharing_consent: bool = False
    app_lock_enabled: bool = False
    wearable_integration_enabled: bool = False


class UserCreate(UserBase):
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


# Settings

class CycleSettingsBase(BaseModel):
    average_cycle_length: int = Field(28, gt=15, lt=60)
    average_period_length: int = Field(5, gt=1, lt=15)
    first_period_start_date: Optional[date] = None
    uses_hormonal_contraceptives: bool = False
    show_fertile_window: bool = True
    irregular_cycle_mode: bool = False
    pregnancy_mode: bool = False
    lactation_mode: bool = False
    tracked_symptoms: Optional[str] = None  # comma-separated


class CycleSettingsCreate(CycleSettingsBase):
    pass


class CycleSettingsResponse(CycleSettingsBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class NotificationSettingsBase(BaseModel):
    notify_period: bool = True
    period_reminder_days_before: int = 2
    notify_period_end: bool = False
    notify_fertile_window: bool = True
    notify_ovulation: bool = True
    notify_daily_log: bool = False
    daily_log_time: Optional[str] = None
    notify_medication: bool = False
    medication_time: Optional[str] = None


class NotificationSettingsCreate(NotificationSettingsBase):
    pass


class NotificationSettingsResponse(NotificationSettingsBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


# Period logs

class PeriodLogBase(BaseModel):
    start_date: date
    end_date: date
    flow_intensity: Optional[str] = None
    exclude_from_stats: bool = False


class PeriodLogCreate(PeriodLogBase):
    pass


class PeriodLogUpdate(BaseModel):
    exclude_from_stats: Optional[bool] = None


class PeriodLogResponse(PeriodLogBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


# Predictions & history

class PredictionResponse(BaseModel):
    next_period_start: Optional[date]
    next_period_end: Optional[date]
    ovulation_day: Optional[date]
    fertile_window_start: Optional[date]
    fertile_window_end: Optional[date]
    cycle_day_today: Optional[int]
    cycle_length_used: Optional[int]
    period_length_used: Optional[int]
    irregular_cycle_mode: bool
    pregnancy_mode: bool
    lactation_mode: bool
    show_fertile_window: bool


class CycleHistoryItem(BaseModel):
    start_date: date
    end_date: date
    cycle_length: Optional[int] = None
    excluded_from_stats: bool = False

    class Config:
        orm_mode = True


class CycleHistoryResponse(BaseModel):
    periods: List[CycleHistoryItem]


# Export

class ExportBundle(BaseModel):
    user: UserProfile
    cycle_settings: Optional[CycleSettingsResponse]
    notification_settings: Optional[NotificationSettingsResponse]
    periods: List[PeriodLogResponse]

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=6)

class FAQRequest(BaseModel):
    question: str
    user_id: int | None = None

class FAQResponse(BaseModel):
    answer: str