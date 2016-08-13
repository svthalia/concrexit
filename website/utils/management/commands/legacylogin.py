from django.core.management.base import BaseCommand

from bs4 import BeautifulSoup
import requests
import getpass


class Command(BaseCommand):
    help = "Logs into the old Thalia website"

    def handle(self, *args, **options):
        self.session = requests.Session()
        loginpage = self.session.get("https://thalia.nu/account")
        soup = BeautifulSoup(loginpage.text, 'lxml')
        ccm_token = soup(attrs={'name': 'ccm_token'})[0]['value']
        while True:
            data = {
                'uName': input("What is your Thalia username? "),
                'uPassword': getpass.getpass("And what is your password? "),
                'ccm_token': ccm_token,
            }
            url = 'https://thalia.nu/login/authenticate/concrete'
            r = self.session.post(url, data=data)
            if "Ongeldige gebruikersnaam" in r.text:
                print("You did not authenticate successfully. Try again.")
                continue
            print("Authentication successful.")
            break
