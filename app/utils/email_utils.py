"""
📧 邮件发送工具类
🔷 backend-architect 设计的邮件系统工具函数
"""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from flask import current_app, render_template_string
from jinja2 import Template
import logging


class EmailSender:
    """
    📧 邮件发送器
    支持HTML邮件、附件和模板渲染
    """
    
    def __init__(self):
        """初始化邮件配置"""
        self.smtp_server = current_app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = current_app.config.get('MAIL_PORT', 587)
        self.username = current_app.config.get('MAIL_USERNAME', '')
        self.password = current_app.config.get('MAIL_PASSWORD', '')
        self.use_tls = current_app.config.get('MAIL_USE_TLS', True)
        self.use_ssl = current_app.config.get('MAIL_USE_SSL', False)
        self.sender_name = current_app.config.get('MAIL_SENDER_NAME', '个人门户')
        self.sender_email = current_app.config.get('MAIL_SENDER_EMAIL', self.username)
        
    def send_email(self, to_email, subject, body, html_body=None, attachments=None, cc=None, bcc=None):
        """
        发送邮件
        
        Args:
            to_email: 收件人邮箱地址（字符串或列表）
            subject: 邮件主题
            body: 邮件文本内容
            html_body: 邮件HTML内容（可选）
            attachments: 附件列表（可选）
            cc: 抄送地址（可选）
            bcc: 密抄地址（可选）
            
        Returns:
            tuple: (success, message)
        """
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.sender_name, self.sender_email))
            
            # 处理收件人
            if isinstance(to_email, str):
                msg['To'] = to_email
                recipients = [to_email]
            else:
                msg['To'] = ', '.join(to_email)
                recipients = to_email
            
            # 处理抄送
            if cc:
                if isinstance(cc, str):
                    msg['Cc'] = cc
                    recipients.extend([cc])
                else:
                    msg['Cc'] = ', '.join(cc)
                    recipients.extend(cc)
            
            # 密抄不在邮件头中显示
            if bcc:
                if isinstance(bcc, str):
                    recipients.extend([bcc])
                else:
                    recipients.extend(bcc)
            
            msg['Subject'] = subject
            msg['Date'] = formataddr((datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'), ''))
            
            # 添加文本内容
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # 添加HTML内容
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 添加附件
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # 连接SMTP服务器并发送
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            elif self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            
            server.login(self.username, self.password)
            server.send_message(msg, to_addrs=recipients)
            server.quit()
            
            logging.info(f"邮件发送成功: {subject} -> {recipients}")
            return True, "邮件发送成功"
            
        except Exception as e:
            error_msg = f"邮件发送失败: {str(e)}"
            logging.error(error_msg)
            return False, error_msg
    
    def _add_attachment(self, msg, attachment):
        """
        添加附件到邮件
        
        Args:
            msg: 邮件对象
            attachment: 附件信息 (文件路径或(文件路径, 文件名)元组)
        """
        try:
            if isinstance(attachment, tuple):
                file_path, filename = attachment
            else:
                file_path = attachment
                filename = os.path.basename(file_path)
            
            with open(file_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logging.error(f"添加附件失败: {str(e)}")


# 邮件模板管理
class EmailTemplates:
    """
    📧 邮件模板管理器
    提供预定义的邮件模板
    """
    
    @staticmethod
    def get_inquiry_notification_template():
        """新咨询通知模板（发给管理员）"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .info-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .info-table th, .info-table td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        .info-table th { background: #e9ecef; font-weight: bold; }
        .highlight { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🆕 新的项目咨询</h1>
            <p>有新的项目咨询需要处理</p>
        </div>
        
        <div class="content">
            <div class="highlight">
                <strong>咨询类型：</strong>{{ inquiry.inquiry_type }}<br>
                <strong>咨询主题：</strong>{{ inquiry.subject }}
            </div>
            
            <table class="info-table">
                <tr><th>联系人</th><td>{{ inquiry.name }}</td></tr>
                <tr><th>邮箱</th><td>{{ inquiry.email }}</td></tr>
                {% if inquiry.phone %}<tr><th>电话</th><td>{{ inquiry.phone }}</td></tr>{% endif %}
                {% if inquiry.company %}<tr><th>公司</th><td>{{ inquiry.company }}</td></tr>{% endif %}
                {% if inquiry.position %}<tr><th>职位</th><td>{{ inquiry.position }}</td></tr>{% endif %}
                <tr><th>预算范围</th><td>{{ inquiry.budget_range or '未指定' }}</td></tr>
                <tr><th>期望时间</th><td>{{ inquiry.timeline or '未指定' }}</td></tr>
                <tr><th>联系偏好</th><td>{{ inquiry.contact_preference }}</td></tr>
                <tr><th>方便时间</th><td>{{ inquiry.contact_time }}</td></tr>
            </table>
            
            <h3>📝 详细需求：</h3>
            <div style="background: white; padding: 15px; border-radius: 5px;">
                {{ inquiry.description | nl2br | safe }}
            </div>
            
            {% if inquiry.preferred_tech %}
            <h3>🔧 技术偏好：</h3>
            <p>{{ inquiry.preferred_tech }}</p>
            {% endif %}
            
            {% if inquiry.additional_info %}
            <h3>ℹ️ 补充信息：</h3>
            <p>{{ inquiry.additional_info | nl2br | safe }}</p>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>收到时间：{{ inquiry.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
            <p>请及时登录后台处理此咨询</p>
        </div>
    </div>
</body>
</html>
        """
        return template
    
    @staticmethod
    def get_inquiry_confirmation_template():
        """咨询确认模板（发给客户）"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #28a745; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .info-box { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ 咨询已收到</h1>
            <p>感谢您的项目咨询</p>
        </div>
        
        <div class="content">
            <p>尊敬的 <strong>{{ inquiry.name }}</strong>，</p>
            
            <p>我们已收到您关于"<strong>{{ inquiry.subject }}</strong>"的咨询，感谢您的信任！</p>
            
            <div class="info-box">
                <h3>📋 咨询摘要：</h3>
                <p><strong>咨询类型：</strong>{{ inquiry.inquiry_type }}</p>
                <p><strong>提交时间：</strong>{{ inquiry.created_at.strftime('%Y-%m-%d %H:%M') }}</p>
                {% if inquiry.budget_range %}<p><strong>预算范围：</strong>{{ inquiry.budget_range }}</p>{% endif %}
                {% if inquiry.timeline %}<p><strong>期望时间：</strong>{{ inquiry.timeline }}</p>{% endif %}
            </div>
            
            <h3>🚀 接下来的步骤：</h3>
            <ol>
                <li><strong>需求评估</strong> - 我们将仔细分析您的需求</li>
                <li><strong>方案制定</strong> - 为您量身定制解决方案</li>
                <li><strong>沟通确认</strong> - 与您详细讨论技术细节</li>
                <li><strong>项目启动</strong> - 确定合作后正式开始项目</li>
            </ol>
            
            <div class="info-box">
                <h3>⏰ 预期回复时间：</h3>
                <p>我们通常在 <strong>24-48小时内</strong> 回复您的咨询。如果是复杂项目，可能需要更多时间进行详细评估。</p>
                <p>我们会通过 <strong>{{ inquiry.contact_preference }}</strong> 与您联系。</p>
            </div>
            
            <p>如果您有任何紧急问题或需要补充信息，请直接回复此邮件。</p>
            
            <p>再次感谢您的咨询，期待与您的合作！</p>
            
            <p>此致<br>
            敬礼！</p>
        </div>
        
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复</p>
            <p>如有问题请通过原咨询邮箱联系</p>
        </div>
    </div>
</body>
</html>
        """
        return template
    
    @staticmethod
    def get_inquiry_response_template():
        """咨询回复模板（管理员回复客户）"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .response-box { background: #e7f3ff; padding: 15px; border-left: 4px solid #007bff; margin: 15px 0; }
        .original-inquiry { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 项目咨询回复</h1>
            <p>关于"{{ inquiry.subject }}"的详细回复</p>
        </div>
        
        <div class="content">
            <p>尊敬的 <strong>{{ inquiry.name }}</strong>，</p>
            
            <p>感谢您对我们项目的咨询，以下是针对您需求的详细回复：</p>
            
            <div class="response-box">
                <h3>💬 我们的回复：</h3>
                {{ response.response | nl2br | safe }}
                
                {% if response.estimated_budget %}
                <p><strong>💰 预估费用：</strong>{{ response.estimated_budget }}</p>
                {% endif %}
                
                {% if response.estimated_timeline %}
                <p><strong>⏰ 预估周期：</strong>{{ response.estimated_timeline }}</p>
                {% endif %}
            </div>
            
            <div class="original-inquiry">
                <h3>📋 原始咨询内容：</h3>
                <p><strong>咨询类型：</strong>{{ inquiry.inquiry_type }}</p>
                <p><strong>咨询时间：</strong>{{ inquiry.created_at.strftime('%Y-%m-%d %H:%M') }}</p>
                <p><strong>需求描述：</strong></p>
                <p>{{ inquiry.description | nl2br | safe | truncate(200) }}...</p>
            </div>
            
            {% if response.next_contact_date %}
            <p><strong>📅 后续联系：</strong>我们计划在 {{ response.next_contact_date.strftime('%Y-%m-%d') }} 与您进一步沟通。</p>
            {% endif %}
            
            <p>如果您对我们的回复有任何问题，或需要进一步讨论，请随时联系我们。</p>
            
            <p>期待您的回复！</p>
            
            <p>此致<br>
            敬礼！</p>
        </div>
        
        <div class="footer">
            <p>回复时间：{{ response.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</p>
            <p>您可以直接回复此邮件继续沟通</p>
        </div>
    </div>
</body>
</html>
        """
        return template
    
    @staticmethod
    def get_newsletter_template():
        """邮件订阅模板"""
        template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #6f42c1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .article { border-bottom: 1px solid #eee; padding: 15px 0; }
        .article:last-child { border-bottom: none; }
        .footer { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 技术周报</h1>
            <p>{{ newsletter.title }}</p>
        </div>
        
        <div class="content">
            {{ newsletter.content | safe }}
        </div>
        
        <div class="footer">
            <p>感谢您的订阅！</p>
            <p><a href="{{ unsubscribe_url }}">取消订阅</a></p>
        </div>
    </div>
</body>
</html>
        """
        return template


# 便捷的邮件发送函数
def send_inquiry_notification(inquiry):
    """发送新咨询通知给管理员"""
    try:
        sender = EmailSender()
        template = Template(EmailTemplates.get_inquiry_notification_template())
        
        # 获取管理员邮箱
        admin_email = current_app.config.get('ADMIN_EMAIL', sender.username)
        
        # 渲染模板
        html_body = template.render(inquiry=inquiry)
        
        # 发送邮件
        subject = f"🆕 新的项目咨询：{inquiry.subject}"
        text_body = f"收到来自 {inquiry.name} ({inquiry.email}) 的项目咨询\n\n咨询类型：{inquiry.inquiry_type}\n主题：{inquiry.subject}\n\n详细内容：\n{inquiry.description}"
        
        return sender.send_email(
            to_email=admin_email,
            subject=subject,
            body=text_body,
            html_body=html_body
        )
        
    except Exception as e:
        logging.error(f"发送咨询通知邮件失败: {str(e)}")
        return False, str(e)


def send_inquiry_confirmation(inquiry):
    """发送咨询确认邮件给客户"""
    try:
        sender = EmailSender()
        template = Template(EmailTemplates.get_inquiry_confirmation_template())
        
        # 渲染模板
        html_body = template.render(inquiry=inquiry)
        
        # 发送邮件
        subject = f"✅ 咨询确认：{inquiry.subject}"
        text_body = f"尊敬的 {inquiry.name}，\n\n我们已收到您关于"{inquiry.subject}"的咨询，感谢您的信任！\n\n我们将在24-48小时内回复您的咨询。\n\n此致\n敬礼！"
        
        return sender.send_email(
            to_email=inquiry.email,
            subject=subject,
            body=text_body,
            html_body=html_body
        )
        
    except Exception as e:
        logging.error(f"发送咨询确认邮件失败: {str(e)}")
        return False, str(e)


def send_inquiry_response(inquiry, response):
    """发送咨询回复邮件给客户"""
    try:
        sender = EmailSender()
        template = Template(EmailTemplates.get_inquiry_response_template())
        
        # 渲染模板
        html_body = template.render(inquiry=inquiry, response=response)
        
        # 发送邮件
        subject = f"📧 Re: {inquiry.subject}"
        text_body = f"尊敬的 {inquiry.name}，\n\n关于您的咨询"{inquiry.subject}"，我们的回复如下：\n\n{response.response}\n\n如有问题请随时联系。\n\n此致\n敬礼！"
        
        return sender.send_email(
            to_email=inquiry.email,
            subject=subject,
            body=text_body,
            html_body=html_body
        )
        
    except Exception as e:
        logging.error(f"发送回复邮件失败: {str(e)}")
        return False, str(e)


def send_newsletter(email, newsletter_data):
    """发送邮件订阅内容"""
    try:
        sender = EmailSender()
        template = Template(EmailTemplates.get_newsletter_template())
        
        # 渲染模板
        html_body = template.render(
            newsletter=newsletter_data,
            unsubscribe_url=f"{current_app.config.get('BASE_URL', '')}/unsubscribe?email={email}"
        )
        
        # 发送邮件
        subject = newsletter_data.get('title', '📚 技术周报')
        text_body = newsletter_data.get('text_content', '请查看HTML版本的邮件内容')
        
        return sender.send_email(
            to_email=email,
            subject=subject,
            body=text_body,
            html_body=html_body
        )
        
    except Exception as e:
        logging.error(f"发送邮件订阅失败: {str(e)}")
        return False, str(e)