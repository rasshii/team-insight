"""
メール送信サービス

このモジュールは、メール送信機能を提供します。
メール検証、通知、その他のメール送信機能をサポートします。
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """メール送信サービスクラス"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.use_tls = settings.SMTP_TLS
        self.use_ssl = settings.SMTP_SSL
    
    def _create_smtp_connection(self):
        """SMTP接続を作成"""
        if self.use_ssl:
            smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
        else:
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
        if self.use_tls and not self.use_ssl:
            smtp.starttls()
            
        if self.smtp_user and self.smtp_password:
            smtp.login(self.smtp_user, self.smtp_password)
            
        return smtp
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        メールを送信
        
        Args:
            to_email: 送信先メールアドレス
            subject: 件名
            html_content: HTMLコンテンツ
            text_content: テキストコンテンツ（オプション）
            cc: CCメールアドレスリスト
            bcc: BCCメールアドレスリスト
            
        Returns:
            bool: 送信成功の場合True
        """
        try:
            # メールメッセージを作成
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # テキストパートを追加
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # HTMLパートを追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 受信者リストを作成
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # メール送信
            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg, from_addr=self.from_email, to_addrs=recipients)
            
            logger.info(f"メール送信成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"メール送信エラー: {str(e)}", exc_info=True)
            return False
    
    def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_url: str
    ) -> bool:
        """
        メール検証メールを送信
        
        Args:
            to_email: 送信先メールアドレス
            user_name: ユーザー名
            verification_url: 検証URL
            
        Returns:
            bool: 送信成功の場合True
        """
        subject = "Team Insight - メールアドレスの確認"
        
        # HTMLテンプレート
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background-color: #4F46E5;
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }
                .content {
                    background-color: #f9fafb;
                    padding: 40px;
                    border-radius: 0 0 10px 10px;
                }
                .button {
                    display: inline-block;
                    background-color: #4F46E5;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Team Insight</h1>
            </div>
            <div class="content">
                <h2>メールアドレスの確認</h2>
                <p>こんにちは、{{ user_name }}さん</p>
                <p>Team Insightへのご登録ありがとうございます。</p>
                <p>以下のボタンをクリックして、メールアドレスを確認してください：</p>
                <p style="text-align: center;">
                    <a href="{{ verification_url }}" class="button">メールアドレスを確認</a>
                </p>
                <p>または、以下のURLをブラウザにコピー＆ペーストしてください：</p>
                <p style="word-break: break-all; background-color: #e5e7eb; padding: 10px; border-radius: 5px;">
                    {{ verification_url }}
                </p>
                <p>このリンクは24時間有効です。</p>
                <div class="footer">
                    <p>このメールに心当たりがない場合は、無視してください。</p>
                    <p>&copy; 2025 Team Insight. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # テキストテンプレート
        text_template = """
こんにちは、{{ user_name }}さん

Team Insightへのご登録ありがとうございます。

以下のURLをクリックして、メールアドレスを確認してください：
{{ verification_url }}

このリンクは24時間有効です。

このメールに心当たりがない場合は、無視してください。

Team Insight
        """
        
        # テンプレートをレンダリング
        html_content = Template(html_template).render(
            user_name=user_name,
            verification_url=verification_url
        )
        text_content = Template(text_template).render(
            user_name=user_name,
            verification_url=verification_url
        )
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
    
    def send_verification_success_email(
        self,
        to_email: str,
        user_name: str
    ) -> bool:
        """
        メール検証成功通知メールを送信
        
        Args:
            to_email: 送信先メールアドレス
            user_name: ユーザー名
            
        Returns:
            bool: 送信成功の場合True
        """
        subject = "Team Insight - メールアドレスの確認が完了しました"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .header {
                    background-color: #10B981;
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }
                .content {
                    background-color: #f9fafb;
                    padding: 40px;
                    border-radius: 0 0 10px 10px;
                }
                .button {
                    display: inline-block;
                    background-color: #4F46E5;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .footer {
                    margin-top: 30px;
                    text-align: center;
                    color: #666;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>メールアドレスの確認が完了しました</h1>
            </div>
            <div class="content">
                <h2>ようこそ、{{ user_name }}さん！</h2>
                <p>メールアドレスの確認が正常に完了しました。</p>
                <p>これでTeam Insightのすべての機能をご利用いただけます。</p>
                <p style="text-align: center;">
                    <a href="{{ email_frontend_url }}/dashboard" class="button">ダッシュボードへ</a>
                </p>
                <div class="footer">
                    <p>&copy; 2025 Team Insight. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_template = """
ようこそ、{{ user_name }}さん！

メールアドレスの確認が正常に完了しました。
これでTeam Insightのすべての機能をご利用いただけます。

ダッシュボードへアクセス: {{ email_frontend_url }}/dashboard

Team Insight
        """
        
        html_content = Template(html_template).render(
            user_name=user_name,
            email_frontend_url=settings.EMAIL_FRONTEND_URL
        )
        text_content = Template(text_template).render(
            user_name=user_name,
            email_frontend_url=settings.EMAIL_FRONTEND_URL
        )
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )


# シングルトンインスタンス
email_service = EmailService()