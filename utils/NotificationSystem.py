import smtplib
from getpass import getpass


class NotificationSystem:
    def __init__(self, email_address: str, recipient_addresses: list[str]):
        self.be_notified = True
        self.email_address = email_address
        self.recipient_addresses = recipient_addresses
        validation = input('Type `yes or y` if you wish to be notified by email:\t')
        if validation not in ['yes', 'y']:
            self.be_notified = False
            return
        message = f'Email password for {self.email_address} :'
        self.password = getpass(message)

    def notify(self, title: str, body: str):
        for recipient_address in self.recipient_addresses:
            self._send_message(title, body, recipient_address)

    def _send_message(self, title, body, recipient_address: str):
        if not self.be_notified:
            return

        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(self.email_address, self.password)
        content = f'Subject: {title}' + '\n' + body
        smtp_server.sendmail(self.email_address, recipient_address, content)

        smtp_server.quit()
        print('Email sent successfully')
