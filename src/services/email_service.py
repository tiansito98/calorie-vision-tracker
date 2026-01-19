"""
Email Service
=============
Handles sending weekly digest emails using SendGrid.
"""

from datetime import date, timedelta
from typing import Dict, Optional
import json


class EmailService:
    """Service for sending email notifications and digests."""
    
    def __init__(self, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email
        self.sg = None
        
        if api_key:
            try:
                from sendgrid import SendGridAPIClient
                self.sg = SendGridAPIClient(api_key)
            except ImportError:
                pass
    
    def _generate_digest_html(self, digest_data: Dict) -> str:
        """Generate HTML content for weekly digest email."""
        
        week_start = digest_data.get("week_start", date.today() - timedelta(days=7))
        week_end = digest_data.get("week_end", date.today())
        avg_calories = digest_data.get("avg_daily_calories", 0)
        target = digest_data.get("calorie_target", 2000)
        days_logged = digest_data.get("days_logged", 0)
        days_under = digest_data.get("days_under_target", 0)
        days_over = digest_data.get("days_over_target", 0)
        total_protein = digest_data.get("total_protein_g", 0)
        total_carbs = digest_data.get("total_carbs_g", 0)
        total_fat = digest_data.get("total_fat_g", 0)
        
        # Calculate variance
        variance = avg_calories - target
        variance_color = "#22c55e" if variance <= 0 else "#ef4444"
        variance_text = f"{abs(variance):.0f} under" if variance < 0 else f"{variance:.0f} over"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; padding: 30px; border-radius: 12px 12px 0 0; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 10px 0 0; opacity: 0.9; }}
                .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 12px 12px; }}
                .stat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                .stat-value {{ font-size: 28px; font-weight: bold; color: #3b82f6; }}
                .stat-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; margin-top: 5px; }}
                .highlight {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {variance_color}; }}
                .macro-bar {{ display: flex; gap: 10px; margin: 20px 0; }}
                .macro {{ flex: 1; text-align: center; padding: 15px; background: white; border-radius: 8px; }}
                .macro-value {{ font-size: 18px; font-weight: bold; }}
                .macro-label {{ font-size: 11px; color: #6b7280; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #9ca3af; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Weekly Calorie Report</h1>
                    <p>{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}</p>
                </div>
                
                <div class="content">
                    <div class="highlight">
                        <div style="font-size: 14px; color: #6b7280;">Average Daily Calories</div>
                        <div style="font-size: 36px; font-weight: bold; color: #1f2937;">{avg_calories:,.0f}</div>
                        <div style="color: {variance_color}; font-weight: 500;">{variance_text} target</div>
                    </div>
                    
                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="stat-value">{days_logged}</div>
                            <div class="stat-label">Days Logged</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #22c55e;">{days_under}</div>
                            <div class="stat-label">Days Under Target</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: #ef4444;">{days_over}</div>
                            <div class="stat-label">Days Over Target</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{target:,}</div>
                            <div class="stat-label">Daily Target</div>
                        </div>
                    </div>
                    
                    <h3 style="margin-top: 30px;">Weekly Macros</h3>
                    <div class="macro-bar">
                        <div class="macro">
                            <div class="macro-value" style="color: #ef4444;">{total_protein:.0f}g</div>
                            <div class="macro-label">Protein</div>
                        </div>
                        <div class="macro">
                            <div class="macro-value" style="color: #3b82f6;">{total_carbs:.0f}g</div>
                            <div class="macro-label">Carbs</div>
                        </div>
                        <div class="macro">
                            <div class="macro-value" style="color: #f59e0b;">{total_fat:.0f}g</div>
                            <div class="macro-label">Fat</div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Keep up the great work! 💪</p>
                        <p>Calorie Vision Tracker</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_digest_text(self, digest_data: Dict) -> str:
        """Generate plain text content for weekly digest email."""
        week_start = digest_data.get("week_start", date.today() - timedelta(days=7))
        week_end = digest_data.get("week_end", date.today())
        avg_calories = digest_data.get("avg_daily_calories", 0)
        target = digest_data.get("calorie_target", 2000)
        days_logged = digest_data.get("days_logged", 0)
        
        variance = avg_calories - target
        variance_text = f"{abs(variance):.0f} under" if variance < 0 else f"{variance:.0f} over"
        
        text = f"""
Weekly Calorie Report
{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}

SUMMARY
-------
Average Daily Calories: {avg_calories:,.0f} ({variance_text} target)
Days Logged: {days_logged}
Daily Target: {target:,}

MACROS (Weekly Total)
--------------------
Protein: {digest_data.get('total_protein_g', 0):.0f}g
Carbs: {digest_data.get('total_carbs_g', 0):.0f}g
Fat: {digest_data.get('total_fat_g', 0):.0f}g

Keep up the great work!
- Calorie Vision Tracker
        """
        return text.strip()
    
    def send_weekly_digest(
        self, 
        to_email: str, 
        display_name: str,
        digest_data: Dict
    ) -> Dict:
        """
        Send weekly digest email.
        
        Args:
            to_email: Recipient email address
            display_name: User's display name
            digest_data: Dictionary containing weekly summary data
        
        Returns:
            Dict with success status and any error message
        """
        if not self.sg:
            return {"success": False, "error": "SendGrid not configured"}
        
        try:
            from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
            
            week_start = digest_data.get("week_start", date.today() - timedelta(days=7))
            week_end = digest_data.get("week_end", date.today())
            
            subject = f"📊 Your Weekly Calorie Report ({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})"
            
            message = Mail(
                from_email=Email(self.from_email, "Calorie Vision Tracker"),
                to_emails=To(to_email, display_name),
                subject=subject
            )
            
            message.add_content(Content("text/plain", self._generate_digest_text(digest_data)))
            message.add_content(Content("text/html", self._generate_digest_html(digest_data)))
            
            response = self.sg.send(message)
            
            return {
                "success": response.status_code in [200, 201, 202],
                "status_code": response.status_code
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_reminder(
        self,
        to_email: str,
        meal_type: str,
        display_name: str = ""
    ) -> Dict:
        """
        Send meal logging reminder email.
        
        Args:
            to_email: Recipient email address
            meal_type: Type of meal (breakfast, lunch, dinner, etc.)
            display_name: User's display name
        
        Returns:
            Dict with success status
        """
        if not self.sg:
            return {"success": False, "error": "SendGrid not configured"}
        
        try:
            from sendgrid.helpers.mail import Mail
            
            greeting = f"Hey {display_name}!" if display_name else "Hey!"
            
            subject = f"🍽️ Don't forget to log your {meal_type}!"
            
            html_content = f"""
            <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 20px;">
                <h2>{greeting}</h2>
                <p>Just a friendly reminder to log your <strong>{meal_type}</strong> in Calorie Vision Tracker.</p>
                <p>Taking a quick photo helps you stay on track with your goals! 📸</p>
                <p style="color: #6b7280; font-size: 12px; margin-top: 30px;">
                    You can turn off reminders in your profile settings.
                </p>
            </div>
            """
            
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            response = self.sg.send(message)
            
            return {"success": response.status_code in [200, 201, 202]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}


def create_email_service(api_key: str, from_email: str) -> EmailService:
    """Factory function to create email service."""
    return EmailService(api_key=api_key, from_email=from_email)
