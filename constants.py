#!/usr/bin/env python3

### arg_parse ###
PROGRAM_NAME = "main.py"
PROGRAM_DESCRIPTION = """A program to identify, 
like, and download videos from YouTube"""
VERSION = "0.1.0"
AUTHOR = "Benjamin Owen"
REPO = "https://github.com/benowe1717/youtube-like-and-download"

CONFIG_ACTIONS = [
    "add", "list", "update", "remove"
]
###

### youtube_logger ###
TIME_FORMAT = "%b %d %H:%M:%S"
NAME = "youtubeDL"
###

### youtube_configurator ###
YOUTUBE_TABS = [
    "featured", "videos", "shorts", "streams", "playlists", "community",
    "channels", "about"
]
UPDATE_TYPES = [
    "u", "o", "update", "overwrite"
]
###

### youtube_oauth ###
OAUTH_BASE_URL = "https://oauth2.googleapis.com"
OAUTH_SCOPE = "https://www.googleapis.com/auth/youtube"
OAUTH_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
###

### youtube_dl ###
DL_BASE_URL = "https://youtube.googleapis.com"
###