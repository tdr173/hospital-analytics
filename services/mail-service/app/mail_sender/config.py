import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    from_address: str
    from_name: str
    use_tls: str  # "true" (STARTTLS), "ssl" (implicit TLS), or "false"
    timeout: int

    @property
    def use_starttls(self) -> bool:
        return self.use_tls.lower() == "true"

    @property
    def use_ssl(self) -> bool:
        return self.use_tls.lower() == "ssl"


def load_smtp_settings() -> SmtpSettings:
    """Read mail settings from env. Returns the dataclass even if values are
    empty; the sender raises a clear error at send-time if required fields
    are missing."""
    return SmtpSettings(
        host=os.getenv("MAIL_SMTP_HOST", ""),
        port=int(os.getenv("MAIL_SMTP_PORT", "587")),
        username=os.getenv("MAIL_SMTP_USER", ""),
        password=os.getenv("MAIL_SMTP_PASSWORD", ""),
        from_address=os.getenv("MAIL_FROM_ADDRESS", ""),
        from_name=os.getenv("MAIL_FROM_NAME", "Hospital Analytics"),
        use_tls=os.getenv("MAIL_USE_TLS", "true"),
        timeout=int(os.getenv("MAIL_TIMEOUT", "10")),
    )
