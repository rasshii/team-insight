"""
レポート配信用メールサービス

このモジュールは、分析レポートの配信に特化したメール送信機能を提供します。
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from jinja2 import Template
from datetime import datetime
import io

from app.core.config import settings

logger = logging.getLogger(__name__)


class ReportEmailService:
    """レポート配信用メールサービスクラス"""
    
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
    
    def send_report(
        self,
        to_email: str,
        report_type: str,
        report_data: Dict[str, Any],
        attachments: Optional[List[Dict[str, Any]]] = None,
        cc: Optional[List[str]] = None,
    ) -> bool:
        """
        分析レポートを送信
        
        Args:
            to_email: 送信先メールアドレス
            report_type: レポートタイプ（weekly, monthly, daily）
            report_data: レポートデータ
            attachments: 添付ファイルリスト [{filename: str, content: bytes, mimetype: str}]
            cc: CCメールアドレスリスト
            
        Returns:
            bool: 送信成功の場合True
        """
        try:
            # 件名を設定
            subject = self._get_report_subject(report_type, report_data)
            
            # メールコンテンツを生成
            html_content = self._generate_html_report(report_type, report_data)
            text_content = self._generate_text_report(report_type, report_data)
            
            # メールメッセージを作成
            msg = MIMEMultipart('mixed')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # 本文部分を作成
            msg_alternative = MIMEMultipart('alternative')
            
            # テキストパートを追加
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg_alternative.attach(text_part)
            
            # HTMLパートを追加
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg_alternative.attach(html_part)
            
            msg.attach(msg_alternative)
            
            # 添付ファイルを追加
            if attachments:
                for attachment in attachments:
                    self._attach_file(msg, attachment)
            
            # 受信者リストを作成
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            
            # メール送信
            with self._create_smtp_connection() as smtp:
                smtp.send_message(msg, from_addr=self.from_email, to_addrs=recipients)
            
            logger.info(f"レポート送信成功: {to_email} - タイプ: {report_type}")
            return True
            
        except Exception as e:
            logger.error(f"レポート送信エラー: {str(e)}", exc_info=True)
            return False
    
    def _get_report_subject(self, report_type: str, report_data: Dict[str, Any]) -> str:
        """レポートの件名を生成"""
        date_str = datetime.now().strftime("%Y年%m月%d日")
        
        if report_type == "daily":
            return f"[Team Insight] 日次レポート - {date_str}"
        elif report_type == "weekly":
            week_str = report_data.get("week_range", "")
            return f"[Team Insight] 週次レポート - {week_str}"
        elif report_type == "monthly":
            month_str = report_data.get("month", datetime.now().strftime("%Y年%m月"))
            return f"[Team Insight] 月次レポート - {month_str}"
        else:
            return f"[Team Insight] 分析レポート - {date_str}"
    
    def _generate_html_report(self, report_type: str, report_data: Dict[str, Any]) -> str:
        """HTMLレポートを生成"""
        template = self._get_html_template(report_type)
        return Template(template).render(**report_data)
    
    def _generate_text_report(self, report_type: str, report_data: Dict[str, Any]) -> str:
        """テキストレポートを生成"""
        template = self._get_text_template(report_type)
        return Template(template).render(**report_data)
    
    def _get_html_template(self, report_type: str) -> str:
        """HTMLテンプレートを取得"""
        import os
        from pathlib import Path
        
        # テンプレートファイルのパスを構築
        template_dir = Path(__file__).parent.parent / "templates" / "reports"
        template_file = template_dir / f"personal_{report_type}.html"
        
        # テンプレートファイルが存在する場合は読み込む
        if template_file.exists():
            with open(template_file, 'r', encoding='utf-8') as f:
                return f.read()
        
        # デフォルトテンプレート
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
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
                .metric {
                    background-color: white;
                    padding: 20px;
                    margin: 10px 0;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
                }
                .metric-value {
                    font-size: 28px;
                    font-weight: bold;
                    color: #4F46E5;
                }
                .metric-label {
                    color: #666;
                    font-size: 14px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e5e7eb;
                }
                th {
                    background-color: #f3f4f6;
                    font-weight: 600;
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
                <h1>Team Insight {{ report_type_label }} レポート</h1>
                <p>{{ report_period }}</p>
            </div>
            <div class="content">
                <h2>サマリー</h2>
                
                <div class="metric">
                    <div class="metric-label">完了タスク数</div>
                    <div class="metric-value">{{ completed_tasks }}</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">平均サイクルタイム</div>
                    <div class="metric-value">{{ avg_cycle_time }} 日</div>
                </div>
                
                <div class="metric">
                    <div class="metric-label">チーム生産性スコア</div>
                    <div class="metric-value">{{ productivity_score }}/100</div>
                </div>
                
                {% if top_performers %}
                <h2>トップパフォーマー</h2>
                <table>
                    <thead>
                        <tr>
                            <th>メンバー</th>
                            <th>完了タスク数</th>
                            <th>平均完了時間</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for performer in top_performers %}
                        <tr>
                            <td>{{ performer.name }}</td>
                            <td>{{ performer.completed_tasks }}</td>
                            <td>{{ performer.avg_completion_time }} 日</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% endif %}
                
                <div class="footer">
                    <p>詳細な分析結果は<a href="{{ dashboard_url }}">ダッシュボード</a>でご確認ください。</p>
                    <p>&copy; 2025 Team Insight. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_text_template(self, report_type: str) -> str:
        """テキストテンプレートを取得"""
        # TODO: 実際のテンプレートファイルから読み込む
        return """
Team Insight {{ report_type_label }} レポート
{{ report_period }}

======================
サマリー
======================

完了タスク数: {{ completed_tasks }}
平均サイクルタイム: {{ avg_cycle_time }} 日
チーム生産性スコア: {{ productivity_score }}/100

{% if top_performers %}
======================
トップパフォーマー
======================
{% for performer in top_performers %}
- {{ performer.name }}: {{ performer.completed_tasks }} タスク完了（平均 {{ performer.avg_completion_time }} 日）
{% endfor %}
{% endif %}

詳細な分析結果はダッシュボードでご確認ください:
{{ dashboard_url }}

Team Insight
        """
    
    def _attach_file(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """ファイルを添付"""
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment['content'])
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment["filename"]}"'
        )
        msg.attach(part)


# シングルトンインスタンス
report_email_service = ReportEmailService()