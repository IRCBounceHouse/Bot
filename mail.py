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

To confirm your IRCBounceHouse account request, send the following in our channel:

!verify {0}

Thanks for choosing IRCBounceHouse.

Regards,
IRCBounceHouse Team
admin@ircbouncehouse.com
        """.format(code)
        self.send(toaddr, "IRCBounceHouse account verification", msg)

    def accept(self, toaddr, user, passwd):
        msg = """
Hi,

Your IRCBounceHouse account request has been accepted. Your account details are:

Username: {0}
Password: {1}

Please change your password once you login. Thanks for choosing IRCBounceHouse.

Regards,
IRCBounceHouse Team
admin@ircbouncehouse.com
        """.format(user, passwd)
        self.send(toaddr, "Your IRCBounceHouse account details", msg)

    def reject(self, toaddr, reason):
        msg = """
Hi,

Your IRCBounceHouseC account request has been rejected. The reason given was:

{0}

If you would like to discuss this, please email us at admin@ircbouncehouse.com or join #IRCBounceHouse@irc.spotchat.org

Regards,
IRCBounceHouse Team
admin@ircbouncehouse.com
        """.format(reason)
        self.send(toaddr, "IRCBounceHouse request rejected", msg)
