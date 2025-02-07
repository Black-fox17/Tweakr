import requests

from app.core.template import email_otp_template
from app.core.constants import EMAIL, BREVO_KEY


class EmailService:
    def __init__(self, otp_expiration: int, sender_email=EMAIL):
        """
        Initializes the EmailService.

        Args:
            ses_client: AWS SES client.
            brevo_api_instance: Brevo API instance.
            sender_email: Sender's email address.
            otp_expiration: OTP expiration time in seconds.
        """
        self.sender_email = sender_email
        self.otp_expiration = otp_expiration

    def send_email(self, to: str, subject: str, message: str, use_brevo: bool = True):
        """
        Sends an email using either AWS SES or Brevo.

        Args:
            to: Recipient email address.
            subject: Email subject.
            message: Email body (text or HTML).
            use_brevo: If True, use Brevo; otherwise, use AWS SES.
        """
        if use_brevo:
            self._send_email_brevo(to, subject, message)


    def _send_email_brevo(self, to: str, subject: str, message: str):
        """Sends an email using Brevo with a direct HTTP POST request."""
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": BREVO_KEY,  # Use your BREVO_KEY constant here
            "content-type": "application/json",
        }
        payload = {
            "sender": {
                "name": "Tweakr | Notifications",
                "email": self.sender_email,  # Use the sender email from the class
            },
            "to": [
                {"email": to, "name": "Recipient Name"}
            ],  # Customize recipient name as needed
            "subject": subject,
            "htmlContent": message,
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
            print(f"Email sent successfully: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending email via Brevo: {e}")

    def send_otp_email(self, to: str, otp_code: str):
        """
        Sends an OTP email with a custom HTML template.

        Args:
            to: Recipient email address.
            otp_code: OTP code to include in the email.
        """
        subject = "Your OTP Code"
        expiration_minutes = self.otp_expiration // 60
        html_content = email_otp_template(
            otp_code=otp_code, expiration_minutes=expiration_minutes
        )
        self.send_email(to, subject, html_content)
