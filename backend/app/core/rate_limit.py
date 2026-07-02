"""Rate limiting pour les routes d'authentification sensibles."""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Limites par défaut (par adresse IP)
LIMIT_REGISTER = "5/minute"
LIMIT_LOGIN = "10/minute"
LIMIT_FORGOT_PASSWORD = "5/minute"
LIMIT_RESEND_OTP = "3/minute"
LIMIT_VERIFY_OTP = "10/minute"
LIMIT_RESET_PASSWORD = "5/minute"
LIMIT_OAUTH = "15/minute"
LIMIT_UNSUBSCRIBE = "5/minute"
