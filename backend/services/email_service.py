"""Email service for Titan Trade - sends plan confirmation emails via Gmail SMTP"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

PLAN_FEATURES = {
    "free": ["3 AI signals/day", "Basic market data", "Single timeframe", "5 price alerts"],
    "basic": ["5 AI signals/day", "Crypto + Forex data", "Price alerts (10)", "Trade Journal", "4 Strategy templates"],
    "pro": ["25 AI signals/day", "All markets (Crypto + Forex + Indian)", "Multi-timeframe analysis", "10 Strategy templates", "SL/TP & holding duration", "Titan AI Chat (100 msgs/day)", "50 price alerts", "Priority support"],
    "titan": ["Unlimited AI signals", "All markets + real-time streaming", "All timeframes + confluence scoring", "All strategies + custom strategies", "Advanced SL/TP with invalidation", "Unlimited Titan AI Chat", "Portfolio analytics + P&L tracking", "Trade execution", "Dedicated support + early features"],
}

PLAN_PRICES = {
    "free": {"weekly": "Free", "monthly": "Free"},
    "basic": {"weekly": "INR 499/week", "monthly": "INR 1,499/month"},
    "pro": {"weekly": "INR 999/week", "monthly": "INR 3,499/month"},
    "titan": {"weekly": "INR 1,999/week", "monthly": "INR 6,999/month"},
}


def send_plan_email(gmail_user: str, gmail_password: str, to_email: str, user_name: str, plan_name: str, billing_cycle: str, expires_at: str) -> bool:
    """Send professional plan confirmation email via Gmail SMTP"""
    if not gmail_user or not gmail_password:
        logger.warning("Gmail credentials not configured, skipping email")
        return False
    try:
        features = PLAN_FEATURES.get(plan_name, [])
        price = PLAN_PRICES.get(plan_name, {}).get(billing_cycle, "N/A")
        features_html = "".join([f'<li style="padding:4px 0;color:#d1d5db;">{f}</li>' for f in features])

        html = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#0a0a0f;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:520px;margin:0 auto;padding:32px 24px;">
  <div style="text-align:center;padding-bottom:24px;border-bottom:1px solid #1f2937;">
    <h1 style="margin:0;color:#fff;font-size:22px;font-weight:800;letter-spacing:-0.02em;">TITAN TRADE</h1>
    <p style="margin:4px 0 0;color:#6366F1;font-size:10px;letter-spacing:0.2em;">TRADING INTELLIGENCE</p>
  </div>
  <div style="padding:28px 0;">
    <h2 style="color:#00FF94;font-size:18px;margin:0 0 8px;">Plan Activated</h2>
    <p style="color:#9ca3af;font-size:14px;margin:0 0 20px;">Hello {user_name or 'Trader'},</p>
    <p style="color:#d1d5db;font-size:14px;line-height:1.6;margin:0 0 20px;">
      Your <strong style="color:#fff;text-transform:capitalize;">{plan_name}</strong> plan has been successfully activated.
    </p>
    <div style="background:#111827;border:1px solid #1f2937;border-radius:12px;padding:20px;margin-bottom:20px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Plan</td><td style="color:#fff;font-size:14px;font-weight:600;text-align:right;text-transform:capitalize;">{plan_name}</td></tr>
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Billing</td><td style="color:#fff;font-size:14px;text-align:right;text-transform:capitalize;">{billing_cycle}</td></tr>
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Price</td><td style="color:#6366F1;font-size:14px;font-weight:600;text-align:right;">{price}</td></tr>
        <tr><td style="color:#6b7280;font-size:12px;padding:6px 0;">Valid Until</td><td style="color:#FFD700;font-size:14px;text-align:right;">{expires_at[:10]}</td></tr>
      </table>
    </div>
    <div style="margin-bottom:20px;">
      <p style="color:#9ca3af;font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;margin:0 0 8px;">Your Features:</p>
      <ul style="margin:0;padding:0 0 0 20px;font-size:13px;line-height:1.8;">{features_html}</ul>
    </div>
  </div>
  <div style="border-top:1px solid #1f2937;padding-top:16px;text-align:center;">
    <p style="color:#4b5563;font-size:10px;margin:0;">Titan Trade | Trading Intelligence Platform</p>
  </div>
</div>
</body>
</html>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Titan Trade - Your {plan_name.capitalize()} Plan is Active"
        msg['From'] = f"Titan Trade <{gmail_user}>"
        msg['To'] = to_email
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        logger.info(f"Plan email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send plan email to {to_email}: {e}")
        return False
