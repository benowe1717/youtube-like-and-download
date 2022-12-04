#!/usr/bin/env python3
from youtubeDL import youtubeDL
from youtubeOauth import youtubeOauth
from youtubeLogger import youtubeLogger
import time

def main():

    # Instantiate the first class
    # This gives us access to the logging class
    logger = youtubeLogger()

    logger.logMsg("Starting script...")

    # Before we ge started on checking for videos
    # and downloading them, we need to be able to "like"
    # each video that we download, to do that we will need
    # an OAuth access token
    yto = youtubeOauth()
    logger.logMsg("Attempting to refresh the access token...")
    if yto.NEW_AUTH:
        logger.logMsg("Access token was not refreshed, so we need to get a new one...")
        
        # So the first thing we need to do is get the Device Code, the User Code, 
        # and the Verification URL so that we can work through Youtube's "Device"
        # OAuth authorization flow. This will require manual user intervention
        step1 = yto.requestDeviceAndUserCodes()
        if step1:
            yto.displayUserCode()

            # So now we've gotten the codes and displayed them to the user, we need to poll
            # the authorization server at the given interval to see if the user has authorized
            # us yet or not
            wait = yto.device_codes[3]
            time.sleep(wait)
            step2 = yto.pollAuthServer()
            while step2 != 200:
                if step2 == 428:
                    time.sleep(wait)
                    step2 = yto.pollAuthServer()
                elif step2 == 425:
                    new_wait = wait * 3
                    time.sleep(new_wait)
                    step2 = yto.pollAuthServer()
                else:
                    exit(1)
        else:
            logger.logMsg("ERROR: Unable to set up Oauth authorization for this app! Cannot continue!")
            exit(1)
    else:
        refresh = yto.refreshAccessToken()
        if refresh is False:
            exit(1)

    # Now that we've finished refreshing our Access Token, we need to work on parsing
    # the config.json file for all of the configured channels and getting that channel's
    # "uploads" playlistId so we can continue

    # So let's start by instantiating the class
    ytDL = youtubeDL()

    # First thing we need to do is figure out if we already have the channelId saved in
    # the config file. if we do, then there isn't much to do in this setup. if we don't
    # then we neeed to start getting those channelIds and saving them for later use
    ytDL.setup()

    if len(ytDL.search_queue) > 0:
        logger.logMsg("Starting up the search queries for the missing Channel IDs...")
        ytDL.getChannelIds()
        logger.logMsg("Updating the local config file for future iterations...")
        ytDL.updateConfig()
    else:
        logger.logMsg("No search queries needed as we have all Channel IDs saved!")

    # And now that we have the channel's ID, we can get the channel's uploads playlist ID
    ytDL.requestChannelPlaylistId()

    # If the above went well, then we've updated the ytDL.video_data dictionary with the
    # channel's "uploads" playlistId. This playlist holds all of the uploaded videos for that channel
    # regardless of how the video was made or uploaded (live stream, or prerecorded, or shorts). Now
    # we need to retrieve a recent list of videos in this playlist for each channel
    ytDL.getRecentVideos()

    # Once this is done, the ytDL.video_data dictionary will once again be updated with all
    # of the most recent videos for each channel. Now we need to parse each video's publishedAt
    # date & time + the video's title to see if it is a "new release" and if it matches the configured
    # "titles" portion of the config.json file
    ytDL.parseVideos()

    # If we found any matching videos, then the ytDL.download_queue list will be populated with each
    # of the videoIds that need to be downloaded. So let's check the length of that list. If the length
    # of the list is greater than 0, then we have work to do. Otherwise, we can safely end the script here
    queue = len(ytDL.download_queue)
    if queue > 0:
        if queue > 1:
            grammar = "videos"
        else:
            grammar = "video"
        logger.logMsg(f"There are {queue} {grammar} to download! Starting the download process now...")
        ytDL.downloadVideos()
        ytDL.rateVideos()
    else:
        logger.logMsg("There are no videos in the download queue!")

    logger.logMsg("Script is finished! Bye bye!")

if __name__ == "__main__":
    main()