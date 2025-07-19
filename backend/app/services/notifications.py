import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional
from jinja2 import Template
from datetime import datetime
import asyncio
import asyncpg

class EmailService:
    """
    Service for sending email notifications
    """
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", self.email_user)
        
    def _create_smtp_connection(self):
        """Create SMTP connection"""
        if not self.email_user or not self.email_password:
            raise ValueError("Email credentials not configured")
            
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.email_user, self.email_password)
        return server
    
    def send_email(
        self, 
        to_emails: List[str], 
        subject: str, 
        html_content: str, 
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email to recipients
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = ', '.join(to_emails)
            
            # Add text and HTML content
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_job_completion_notification(
        self, 
        user_email: str, 
        job_name: str, 
        status: str, 
        items_scraped: int = 0,
        error_message: str = None
    ) -> bool:
        """
        Send job completion notification
        """
        subject = f"Trabajo de Crawling {status.title()}: {job_name}"
        
        if status == 'completed':
            html_template = """
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #10b981; margin: 0;">✅ Trabajo Completado</h1>
                        </div>
                        
                        <h2 style="color: #333; margin-bottom: 20px;">{{ job_name }}</h2>
                        
                        <div style="background-color: #f0fdf4; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                            <p style="margin: 0; color: #166534;"><strong>Estado:</strong> Completado exitosamente</p>
                            <p style="margin: 10px 0 0 0; color: #166534;"><strong>Elementos encontrados:</strong> {{ items_scraped }}</p>
                        </div>
                        
                        <p style="color: #666; line-height: 1.5;">
                            Tu trabajo de crawling se ha completado exitosamente. 
                            Los datos están ahora disponibles en tu dashboard.
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{{ dashboard_url }}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                                Ver Dashboard
                            </a>
                        </div>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                            Inmobiliario Tools - {{ timestamp }}
                        </p>
                    </div>
                </body>
            </html>
            """
        else:
            html_template = """
            <html>
                <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #ef4444; margin: 0;">❌ Trabajo Fallido</h1>
                        </div>
                        
                        <h2 style="color: #333; margin-bottom: 20px;">{{ job_name }}</h2>
                        
                        <div style="background-color: #fef2f2; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                            <p style="margin: 0; color: #dc2626;"><strong>Estado:</strong> {{ status.title() }}</p>
                            {% if error_message %}
                            <p style="margin: 10px 0 0 0; color: #dc2626;"><strong>Error:</strong> {{ error_message }}</p>
                            {% endif %}
                        </div>
                        
                        <p style="color: #666; line-height: 1.5;">
                            Tu trabajo de crawling ha fallado. Por favor revisa la configuración 
                            y vuelve a intentarlo.
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px;">
                            <a href="{{ dashboard_url }}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                                Ver Dashboard
                            </a>
                        </div>
                        
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                            Inmobiliario Tools - {{ timestamp }}
                        </p>
                    </div>
                </body>
            </html>
            """
        
        template = Template(html_template)
        html_content = template.render(
            job_name=job_name,
            status=status,
            items_scraped=items_scraped,
            error_message=error_message,
            dashboard_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
            timestamp=datetime.now().strftime("%d/%m/%Y %H:%M")
        )
        
        return self.send_email([user_email], subject, html_content)
    
    def send_weekly_summary(self, user_email: str, summary_data: dict) -> bool:
        """
        Send weekly summary report
        """
        subject = "Resumen Semanal - Inmobiliario Tools"
        
        html_template = """
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #3b82f6; margin: 0;">📊 Resumen Semanal</h1>
                    </div>
                    
                    <p style="color: #666; margin-bottom: 30px;">
                        Aquí tienes el resumen de actividad de la última semana:
                    </p>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">Trabajos Ejecutados</h3>
                        <p style="margin: 5px 0; color: #666;">Total: {{ summary_data.total_jobs }}</p>
                        <p style="margin: 5px 0; color: #10b981;">Exitosos: {{ summary_data.successful_jobs }}</p>
                        <p style="margin: 5px 0; color: #ef4444;">Fallidos: {{ summary_data.failed_jobs }}</p>
                    </div>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">Propiedades Encontradas</h3>
                        <p style="margin: 5px 0; color: #666;">Total: {{ summary_data.total_properties }}</p>
                        <p style="margin: 5px 0; color: #666;">Nuevas esta semana: {{ summary_data.new_properties }}</p>
                    </div>
                    
                    {% if summary_data.top_locations %}
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                        <h3 style="color: #333; margin-top: 0;">Top Ubicaciones</h3>
                        {% for location in summary_data.top_locations %}
                        <p style="margin: 5px 0; color: #666;">{{ location.name }}: {{ location.count }} propiedades</p>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{{ dashboard_url }}" style="background-color: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                            Ver Dashboard Completo
                        </a>
                    </div>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
                        Inmobiliario Tools - {{ timestamp }}
                    </p>
                </div>
            </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            summary_data=summary_data,
            dashboard_url=os.getenv("FRONTEND_URL", "http://localhost:3000"),
            timestamp=datetime.now().strftime("%d/%m/%Y")
        )
        
        return self.send_email([user_email], subject, html_content)

class NotificationManager:
    """
    Manager for handling all notification types
    """
    
    def __init__(self):
        self.email_service = EmailService()
    
    async def notify_job_completion(
        self, 
        job_id: int, 
        status: str, 
        items_scraped: int = 0, 
        error_message: str = None
    ):
        """
        Send notification when a job completes
        """
        try:
            # Get job and user details from database
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
            
            conn = await asyncpg.connect(DATABASE_URL)
            
            row = await conn.fetchrow("""
                SELECT cj.job_name, u.email, u.username
                FROM crawl_jobs cj
                JOIN users u ON cj.created_by = u.user_id
                WHERE cj.job_id = $1
            """, job_id)
            
            if row and row['email']:
                success = self.email_service.send_job_completion_notification(
                    user_email=row['email'],
                    job_name=row['job_name'],
                    status=status,
                    items_scraped=items_scraped,
                    error_message=error_message
                )
                
                if success:
                    print(f"Notification sent to {row['email']} for job {job_id}")
                else:
                    print(f"Failed to send notification for job {job_id}")
            
            await conn.close()
            
        except Exception as e:
            print(f"Error sending job completion notification: {e}")
    
    async def send_weekly_summaries(self):
        """
        Send weekly summary reports to all active users
        """
        try:
            DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@postgres:5432/{os.getenv('POSTGRES_DB', 'inmobiliario_db')}"
            
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Get active users
            users = await conn.fetch("""
                SELECT user_id, email, username 
                FROM users 
                WHERE is_active = true AND email IS NOT NULL
            """)
            
            for user in users:
                # Get user's weekly summary data
                summary_data = await self._get_user_weekly_summary(conn, user['user_id'])
                
                # Send summary email
                success = self.email_service.send_weekly_summary(
                    user_email=user['email'],
                    summary_data=summary_data
                )
                
                if success:
                    print(f"Weekly summary sent to {user['email']}")
                else:
                    print(f"Failed to send weekly summary to {user['email']}")
            
            await conn.close()
            
        except Exception as e:
            print(f"Error sending weekly summaries: {e}")
    
    async def _get_user_weekly_summary(self, conn, user_id: int) -> dict:
        """
        Get weekly summary data for a user
        """
        # Job execution stats
        job_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_jobs,
                COUNT(CASE WHEN je.status = 'completed' THEN 1 END) as successful_jobs,
                COUNT(CASE WHEN je.status = 'failed' THEN 1 END) as failed_jobs,
                SUM(je.items_scraped) as total_items
            FROM job_executions je
            JOIN crawl_jobs cj ON je.job_id = cj.job_id
            WHERE cj.created_by = $1
            AND je.started_at >= NOW() - INTERVAL '7 days'
        """, user_id)
        
        # Property stats
        property_stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_properties,
                COUNT(CASE WHEN fecha_crawl >= NOW() - INTERVAL '7 days' THEN 1 END) as new_properties
            FROM propiedades
        """)
        
        # Top locations
        top_locations = await conn.fetch("""
            SELECT poblacion as name, COUNT(*) as count
            FROM propiedades
            WHERE fecha_crawl >= NOW() - INTERVAL '7 days'
            AND poblacion IS NOT NULL
            GROUP BY poblacion
            ORDER BY count DESC
            LIMIT 5
        """)
        
        return {
            'total_jobs': job_stats['total_jobs'] or 0,
            'successful_jobs': job_stats['successful_jobs'] or 0,
            'failed_jobs': job_stats['failed_jobs'] or 0,
            'total_properties': property_stats['total_properties'] or 0,
            'new_properties': property_stats['new_properties'] or 0,
            'top_locations': [{'name': row['name'], 'count': row['count']} for row in top_locations]
        }

# Global notification manager instance
notification_manager = NotificationManager()