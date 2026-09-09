"""Email sending tool — sends emails via SMTP with STARTTLS."""

import smtplib
import ssl

from tool_library.base import BaseTool, ToolConfig, ToolResult


class EmailTool(BaseTool):
    """Send an email via SMTP with STARTTLS encryption."""

    def __init__(self) -> None:
        config = ToolConfig(
            name="send_email",
            description="Send an email to one or more recipients",
            timeout_seconds=30.0,
        )
        super().__init__(config)

    async def run(self, input_data: dict) -> ToolResult:
        to: str = input_data.get("to", "")
        subject: str = input_data.get("subject", "")
        body: str = input_data.get("body", "")

        missing = [k for k, v in [("to", to), ("subject", subject), ("body", body)] if not v]
        if missing:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"Missing required parameter(s): {', '.join(missing)}",
            )

        # Lazy import to avoid circular dependency at module level
        from core_agent.settings import settings  # noqa: PLC0415

        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_username = settings.SMTP_USERNAME
        smtp_password = settings.SMTP_PASSWORD
        from_email = settings.SMTP_FROM_EMAIL

        if not smtp_host or smtp_host == "localhost":
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=(
                    "SMTP is not configured. Set SMTP_HOST, SMTP_USERNAME, "
                    "SMTP_PASSWORD, and SMTP_FROM_EMAIL in your .env file."
                ),
            )

        message = (
            f"From: {from_email}\r\n"
            f"To: {to}\r\n"
            f"Subject: {subject}\r\n"
            f"\r\n{body}"
        )

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_host, smtp_port, timeout=self.config.timeout_seconds) as server:
                server.starttls(context=context)
                if smtp_username:
                    server.login(smtp_username, smtp_password)
                server.sendmail(from_email, [addr.strip() for addr in to.split(",")], message)
        except smtplib.SMTPAuthenticationError:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error="SMTP authentication failed. Check SMTP_USERNAME and SMTP_PASSWORD.",
            )
        except smtplib.SMTPException as exc:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"SMTP error: {exc}",
            )
        except OSError as exc:
            return ToolResult(
                tool_name=self.config.name,
                output=None,
                success=False,
                error=f"Connection error: {exc}",
            )

        return ToolResult(
            tool_name=self.config.name,
            output={"to": to, "subject": subject, "status": "sent"},
            metadata={"from": from_email},
        )
