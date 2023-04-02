import smtplib
from getpass import getpass


class NotificationSystem():
    def __init__(self, email_address, recipient_address):
        self.be_notified = True
        self.email_address = email_address
        self.recipient_address = recipient_address
        validation = input('Type `yes or y` if you wish to be notified by email:\t')
        if not (validation == 'yes' or validation == 'y'):
            self.be_notified = False
            return
        message = 'Email password for ' + self.email_address + ' :'
        self.password = getpass(message)

    def send_message(self, title, body):
        if not self.be_notified :
            return
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(self.email_address, self.password)
        content = 'Subject: ' + title + '\n' + body
        smtp_server.sendmail(self.email_address, self.recipient_address, content)

        smtp_server.quit()
        print('Email sent successfully')