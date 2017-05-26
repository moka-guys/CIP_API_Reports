""" CIP-API Authentication module """

import getpass
import requests


class APIAuthentication:

    """ Generate token and and create a requests 'session'
        http://docs.python-requests.org/en/master/user/advanced/#session-objects
    """

    def __init__(self):
        self.token_url = "https://cipapi.genomicsengland.nhs.uk/api/get-token/"
        self.username =  "/home/mokaguys/Apps/CIP_API/auth_username.txt"
        self.pw = "/home/mokaguys/Apps/CIP_API/auth_pw.txt"
        self.token = self.get_token()
        self.r_session = requests.Session()

    def get_token(self):
	with open(self.username,'r') as f:
		username=f.readline()
	with open(self.pw,'r') as f:
		password=f.readline()
        return requests.post(self.token_url, {"username": username, "password":password}).json()["token"]


if __name__ == "__main__":
    auth = APIAuthentication()
    print auth.token



