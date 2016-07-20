from email.mime.text import MIMEText
import email.utils
import textwrap
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
        msg = MIMEText(textwrap.dedent(body.strip()))
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

    def accept(self, toaddr, server, user, passwd, net):
        msg = """
        Hi,

        Your SuperBNC account request has been accepted. Your account details are:

        BNC Server: {0}
        Username: {1}
        Password: {2}
        IRC Network: {3}

        Thanks for choosing SuperBNC.

        Regards,
        SuperBNC Team
        support@superbnc.com
        """.format(server, user, passwd, net)
        self.send(toaddr, "Your SuperBNC account details", msg)

    def reject(self, toaddr, reason):
        msg = """
        Hi,

        Your SuperBNC account request has been rejected. The reason given was:

        {0}

        If you would like to discuss this, please email us at support@superbnc.com or join one of our channels (see https://superbnc.com/channels/ for a list)

        Regards,
        SuperBNC Team
        support@superbnc.com
        """.format(reason)
        self.send(toaddr, "SuperBNC request rejected", msg)
