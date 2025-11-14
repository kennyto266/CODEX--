"""
邮件自动发送模块

实现邮件自动发送功能，支持：
- SMTP配置
- 多收件人支持
- 附件发送
- HTML邮件模板
- 邮件个性化
- 发送状态跟踪
- 退信处理
"""

import smtplib
import ssl
import os
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from jinja2 import Template, Environment, FileSystemLoader
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .params import EmailConfig, ReportParams, get_params_manager

logger = logging.getLogger(__name__)


@dataclass
class EmailAttachment:
    """邮件附件"""
    filename: str
    path: str
    content_type: Optional[str] = None
    content_id: Optional[str] = None


@dataclass
class EmailSendResult:
    """邮件发送结果"""
    success: bool
    message: str
    error: Optional[str] = None
    recipients: List[str] = None
    attachments_count: int = 0
    send_time: float = 0.0
    email_id: str = ""


class EmailTemplate:
    """邮件模板管理器"""

    def __init__(self, template_dir: str = "templates/email"):
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        # 创建Jinja2环境
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # 内置模板
        self._create_default_templates()

    def _create_default_templates(self):
        """创建默认邮件模板"""
        templates = {
            "default.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .footer { background-color: #f1f1f1; padding: 10px; text-align: center; font-size: 12px; }
        .report-summary { background-color: #f9f9f9; padding: 15px; border-left: 4px solid #4CAF50; }
        .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
        .metric { text-align: center; padding: 10px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #4CAF50; }
        .metric-label { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ title }}</h1>
        <p>报告日期: {{ report_date }}</p>
    </div>

    <div class="content">
        <div class="report-summary">
            <h2>报告摘要</h2>
            <p>{{ summary }}</p>
        </div>

        {% if metrics %}
        <h2>关键指标</h2>
        <div class="metrics">
            {% for metric in metrics %}
            <div class="metric">
                <div class="metric-value">{{ metric.value }}</div>
                <div class="metric-label">{{ metric.name }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <h2>详细信息</h2>
        <p>{{ details }}</p>

        {% if next_report_time %}
        <p><strong>下次报告时间:</strong> {{ next_report_time }}</p>
        {% endif %}
    </div>

    <div class="footer">
        <p>{{ signature }}</p>
        <p>此邮件由量化交易系统自动发送</p>
    </div>
</body>
</html>
            """,

            "simple.txt": """
标题: {{ title }}
报告日期: {{ report_date }}

摘要:
{{ summary }}

详细信息:
{{ details }}

{{ signature }}
            """,

            "alert.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>系统告警 - {{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .header { background-color: #f44336; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; }
        .alert-box { background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
        .error-box { background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚠️ 系统告警</h1>
        <p>{{ alert_type }}</p>
    </div>

    <div class="content">
        <div class="{{ 'error-box' if alert_type == '错误' else 'alert-box' }}">
            <h2>{{ title }}</h2>
            <p>{{ message }}</p>
        </div>

        <h3>时间</h3>
        <p>{{ timestamp }}</p>

        <h3>详情</h3>
        <p>{{ details }}</p>
    </div>
</body>
</html>
            """
        }

        for template_name, content in templates.items():
            template_path = self.template_dir / template_name
            if not template_path.exists():
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)

    def render_template(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """渲染邮件模板"""
        try:
            template = self.env.get_template(template_name)
            return template.render(**variables)
        except Exception as e:
            logger.error(f"渲染模板失败: {e}")
            raise

    def list_templates(self) -> List[str]:
        """列出所有模板"""
        return list(self.env.list_templates())


class EmailDelivery:
    """邮件发送器"""

    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config
        self.template_manager = EmailTemplate()
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 发送历史存储
        self.send_history: List[EmailSendResult] = []

    def set_config(self, config: EmailConfig):
        """设置邮件配置"""
        self.config = config

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: Optional[List[str]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        body_html: bool = False,
        template_name: Optional[str] = None,
        template_vars: Optional[Dict[str, Any]] = None
    ) -> EmailSendResult:
        """发送邮件"""
        if not self.config:
            raise ValueError("邮件配置未设置")

        start_time = time.time()
        email_id = f"email_{int(time.time() * 1000)}"

        try:
            # 设置收件人
            to_recipients = recipients or self.config.recipients
            cc_recipients = cc or self.config.cc
            bcc_recipients = bcc or self.config.bcc

            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.username
            msg['To'] = ', '.join(to_recipients)
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid()

            if cc_recipients:
                msg['Cc'] = ', '.join(cc_recipients)
            if self.config.reply_to:
                msg['Reply-To'] = self.config.reply_to

            # 渲染模板
            if template_name and template_vars:
                body = self.template_manager.render_template(template_name, template_vars)
                if not body_html:
                    # 如果模板是HTML但要求纯文本，需要转换
                    body_html = template_name.endswith('.html')

            # 添加邮件正文
            if body_html:
                # HTML邮件
                msg.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                # 纯文本邮件
                msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 添加附件
            if attachments:
                for attachment in attachments:
                    self._attach_file(msg, attachment)

            # 发送邮件
            send_result = self._send_smtp(msg, to_recipients + cc_recipients + bcc_recipients)
            send_result.email_id = email_id
            send_result.attachments_count = len(attachments) if attachments else 0
            send_result.send_time = time.time() - start_time

            # 保存到历史记录
            self.send_history.append(send_result)

            return send_result

        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return EmailSendResult(
                success=False,
                message=f"发送失败: {str(e)}",
                error=str(e),
                recipients=recipients or [],
                send_time=time.time() - start_time,
                email_id=email_id
            )

    def send_report_email(
        self,
        report_params: ReportParams,
        report_path: str,
        custom_subject: Optional[str] = None
    ) -> EmailSendResult:
        """发送报告邮件"""
        if not report_params.email:
            raise ValueError("报告参数中没有邮件配置")

        # 更新配置
        self.set_config(report_params.email)

        # 准备模板变量
        template_vars = {
            "title": report_params.name,
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": report_params.email.template_variables.get("summary", ""),
            "metrics": report_params.email.template_variables.get("metrics", []),
            "details": report_params.email.template_variables.get("details", ""),
            "next_report_time": report_params.email.template_variables.get("next_report_time", ""),
            "signature": report_params.email.signature
        }

        # 生成主题
        subject = custom_subject or report_params.email.subject_template.format(
            report_date=template_vars["report_date"]
        )

        # 创建附件
        attachment = EmailAttachment(
            filename=Path(report_path).name,
            path=report_path
        )

        # 选择模板
        template_name = "default.html" if report_params.template.format == "html" else "simple.txt"

        # 发送邮件
        return self.send_email(
            subject=subject,
            body="",  # 使用模板
            body_html=template_name.endswith('.html'),
            template_name=template_name,
            template_vars=template_vars,
            attachments=[attachment]
        )

    def _send_smtp(self, msg: MIMEMultipart, recipients: List[str]) -> EmailSendResult:
        """通过SMTP发送邮件"""
        try:
            if self.config.use_tls:
                # 使用SSL/TLS
                context = ssl.create_default_context()
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
                server.starttls(context=context)
            else:
                # 常规连接
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)

            server.login(self.config.username, self.config.password)
            text = msg.as_string()
            server.sendmail(self.config.username, recipients, text)
            server.quit()

            logger.info(f"邮件发送成功，收件人: {recipients}")
            return EmailSendResult(
                success=True,
                message="邮件发送成功",
                recipients=recipients
            )

        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return EmailSendResult(
                success=False,
                message=f"SMTP发送失败: {str(e)}",
                error=str(e),
                recipients=recipients
            )
        except Exception as e:
            logger.error(f"邮件发送异常: {e}")
            return EmailSendResult(
                success=False,
                message=f"邮件发送失败: {str(e)}",
                error=str(e),
                recipients=recipients
            )

    def _attach_file(self, msg: MIMEMultipart, attachment: EmailAttachment):
        """添加附件到邮件"""
        try:
            with open(attachment.path, "rb") as f:
                file_data = f.read()

            # 猜测MIME类型
            if attachment.content_type is None:
                content_type, _ = mimetypes.guess_type(attachment.path)
                if content_type is None:
                    content_type = 'application/octet-stream'

            # 创建MIME对象
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(file_data)
            encoders.encode_base64(part)

            # 设置文件名
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment.filename}'
            )

            if attachment.content_id:
                part.add_header('Content-ID', f'<{attachment.content_id}>')

            msg.attach(part)

        except Exception as e:
            logger.error(f"添加附件失败: {attachment.path}, {e}")
            raise

    def test_connection(self) -> bool:
        """测试SMTP连接"""
        try:
            if self.config.use_tls:
                context = ssl.create_default_context()
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.config.username, self.config.password)
            else:
                with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                    server.login(self.config.username, self.config.password)

            logger.info("SMTP连接测试成功")
            return True

        except Exception as e:
            logger.error(f"SMTP连接测试失败: {e}")
            return False

    def get_send_history(self, limit: int = 100) -> List[EmailSendResult]:
        """获取发送历史"""
        return self.send_history[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """获取发送统计"""
        total = len(self.send_history)
        success = sum(1 for r in self.send_history if r.success)
        failed = total - success

        total_time = sum(r.send_time for r in self.send_history)
        avg_time = total_time / total if total > 0 else 0

        return {
            "total_sent": total,
            "success_count": success,
            "failed_count": failed,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0,
            "average_send_time": round(avg_time, 2),
            "config": {
                "smtp_server": self.config.smtp_server if self.config else None,
                "smtp_port": self.config.smtp_port if self.config else None,
                "username": self.config.username if self.config else None
            }
        }

    def batch_send(
        self,
        email_configs: List[EmailConfig],
        subject: str,
        body: str,
        body_html: bool = False
    ) -> List[EmailSendResult]:
        """批量发送邮件"""
        results = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_config = {
                executor.submit(self._send_single, config, subject, body, body_html): config
                for config in email_configs
            }

            for future in as_completed(future_to_config):
                result = future.result()
                results.append(result)

        return results

    def _send_single(
        self,
        config: EmailConfig,
        subject: str,
        body: str,
        body_html: bool
    ) -> EmailSendResult:
        """发送单封邮件（用于批量发送）"""
        old_config = self.config
        try:
            self.config = config
            return self.send_email(subject, body, body_html=body_html)
        finally:
            self.config = old_config


class EmailAlertManager:
    """邮件告警管理器"""

    def __init__(self, email_delivery: EmailDelivery):
        self.email_delivery = email_delivery
        self.alert_templates = {
            "error": "alert.html",
            "warning": "alert.html",
            "info": "default.html"
        }

    def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        details: str = "",
        recipients: Optional[List[str]] = None
    ) -> EmailSendResult:
        """发送告警邮件"""
        template_name = self.alert_templates.get(alert_type, "alert.html")

        template_vars = {
            "title": title,
            "alert_type": alert_type.upper(),
            "message": message,
            "details": details,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "signature": "系统自动告警"
        }

        return self.email_delivery.send_email(
            subject=f"[{alert_type.upper()}] {title}",
            body="",
            body_html=True,
            template_name=template_name,
            template_vars=template_vars,
            recipients=recipients
        )

    def send_error_alert(
        self,
        title: str,
        error: str,
        context: str = "",
        recipients: Optional[List[str]] = None
    ) -> EmailSendResult:
        """发送错误告警"""
        return self.send_alert(
            alert_type="error",
            title=title,
            message=f"系统发生错误: {error}",
            details=context,
            recipients=recipients
        )

    def send_warning_alert(
        self,
        title: str,
        warning: str,
        details: str = "",
        recipients: Optional[List[str]] = None
    ) -> EmailSendResult:
        """发送警告告警"""
        return self.send_alert(
            alert_type="warning",
            title=title,
            message=warning,
            details=details,
            recipients=recipients
        )


