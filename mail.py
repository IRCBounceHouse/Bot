from email.mime.text import MIMEText
import email.utils
import smtplib

class Mail(object):

    def __init__(self, config):
        self.config = config
        self.host = self.config["host"]
        self.port = self.config["port"]
        self.user = self.config["user"]
        self.passwd = self.config["pass"]
        self.ssl = self.config.get("ssl", False)
        self.starttls = self.config.get("starttls", False)
        self.fromaddr = self.config.get("from", self.user)

    def connect(self):
        if self.ssl:
            self.smtp = smtplib.SMTP_SSL(self.host, self.port)
        else:
            self.smtp = smtplib.SMTP(self.host, self.port)
            if self.starttls:
                self.smtp.starttls()
        self.smtp.login(self.user, self.passwd)

    def send(self, toaddrs, subject, body):
        self.connect()
        msg = MIMEText(body)
        msg["From"] = self.fromaddr
        if type(toaddrs) is list:
            msg["To"] = ", ".join(toaddrs)
        else:
            msg["To"] = toaddrs
        msg["Subject"] = subject
        msg["Date"] = email.utils.formatdate()
        self.smtp.send_message(msg)
        self.smtp.quit()

    def verify(self, toaddr, code):
        msg = """
            Hi,

            To confirm your SuperBNC account request, send the following in one of our channels.

            !verify {0}

            Thanks for choosing SuperBNC.

            Regards,
            SuperBNC Team
            support@superbnc.com
        """.format(code)
        self.send(toaddr, "SuperBNC account verification", msg)
