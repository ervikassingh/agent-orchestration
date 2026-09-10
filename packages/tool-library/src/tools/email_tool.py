"""Email sending tool — sends emails via SMTP with STARTTLS."""

import smtplib
import ssl
from typing import Any

from base import BaseTool, ToolConfig, ToolResult


class EmailTool(BaseTool):
    """Send an email via SMTP with STARTTLS encryption."""

    def __init__(self) -> None:
        super().__init__(
            ToolConfig(name="send_email", description="Send an email to one or more recipients")
        )

    async def run(self, input_data: dict[str, Any]) -> ToolResult:
        to = input_data.get("to", "")
        subject = input_data.get("subject", "")
        body = input_data.get("body", "")
        missing = [k for k, v in [("to", to), ("subject", subject), ("body", body)] if not v]
        if missing:
            return ToolResult(
                self.config.name,
                None,
                success=False,
                error=f"Missing required parameter(s): {', '.join(missing)}",
            )

        from settings import settings

        if not settings.SMTP_HOST or settings.SMTP_HOST == "localhost":
            return ToolResult(
                self.config.name,
                None,
                success=False,
                error=(
                    "SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, "
                    "SMTP_PASSWORD, and SMTP_FROM_EMAIL in your .env file."
                ),
            )

        message = (
            f"From: {settings.SMTP_FROM_EMAIL}\r\nTo: {to}\r\nSubject: {subject}\r\n\r\n{body}"
        )
        try:
            with smtplib.SMTP(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=self.config.timeout_seconds
            ) as server:
                server.starttls(context=ssl.create_default_context())
                if settings.SMTP_USERNAME:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(
                    settings.SMTP_FROM_EMAIL, [addr.strip() for addr in to.split(",")], message
                )
        except smtplib.SMTPAuthenticationError:
            return ToolResult(
                self.config.name, None, success=False, error="SMTP authentication failed."
            )
        except (smtplib.SMTPException, OSError) as exc:
            return ToolResult(self.config.name, None, success=False, error=f"SMTP error: {exc}")
        return ToolResult(
            self.config.name,
            {"to": to, "subject": subject, "status": "sent"},
            metadata={"from": settings.SMTP_FROM_EMAIL},
        )
