# ==============================================================================
"""
    name:           
    description:    
    started:        
    (c) Alfred LEUNG
"""
# ==============================================================================

# ==============================================================================
# Imports
# ==============================================================================
# -System-----------------------------------------------------------------------
import mimetypes
import os.path

from smtplib import SMTP

#weird stuff in the email module, but these imports work fine
# pylint: disable=E0611,E0401
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.image import MIMEImage
from email.encoders import encode_base64
# pylint: enable=E0611,E0401

# -Third party------------------------------------------------------------------
# -Own modules------------------------------------------------------------------
import outils.logger as OuL

# ==============================================================================
# Constants
# ==============================================================================
SMTP_SERVERS = {"gmail": {"server": "smtp.gmail.com", "port": 587}}

SENDERS = {
    "orgmode": {
        "name": "ChunglakBot <chunglakbot@gmail.com>",
        "login": "chunglakbot@gmail.com",
        "password": "ghfbsgdaafyxjabi",
        # "password": "Mai1tre0ya50",
        "smtp": "gmail",
    }
}
RECIPIENTS = {
    "chunglak": "chunglak@gmail.com",
    "chunglak2": "chunglak@hotmail.com",
    "alfred": "alfred.leung@1050capital.com",
    "maman": "lyducsim@gmail.com",
}


# ==============================================================================
#
# ==============================================================================
def send_mail_known(
    sender, recipient, subject=None, body=None, attachments=None, logger=None
):
    logger = OuL.default_logger(logger)
    try:
        send_rec = SENDERS[sender]
    except KeyError:
        logger.error("Unknown sender %s" % sender)
    try:
        rec = RECIPIENTS[recipient]
    except KeyError:
        logger.error("Unknown recipient %s" % recipient)
    smtp = SMTP_SERVERS[send_rec["smtp"]]
    smtp_conn = MySMTPConnection(
        login=send_rec["login"],
        password=send_rec["password"],
        smtp_server=smtp["server"],
        smtp_server_port=smtp["port"],
        name=send_rec["name"],
        logger=logger,
    )
    msg = MyMessage(
        mysmtp_conn=smtp_conn, recipient=rec, subject=subject, logger=logger
    )
    if body:
        msg.add_text(body)
    if attachments:
        for fn in attachments:
            msg.add_file(fn)
    msg.send()


def send_orgmode_message(
    recipient, subject, body=None, body_html=None, atts=None, logger=None
):
    sm = MySMTPConnection.from_known("orgmode")
    msg = MyMessage(mysmtp_conn=sm, subject=subject, recipient=recipient, logger=logger)
    if body:
        msg.add_text(body)
    if body_html:
        msg.add_html(body_html)
    if atts:
        for att in atts:
            msg.add_file(att)
    msg.send()


# ==============================================================================
#
# ==============================================================================
class MySMTPConnection:
    def __init__(
        self, login, password, smtp_server, smtp_server_port, name=None, logger=None
    ):
        self.logger = OuL.default_logger(logger)
        self.server = SMTP(smtp_server, smtp_server_port)
        self.login = login
        self.password = password
        self.name = name if name else login

    def send_message(self, message):
        self.server.ehlo()
        self.server.starttls()
        self.server.login(self.login, self.password)
        self.server.send_message(message)
        self.server.quit()

    @staticmethod
    def from_known(sender, logger=None):
        if sender not in SENDERS:
            return None
        data = SENDERS[sender]
        if not data:
            return None
        smtp = SMTP_SERVERS[data["smtp"]]
        return MySMTPConnection(
            login=data["login"],
            password=data["password"],
            smtp_server=smtp["server"],
            smtp_server_port=smtp["port"],
            name=data["name"],
            logger=logger,
        )


class MyMessage:
    def __init__(self, mysmtp_conn, recipient, subject=None, logger=None):
        self.logger = OuL.default_logger(logger)
        msg = MIMEMultipart()
        msg["From"] = mysmtp_conn.name
        msg["To"] = recipient
        # msg['To']=', '.join(rs)
        msg["Subject"] = subject
        self.message = msg
        self.mysmtp_conn = mysmtp_conn

    def add_text(self, text_content):
        att = MIMEText(text_content, "plain")
        self.message.attach(att)

    def add_html(self, html_content):
        att = MIMEText(html_content, "html")
        self.message.attach(att)

    def add_file(self, fn):
        if not os.path.isfile(fn):
            self.logger.error("No such file %s" % fn)
            return
        ctype, encoding = mimetypes.guess_type(fn)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        if maintype == "text":
            with open(fn) as fp:
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
        elif maintype == "image":
            with open(fn, "rb") as fp:
                msg = MIMEImage(fp.read(), _subtype=subtype)
        elif maintype == "audio":
            with open(fn, "rb") as fp:
                msg = MIMEAudio(fp.read(), _subtype=subtype)
        else:
            with open(fn, "rb") as fp:
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
            # Encode the payload using Base64
            encode_base64(msg)
        # Set the filename parameter
        msg.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(fn)
        )
        self.message.attach(msg)

    def send(self):
        self.mysmtp_conn.send_message(self.message)


# ==============================================================================
#
# ==============================================================================
