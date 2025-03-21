from django.core.mail import EmailMessage
import logging
from rest_framework_simplejwt.tokens import AccessToken
from datetime import timedelta
from Template import settings
from users.models import User

logger = logging.getLogger(__name__)

class PasswordResetToken(AccessToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token['uid'] = str(user.id)
        token['scope'] = 'password_reset'
        token.set_exp(lifetime=timedelta(days=7))
        return token

def send_email(to_email, subject, body, cc=None, bcc=None, from_email=None):
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    if cc:
        cc = list(set(cc) - set(to_email))
    if bcc:
        bcc = list(set(bcc) - set(to_email) - set(cc or []))

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
            cc=cc,
            bcc=bcc,
        )
        email.content_subtype = "html"
        response = email.send(fail_silently=False)
        logger.info(f"Email sent")
        return response
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise

def send_password_reset_email(email):
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        logger.error(f"User with email {email} does not exist")
        return
    
    reset_token = PasswordResetToken.for_user(user)
    print(reset_token)
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={str(reset_token)}"
    html_body = f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Reset Your Password</title>
                    </head>
                    <body>
                        <h2>Reset Your Password</h2>
                        <p>Hi {user.first_name}, {user.last_name}</p>
                        <p>We received a request to reset your password for your <strong>PFU Expense</strong> account. Click the link below to reset your password:</p>
                        <p><a href="{reset_url}">Reset Password</a></p>
                        <p>If you did not request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                        <p>This link will expire in 7 days.</p>
                    </body>
                    </html>
                """

    send_email(
        to_email=user.email,
        subject='Reset Your Password for PFU Expense',
        body=html_body,
    )