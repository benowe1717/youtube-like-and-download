#!/usr/bin/env python3
import constants
from logger import youtube_logger
from urllib.parse import urlencode
import json, os, requests, time, yaml

class youtube_oauth():
    """
        This class is designed to handle the authentication to the
        YouTube API
    """

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    BASE_URL = constants.OAUTH_BASE_URL
    SCOPE = constants.OAUTH_SCOPE
    GRANT_TYPE = constants.OAUTH_GRANT_TYPE

    #######################
    ### PRIVATE OBJECTS ###
    #######################
    __client_id = ""
    __client_secret = ""
    __access_token = ""
    __refresh_token = {}
    __device_code = ""
    __interval = -1
    __client_secrets_file = "client_secrets.json"
    __refresh_token_file = "refresh_token.json"
    __headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    logger = ""

    def __init__(self):
        self.logger = youtube_logger()

        try:
            with open(self.__client_secrets_file, "r") as file:
                json_data = json.loads(file.readlines()[0])
                self.__client_id = json_data['installed']['client_id']
                self.__client_secret = json_data['installed']['client_secret']
        except FileNotFoundError:
            print(f"ERROR: Unable to open {self.__client_secrets_file}")
            self.logger.logger.error(
                f"ERROR: Unable to open {self.__client_secrets_file}"
            )
            exit(1)

        try:
            with open(self.__refresh_token_file, "r") as file:
                self.__refresh_token = json.loads(file.readlines()[0])
        except FileNotFoundError:
            # This just means that the first auth has never happened
            pass

        if not 'access_token' in self.__refresh_token.keys():
            print(
                "There is no access token on file, starting up the",
                "normal login process..."
            )
            self.logger.logger.info(
                "There is no access token on file, starting up the " +
                "normal login process..."
            )
            self.login()

        if not self.is_expired():
            print(
                "The access token is expired! Refreshing the token..."
            )
            self.logger.logger.info(
                "The access token is expired! Refreshing the token..."
            )
            self.refresh_access_token()

    def login(self):
        self.request_and_display_codes()
        self.poll_auth_server()

    def request_and_display_codes(self):
        endpoint = "/device/code"
        url = f"{self.BASE_URL}{endpoint}"
        payload = {
            "client_id": self.__client_id,
            "scope": self.SCOPE
        }
        r = requests.post(
            url=url, headers=self.__headers, data=urlencode(payload)
        )
        if r.status_code == 200:
            data = json.loads(r.text)
            print(
                "Please navigate to the following URL:",
                f"{data['verification_url']} and enter the following",
                f"code: {data['user_code']}"
            )
            self.__device_code = data['device_code']
            self.__interval = data['interval']
            return
            
        else:
            print(
                "ERROR: Unable to get user and device codes!",
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            exit(1)

    def poll_auth_server(self):
        status_code = -1
        endpoint = "/token"
        url = f"{self.BASE_URL}{endpoint}"
        payload = {
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "device_code": self.__device_code,
            "grant_type": self.GRANT_TYPE
        }
        while status_code != 200:
            r = requests.post(
                url=url, headers=self.__headers, data=urlencode(payload)
            )
            status_code = r.status_code
            if status_code == 428:
                print("Still waiting for authorization...")

            elif status_code == 425:
                print("Polling is too fast! Using a backoff strategy...")
                self.__interval = self.__interval * 2

            elif status_code == 403:
                print("ERROR: Your API Quota has been exceeded!")
                exit(1)

            elif status_code == 200:
                print("Authorization successful!")
                self.__refresh_token = json.loads(r.text)
                self.update_expiration()
                with open(self.__refresh_token_file, "w") as file:
                    json.dump(self.__refresh_token, file)
                return

            time.sleep(self.__interval)

    def refresh_access_token(self):
        endpoint = "/token"
        url = f"{self.BASE_URL}{endpoint}"
        payload = {
            "client_id": self.__client_id,
            "client_secret": self.__client_secret,
            "refresh_token": self.__refresh_token['refresh_token'],
            "grant_type": "refresh_token"
        }
        r = requests.post(
            url=url, headers=self.__headers, data=urlencode(payload)
        )
        if r.status_code == 200:
            print("Access token successfully refreshed!")
            self.logger.logger.info(
                "Access token successfully refreshed!"
            )
            data = json.loads(r.text)
            self.__refresh_token['access_token'] = data['access_token']
            self.update_expiration()
            with open(self.__refresh_token_file, "w") as file:
                json.dump(self.__refresh_token, file)

        else:
            print(
                "Unable to refresh the access token!",
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            self.logger.logger.error(
                "Unable to refresh the access token! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            exit(1)

    def test_api(self):
        endpoint = "/youtube/v3/channels?part=snippet&mine=true"
        url = f"{constants.DL_BASE_URL}{endpoint}"
        access_token = self.__refresh_token['access_token']
        self.__headers["Authorization"] = f"Bearer {access_token}"
        r = requests.get(
            url=url, headers=self.__headers
        )
        if r.status_code == 200:
            print(
                "Test of the API succeeded!"
            )
            return True

        else:
            print(
                "Test of the API failed!",
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            return False

    def update_expiration(self):
        now = time.time()
        expires_in = now + self.__refresh_token['expires_in']
        self.__refresh_token['expires_in'] = expires_in

    def is_expired(self):
        now = time.time()
        if now > self.__refresh_token['expires_in']:
            return False
        return True