# 创建全局邮件发送器实例
_email_delivery_instance: Optional[EmailDelivery] = None


def get_email_delivery() -> EmailDelivery:
    """获取邮件发送器实例"""
    global _email_delivery_instance
    if _email_delivery_instance is None:
        _email_delivery_instance = EmailDelivery()
    return _email_delivery_instance


if __name__ == "__main__":
    # 示例：使用邮件发送器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建邮件配置
    email_config = EmailConfig(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        username="your_email@gmail.com",
        password="your_app_password",
        recipients=["recipient@example.com"],
        use_tls=True,
        signature="量化交易系统"
    )

    # 创建邮件发送器
    email_delivery = EmailDelivery()
    email_delivery.set_config(email_config)

    # 测试连接
    if email_delivery.test_connection():
        print("SMTP连接成功")

        # 发送简单邮件
        result = email_delivery.send_email(
            subject="测试邮件",
            body="这是一封测试邮件",
            body_html=False
        )
        print(f"发送结果: {result.success}, {result.message}")

        # 发送HTML邮件
        result = email_delivery.send_email(
            subject="HTML邮件测试",
            body="<h1>这是一个HTML邮件</h1>",
            body_html=True
        )
        print(f"HTML邮件发送结果: {result.success}")

        # 发送告警邮件
        alert_manager = EmailAlertManager(email_delivery)
        alert_result = alert_manager.send_error_alert(
            title="系统错误",
            error="数据库连接失败",
            context="详细信息..."
        )
        print(f"告警邮件发送结果: {alert_result.success}")

        # 获取统计信息
        stats = email_delivery.get_statistics()
        print(f"发送统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
