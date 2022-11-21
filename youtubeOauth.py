#!/usr/bin/env python3
import requests, json, time
from urllib.parse import urlencode
from youtubeDL import youtubeDL

class youtubeOauth(youtubeDL):
    'This class serves to support the youtubeDL class to get Oauth tokens for the YouTube API'
    RATINGS = ["like", "dislike", "none"]
    SCOPE = "https://www.googleapis.com/auth/youtube"
    SCHEME = "https://"
    BASE_URL = "oauth2.googleapis.com"
    HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}
    SECRETS = "client_secrets.json"
    REFRESHER = "refresh_token.txt"

    video_ids = []
    rating = ""
    client_id = ""
    client_secret = ""
    access_token = ""

    def __init__(self, rating):
        # Pull in the parent's methods and objects
        # so that we can access them as self.
        super().__init__()

        try:
            with open(self.SECRETS, "r") as f:
                json_data = json.loads(f.readlines()[0])
                self.client_id = json_data["installed"]["client_id"]
                self.client_secret = json_data["installed"]["client_secret"]

            if rating in self.RATINGS:
                self.rating = rating
            else:
                self.logMsg("ERROR: Invalid rating!")
                exit(1)
        except FileNotFoundError:
            self.logMsg("ERROR: Unable to locate client_secrets.json file! Cannot continue!")
            self.logMsg("You either need to download the client_secrets.json file from the Google Cloud console or move that file into the same directory as this script!", 1)
            exit(1)

    def updateRefreshToken(self, refresh_token):
        # https://developers.google.com/youtube/v3/guides/auth/devices#offline
        with open(self.REFRESHER, "w") as f:
                f.write(refresh_token)

    def requestDeviceAndUserCodes(self):
        # https://developers.google.com/youtube/v3/guides/auth/devices#step-1:-request-device-and-user-codes
        endpoint = "/device/code"
        url = self.SCHEME + self.BASE_URL + endpoint
        data = {"client_id": self.client_id, "scope": self.SCOPE}
        r = requests.post(url=url, headers=self.HEADERS, data=urlencode(data))
        if r.status_code == 200:
            self.logMsg("Successfully retrieved device and user codes!")
            return json.loads(r.text)
        else:
            self.logMsg("ERROR: Unable to retrieve device and user codes!")
            self.logMsg("DEBUG: Client ID: %s :: HTTP Response: %d :: Error Text: %s" % (self.client_id, r.status_code, r.text), 1)

    def displayUserCode(self, response):
        # https://developers.google.com/youtube/v3/guides/auth/devices#displayingthecode
        print("Please navigate to this URL: %s and input the following code: %s" % (response["verification_url"], response["user_code"]))

    def pollAuthServer(self, response):
        # https://developers.google.com/youtube/v3/guides/auth/devices#step-4:-poll-googles-authorization-server
        self.logMsg("Waiting for user to authorize this script...")
        time.sleep(response["interval"])

        endpoint = "/token"
        url = self.SCHEME + self.BASE_URL + endpoint
        data = {"client_id": self.client_id, "client_secret": self.client_secret, "device_code": response["device_code"], "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}
        r = requests.post(url=url, headers=self.HEADERS, data=urlencode(data))
        result = self.handlePollingServerResponse(r)
        while result is False:
            self.logMsg("Still waiting for user to authorize this script...")
            time.sleep(response["interval"])
            result = self.handlePollingServerResponse(r)
        self.logMsg("User successfully authorized the script!")
        self.access_token = result["access_token"]

    
    def handlePollingServerResponse(self, response):
        # https://developers.google.com/youtube/v3/guides/auth/devices#step-6:-handle-responses-to-polling-requests
        if response.status_code == 200:
            json_data = json.loads(response.text)
            self.updateRefreshToken(json_data["refresh_token"])
            return json_data
        else:
            return False

    def refreshAccessToken(self):
        # https://developers.google.com/youtube/v3/guides/auth/devices#offline
        try:
            with open(self.REFRESHER, "r") as f:
                refresh_token = f.readlines()[0]
            
            endpoint = "/token"
            url = self.SCHEME + self.BASE_URL + endpoint
            data = {"client_id": self.client_id, "client_secret": self.client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}
            r = requests.post(url=url, headers=self.HEADERS, data=data)
            if r.status_code == 200:
                # With the refresh_token saved and stored, it should be reuseable and this should be the 
                # most used part of this method
                self.logMsg("Access token successfully refreshed!")
                json_data = json.loads(r.text)
                self.access_token = json_data["access_token"]
            else:
                # If the refresh_token file has been corrupted or not saved properly or if the
                # refresh_token is simply incorrect or typod, then we need to get a brand new
                # access token and refresh token
                self.logMsg("ERROR: Unable to refresh the access_token with the refresh_token we have on file!")
                self.logMsg("DEBUG: Refresh Token: %s :: HTTP Response: %d :: Error Details: %s" % (refresh_token, r.status_code, r.text), 1)
                return False
        except FileNotFoundError:
            # If the refresh_token file isn't even on the system, then this is probably the first time
            # this script has been ran on the system, or by the user, so we need to get new codes
            self.logMsg("ERROR: Unable to refresh the access_token as there is no refresh_token on file!")
            self.logMsg("This must be a new authorization attempt...")
            return False

    def rateVideos(self):
        # https://developers.google.com/youtube/v3/docs/videos/rate
        for i in self.to_download:
            url = "https://youtube.googleapis.com/youtube/v3/videos/rate?id=%s&rating=%s&key=%s" % (i, self.rating, self._apikey)
            headers = {"Accept": "application/json", "Authorization": ""}
            headers["Authorization"] = "Bearer %s" % self.access_token
            r = requests.post(url=url, headers=headers)
            if r.status_code == 204:
                self.logMsg("Successfully liked video: %s!" % i)
            else:
                self.logMsg("ERROR: Unable to leave rating on video!")
                self.logMsg("DEBUG: Access Token: %s :: HTTP Response: %d :: Error Text: %s :: Video ID: %s" % (self.access_token, r.status_code, r.text, i), lvl=1)