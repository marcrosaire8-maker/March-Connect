from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str
    mongodb_db_name: str = "marches_publics_ouest"
    scheduler_hour: int = 6
    scheduler_minute: int = 0
    scheduler_timezone: str = "Africa/Porto-Novo"
    scheduler_test_interval_seconds: int = 0
    scrape_interval_minutes: int = 30
    automation_startup_run: bool = True
    senegal_max_pages: int = 0
    notification_hour: int = 7
    notification_minute: int = 0
    notification_interval_minutes: int = 15
    notification_max_offres_per_email: int = 1
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_from_name: str = "MarchéConnect"
    smtp_use_tls: bool = True
    formspree_url: str = ""
    frontend_url: str = "http://localhost:5173"
    password_reset_expire_hours: int = 1
    password_reset_otp_expire_minutes: int = 10
    password_reset_token_expire_minutes: int = 10
    password_reset_resend_cooldown_seconds: int = 60
    email_verification_otp_expire_minutes: int = 10
    email_verification_resend_cooldown_seconds: int = 60
    jwt_secret: str = "change-me-in-production"
    jwt_expire_minutes: int = 60 * 24 * 7
    admin_email: str = ""
    admin_password: str = ""
    google_client_id: str = ""
    apple_client_id: str = ""


settings = Settings()
