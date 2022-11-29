#!/usr/bin/env python3
import requests, json
from urllib.parse import urlencode
from youtubeLogger import youtubeLogger

class youtubeOauth():
    'This class serves to support the youtubeDL class to get Oauth tokens for the YouTube API'

    # Note that there are no "private" objects or methods in the
    # Python class structure, but it is generally accepted that
    # methods and objects with a single "_" (underscore) preceding
    # the name indicates something "not to be messed with". So I'm
    # adopting that convention to denote "private" objects and methods

    #########################
    ### PRIVATE CONSTANTS ###
    #########################
    _SECRETS_FILE = "client_secrets.json"
    _REFRESH_TOKEN_FILE = "refresh_token.txt"

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    NEW_AUTH = False
    SCHEME = "https://"
    BASE_URL = "oauth2.googleapis.com"
    SCOPE = "https://www.googleapis.com/auth/youtube"
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code" # https://developers.google.com/youtube/v3/guides/auth/devices#step-4:-poll-googles-authorization-server

    #######################
    ### PRIVATE OBJECTS ###
    #######################
    _client_id = ""
    _client_secret = ""
    _access_token = ""
    _refresh_token = ""
    _logger = youtubeLogger() # Bring in our custom logging class to standardize log location and formatting

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    # device_codes will always be in device_code, user_code, verification_url, interval order
    device_codes = [] # https://developers.google.com/youtube/v3/guides/auth/devices#step-2:-handle-the-authorization-server-response


    # NOTE that all print statements will become
    # actual log messages once i've rewritten the log method to 
    # be an actual class

    def __init__(self):
        try:
            with open(self._SECRETS_FILE, "r") as file:
                json_data = json.loads(file.readlines()[0])
                self._client_id = json_data["installed"]["client_id"]
                self._client_secret = json_data["installed"]["client_secret"]
        except FileNotFoundError:
            self._logger.logMsg("ERROR: Unable to locate client_secrets.json file!")
            self._logger.logMsg("You either need to download the client_secrets.json file from the Google Cloud console or update the _SECRETS_FILE constant with the appropriate path...")
            exit(1)

        try:
            with open(self._REFRESH_TOKEN_FILE, "r") as file:
                self._refresh_token = file.readlines()[0]
        except FileNotFoundError:
            self._logger.logMsg("ERROR: Unable to locate the refresh_token.txt file!")
            self._logger.logMsg("This could be due to this being the first time we are being authorized OR you need to update the _REFRESH_TOKEN_FILE constant with the appropriate path...")
            self.NEW_AUTH = True
            # no exit here as we can just reauth based on what happens

    def _saveRefreshToken(self):
        'This method is used by the pollAuthServer method to save a local copy of the refresh_token so that it can be used to get a new access_token on subsequent runs'
        with open(self._REFRESH_TOKEN_FILE, "w") as file:
            file.writelines(self._refresh_token)

    def requestDeviceAndUserCodes(self):
        'This method sends an HTTP POST request to the authorization server to request Device and User codes for OAuth authentication'
        # https://developers.google.com/youtube/v3/guides/auth/devices#step-1:-request-device-and-user-codes
        endpoint = "/device/code"
        url = self.SCHEME + self.BASE_URL + endpoint
        data = {"client_id": self._client_id, "scope": self.SCOPE}
        self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}...")
        r = requests.post(url=url, headers=self.headers, data=urlencode(data))
        json_data = json.loads(r.text)
        if r.status_code == 200:
            self._logger.logMsg("Successfully retrieved device and user codes!")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Response Text: {r.text}")
            # Apparently the .append() method only accepts one argument, and I wanted to
            # try to keep this to one line, so I found this article:
            # https://bobbyhadz.com/blog/python-append-multiple-values-to-list-in-one-line
            self.device_codes.extend([json_data["device_code"], json_data["user_code"], json_data["verification_url"], json_data["interval"]])
            return True
        elif r.status_code == 403:
            if json_data["error_code"] == "rate_limit_exceeded":
                self._logger.logMsg("ERROR: API Quota has been exceeded for this account!")
                self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Response Text: {r.text}")
        else:
            self._logger.logMsg("ERROR: Unable to request Device and User Codes!")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Response Text: {r.text}")
            return False

    def displayUserCode(self):
        'This method displays the Veritifcation URL and the User Code obtained from the requestDeviceAndUserCodes() method'
        # https://developers.google.com/youtube/v3/guides/auth/devices#displayingthecode
        print(f"Please navigate to the following URL: {self.device_codes[2]} and enter the following code: {self.device_codes[1]}")

    def pollAuthServer(self):
        'This method polls the authorization server at the specified interval to determine if the user has input the correct user_code and allowed our app to authenticate on their behalf'
        # https://developers.google.com/youtube/v3/guides/auth/devices#step-4:-poll-googles-authorization-server
        endpoint = "/token"
        url = self.SCHEME + self.BASE_URL + endpoint
        data = {"client_id": self._client_id, "client_secret": self._client_secret, "device_code": self.device_codes[0], "grant_type": self.GRANT_TYPE}
        self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
        r = requests.post(url=url, headers=self.headers, data=urlencode(data))
        json_data = json.loads(r.text)
        if r.status_code == 200:
            self._logger.logMsg("User has successfully authorized our application!")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Response Text: {r.text}")
            self._access_token = json_data["access_token"]
            self._refresh_token = json_data["refresh_token"]
            self._saveRefreshToken()
            return 200 # This signals the end of use for this method
        elif r.status_code == 428:
            self._logger.logMsg(f"User has not completed the authorization flow! Will check again in {self.device_codes[3]} seconds...")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Error: {json_data['error']} :: Error Description: {json_data['error_description']}")
            return 428 # This signals that the method should be used again once the specified interval has passed
        elif r.status_code == 403:
            self._logger.logMsg(f"ERROR: {json_data['error']} has occurred! Description: {json_data['error_description']}!")
            if json_data["error"] == "slow_down":
                return 425 # This signals something has gone wrong with the speed of the requests, try tripling the wait time
            else:
                return 403 # This signals something has gone wrong with the method and probably isn't recoverable
        else:
            self._logger.logMsg(f"ERROR: Unable to contact YouTube API!")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Response Text: {r.text}")
            return 1 # This signals something has gone wrong with the method and is not recoverable

    def refreshAccessToken(self):
        'This method is used to refresh the current Access Token as these tokens periodically expire and become invalid after expiration'
        # https://developers.google.com/youtube/v3/guides/auth/devices#offline
        endpoint = "/token"
        url = self.SCHEME + self.BASE_URL + endpoint
        data = {"client_id": self._client_id, "client_secret": self._client_secret, "grant_type": "refresh_token", "refresh_token": self._refresh_token}
        self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
        r = requests.post(url=url, headers=self.headers, data=urlencode(data))
        json_data = json.loads(r.text)
        if r.status_code == 200:
            self._logger.logMsg("Successfully refreshed our Access Token!")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Response Text: {r.text}")
            self._access_token = json_data["access_token"]
            return True
        else:
            self._logger.logMsg("ERROR: Unable to refresh our Access Token or unable to contact the YouTube API!")
            self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Refresh Token: {self._refresh_token} :: Response Text: {r.text}")
            return False