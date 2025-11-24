
import time
from django.conf import settings
from django.core.cache import cache

def rate_limit_key(phone): return f"otp_rate:{phone}"
def otp_key(phone): return f"otp_code:{phone}"

def send_sms(phone: str, message: str):
    provider = getattr(settings, "SMS_PROVIDER", "console")
    print(f"[SMS:{provider}] to {phone}: {message}")
    return True

def request_otp(phone: str) -> str:
    # 3 per 10 minutes
    rlkey = rate_limit_key(phone)
    count = cache.get(rlkey, 0)
    if count >= 3:
        raise ValueError("Too many OTP requests. Try later.")
    code = "%06d" % (int(time.time()*1000) % 1000000)
    cache.set(otp_key(phone), code, timeout=getattr(settings, "OTP_EXPIRY_SECONDS", 300))
    cache.set(rlkey, count + 1, timeout=600)
    send_sms(phone, f"Your GHMS verification code is {code}")
    return code

def verify_otp(phone: str, code: str) -> bool:
    real = cache.get(otp_key(phone))
    return real == code
