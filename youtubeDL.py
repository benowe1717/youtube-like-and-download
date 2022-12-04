#!/usr/bin/env python3
from youtubeLogger import youtubeLogger
from datetime import datetime, timezone
import requests, json, pytz, os

class youtubeDL():
    'This class servers to parse a YouTube Content Creator uploads playlist for videos to download and if it meets the defined criteria will be handed off to yt-dlp to actually download the video'

    # Note that there are no "private" objects or methods in the
    # Python class structure, but it is generally accepted that
    # methods and objects with a single "_" (underscore) preceding
    # the name indicates something "not to be messed with". So I'm
    # adopting that convention to denote "private" objects and methods

    #########################
    ### PRIVATE CONSTANTS ###
    #########################
    _CONFIG_FILE = "config.json"
    _CREDS_FILE = ".creds" # This file should store your API Key
    _TIME = 3600 # This is used to control how far back in time we should check for "new releases" (if you set this to 3600, then you should only run this script once an hour)
    _YTDLP = "/usr/local/bin/yt-dlp"

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    SCHEME = "https://"
    BASE_URL = "youtube.googleapis.com"

    #######################
    ### PRIVATE OBJECTS ###
    #######################
    _apikey = "" # This will be populated with the value that we read in from the _CREDS_FILE
    _headers = {"Accept": "application/json"} # This will have the _apikey value added to it, which is why i want to keep it private
    _logger = youtubeLogger() # Bring in our custom logging class to standardize log location and formatting

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    video_data = {}
    download_queue = []
    search_queue = []

    def __init__(self):
        try:
            with open(self._CREDS_FILE, "r") as file:
                self._apikey = file.readlines()[0]
        except FileNotFoundError as e:
            self._logger.logMsg("ERROR: Unable to locate or open the .creds file! Cannot continue!")
            self._logger.logMsg("You either need to create a .creds file and paste in your API Key or move the .creds file you created into the same directory as this script...")
            exit(1)

        try:
            with open(self._CONFIG_FILE, "r") as file:
                self.video_data = json.loads(file.readlines()[0])
        except FileNotFoundError as e:
            self._logger.logMsg("ERROR: Unable to locate or open the config.json file! Cannot continue!")
            self._logger.logMsg("You either need to create a config.json file and paste in the template from GitHub or move the comfig.json file you created into the same directory as this script...")
            exit(1)

    def _getCurrentTime(self):
        'This method gets the current time returned in the same format as the YouTube API time format'
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def _convertTime(self, timestamp):
        'This method is used to convert a timestamp in string format to a datetime object so we can do math on it'
        return datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%S")

    def _convertToEst(self, timestamp):
        'This method is used to convert the UTC Timestamp returned from the YouTube API into an EST timestamp instead'
        return datetime.fromisoformat(timestamp[:-1]).replace(tzinfo=timezone.utc).astimezone(pytz.timezone("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S")

    def _isNewRelease(self, currentTime, publishedTime):
        'This method runs a test to see if the current time - the published time is less than the _TIME constant, indicating that it is a "NEW" video to download'
        test = self._convertTime(currentTime).timestamp() - self._convertTime(publishedTime).timestamp()
        if test < self._TIME:
            return True
        else:
            return False

    def _doesTitleMatch(self, titles, title):
        'This method runs a test to see if the current video title matches any of the titles provided from config.json'
        count = 0 # This variable is a counter to help us parse each video title and if no matches occur we error out
        if len(titles) > 0:
            for i in titles:
                if i in title:
                    # Stop here as we found a match and can safely download the video
                    return True
                else:
                    # Increment the counter so that we test each title in the list
                    count += 1
            if count == len(titles):
                # If all tests failed then we should not download the video
                return False
        else:
            # If there are no titles provided to search, then we just download all new videos
            return True

    def updateConfig(self):
        'This method writes the self.video_data object back into the config.json file only if it has been changed'
        try:
            with open(self._CONFIG_FILE, "w") as file:
                json.dump(self.video_data, file)
            self._logger.logMsg("Successfully updated the local config!")
        except BaseException as e:
            self._logger.logMsg(f"ERROR: Unable to update {self._CONFIG_FILE} with new Channel IDs!")
            self._logger.logDebugMsg(f"DEBUG: Exception Text: {e}")
            exit(1)

    def setup(self):
        'This method checks the config.json file to see if we have the Channel ID configured for each listed Channel'
        for i in self.video_data["channels"]:
            if "channelId" in self.video_data["channels"][i].keys():
                # There's nothing to do here because we already have
                # the channelId in our config, again we're doing this
                # to save on the quota
                self._logger.logMsg(f"The Channel ID is already configured for {i}!")
            else:
                # this means we need to get the channel id
                # this is a VERY expensive api call so we should
                # only do this if we have to. just populate a
                # list of channels to search for
                self.search_queue.append(i)
                self._logger.logMsg(f"The Channel ID is not configured for {i}!")
                self._logger.logMsg("Appending Channel to search queue...")

    def getChannelIds(self):
        'This method is used to search YouTube for the provided Channel Names and get their associated Channel ID'
        # https://developers.google.com/youtube/v3/docs/search/list
        to_remove = [] # This list will be populated only if we cannot find the channelId
        for i in self.search_queue:
            query = i # This is the "Search Term" to pass to the API
            endpoint = f"/youtube/v3/search?part=snippet&maxResults=5&q={query}&key={self._apikey}"
            url = self.SCHEME + self.BASE_URL + endpoint
            self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
            r = requests.get(url=url, headers=self._headers)
            json_data = json.loads(r.text)
            if r.status_code == 200:
                ii = 0
                while ii < len(json_data["items"]):
                    if json_data["items"][ii]["id"]["kind"] == "youtube#channel":
                        channelId = json_data["items"][ii]["id"]["channelId"]
                        self.video_data["channels"][i]["channelId"] = channelId
                        self._logger.logMsg(f"Successfully found the YouTube Channel ID with the name: {query}!")
                        self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Query: {query} :: Channel ID: {channelId} :: Response Text: {json_data}")
                        break # no reason to keep parsing the list if we found what we needed
                    else:
                        ii += 1 # this is used as a "counter", we want to parse each result from the search to give every chance of finding the right channelId
                if ii == len(json_data["items"]):
                    self._logger.logMsg(f"ERROR: Unable to locate any YouTube Channels with the name: {query}!")
                    self._logger.logMsg("Removing this channel name from the list of channels to work on...")
                    to_remove.append(i)
        if len(to_remove) > 0:
            for i in to_remove:
                self.video_data["channels"].pop(i)

    def requestChannelPlaylistId(self):
        'This method is used to get the "Uploads" playlistId for each YouTube Channel listed in the config.json file'
        # https://developers.google.com/youtube/v3/docs/channels/list#request
        to_remove = []
        for i in self.video_data["channels"]:
            channelId = self.video_data["channels"][i]["channelId"]
            endpoint = f"/youtube/v3/channels?part=contentDetails&id={channelId}&key={self._apikey}"
            url = self.SCHEME + self.BASE_URL + endpoint
            self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
            r = requests.get(url=url, headers=self._headers)
            json_data = json.loads(r.text)
            if r.status_code == 200:
                playlistId = json_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
                self.video_data["channels"][i]["playlistId"] = playlistId
                self._logger.logMsg(f"Successfully found the uploads Playlist ID for the Channel: {i}!")
                self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Channel: {i} :: Channel ID: {channelId} :: Uploads Playlist ID: {playlistId} :: Response Text: {json_data}")
            else:
                self._logger.logMsg(f"ERROR: Unable to locate the uploads Playlist for: {i}!")
                self._logger.logMsg("Removing this channel name from the list of channels to work on...")
        if len(to_remove) > 0:
            for i in to_remove:
                self.video_data["channels"].pop(i)

    def getRecentVideos(self):
        'This method is used to get the X most recent videos for the provided playlistIds where X defaults to 5'
        # https://developers.google.com/youtube/v3/docs/playlistItems/list#request
        for i in self.video_data["channels"]:
            playlistId = self.video_data["channels"][i]["playlistId"]
            endpoint = f"/youtube/v3/playlistItems?part=snippet&maxResults=5&playlistId={playlistId}&key={self._apikey}"
            url = self.SCHEME + self.BASE_URL + endpoint
            self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
            r = requests.get(url=url, headers=self._headers)
            json_data = json.loads(r.text)
            if r.status_code == 200:
                self.video_data["channels"][i]["videos"] = {} # This is needed first as you cannot update a dictionary with a key that doesn't exist yet
                for item in json_data["items"]:
                    publishedAt = self._convertToEst(item["snippet"]["publishedAt"])
                    resourceId = item["snippet"]["resourceId"]["videoId"]
                    title = item["snippet"]["title"]
                    self.video_data["channels"][i]["videos"][resourceId] = {"title": title, "publishedAt": publishedAt}
            else:
                self._logger.logMsg("ERROR: Unable to contact YouTube API or process request/response!")
                self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Username: {i} :: Playlist ID: {playlistId} :: API Key: {self._apikey} :: Response Text: {json_data}")
                exit(1)

    def parseVideos(self):
        'This method is used to parse the gathered video data for two pieces of criteria: If it is a new release (based on the _TIME constant) and if the Title matches (based on the titles key in config.json)'
        for i in self.video_data["channels"]:
            self._logger.logMsg(f"Checking videos for channel: {i}")
            titles = self.video_data["channels"][i]["titles"]
            for video in self.video_data["channels"][i]["videos"]:
                title = self.video_data["channels"][i]["videos"][video]["title"]
                publishedAt = self.video_data["channels"][i]["videos"][video]["publishedAt"]
                if self._isNewRelease(self._getCurrentTime(), publishedAt):
                    self._logger.logMsg("Found a newly released video! Checking to see if the title matches our criteria...")
                    if self._doesTitleMatch(titles, title):
                        self._logger.logMsg("The video matches all of our download criteria! Adding video to the download queue...")
                        self._logger.logDebugMsg(f"DEBUG: Channel: {i} :: Video ID: {video} :: Title: {title}")
                        self.download_queue.append(video)
                    else:
                        self._logger.logMsg("The video does not match all of our download criteria! Not adding video to the download queue...")
                        self._logger.logDebugMsg(f"DEBUG: Video ID: {video} :: Title: {title} :: Criteria: {titles}")
                else:
                    self._logger.logMsg("Video is not a new release! Not adding video to the download queue...")
                    self._logger.logDebugMsg(f"DEBUG: Video ID: {video} :: Current Time: {self._getCurrentTime()} :: Published At: {publishedAt}")

    def downloadVideos(self):
        'This method is used to download all videos found in the download_queue list using the yt-dlp application (which must be installed ahead of time)'
        # https://github.com/yt-dlp/yt-dlp
        ii = 1
        base_url = "www.youtube.com"
        path = os.path.realpath(__file__)
        for i in self.download_queue:
            endpoint = f"/watch?v={i}"
            url = self.SCHEME + base_url + endpoint
            self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
            self._logger.logMsg(f"Staring the download process on video #{ii} through yt-dlp...")
            cmd = f"{self._YTDLP} --path {path} --no-progress --format bestvideo*+bestaudio/best {url}"
            self._logger.logDebugMsg(f"DEBUG: Downloading Video ID: {i} with Command: {cmd}")
            os.system(cmd)
            ii += 1

    def rateVideos(self, access_token):
        'This method is used to leave a "rating" on all videos found in the download_queue. This method only leaves the "like" rating even though the YouTube API offers other options'
        # https://developers.google.com/youtube/v3/docs/videos/rate
        ii = 1
        self._headers["Authorization"] = f"Bearer {access_token}"
        for i in self.download_queue:
            self._logger.logMsg(f"Starting the rating process on video #{ii}...")
            endpoint = f"/youtube/v3/videos/rate?id={i}&rating=like&key={self._apikey}"
            url = self.SCHEME + self.BASE_URL + endpoint
            self._logger.logDebugMsg(f"DEBUG: Calling YouTube API via URL: {url}")
            r = requests.post(url=url, headers=self._headers)
            json_data = json.loads(r.text)
            if r.status_code == 204:
                self._logger.logMsg("Successfully left a like on the video!")
            else:
                self._logger.logMsg("ERROR: Unable to leave a rating on the video!")
                self._logger.logDebugMsg(f"DEBUG: HTTP Response Code: {r.status_code} :: Video ID: {i} :: Response Text: {json_data}")
            ii += 1