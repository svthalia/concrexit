from members import emails


def membership_announcement():
    emails.send_membership_announcement()


def info_request():
    emails.send_information_request()


def expiration_announcement():
    emails.send_expiration_announcement()
