#!/usr/bin/env python3
from youtubeDL import youtubeDL
from youtubeOauth import youtubeOauth
from youtubeLogger import youtubeLogger
import time, argparse, os

def addConfig(config):
    title_list = []
    name = input("Enter the Channel Name: ")
    titles = input("Enter in any Title keywords you want to filter on, separated by comma: ")
    if name in config["channels"].keys():
        return False
    else:
        if titles == "":
            config["channels"].update({name: {"titles": []}})
        else:
            for i in titles.split(","):
                title_list.append(i.strip())
            config["channels"].update({name: {"titles": title_list}})
        return True

def updateConfig(config):
    title_list = []
    name = input("Enter the Channel Name to update: ")
    titles = input("Enter in any Title keywords you want to filter on, separated by comma: ")
    title_change = input("Do you want to append Title keywords or overwrite Title keywords? [append/update] ")
    if name in config["channels"].keys():
        if title_change == "append":
            if titles == "":
                config["channels"][name]["titles"] = []
            else:
                for i in titles.split(","):
                    title_list.append(i.strip())
                config["channels"][name]["titles"].append(title_list)
            return True
        elif title_change == "update":
            if titles == "":
                config["channels"][name]["titles"] = []
            else:
                for i in titles.split(","):
                    title_list.append(i.strip())
                config["channels"][name]["titles"] = title_list
            return True
        else:
            return False
    else:
        return False

def deleteConfig(config):
    name = input("Enter the Channel Name to remove: ")
    if name in config["channels"].keys():
        config["channels"].pop(name)
        return True
    else:
        return False

def testPath(path):
    if(os.path.exists(path)):
        if(os.access(path, os.W_OK)):
            return True
        else:
            return False
    else:
        return False

def main():

    # Instantiate the first class
    # This gives us access to the logging class
    logger = youtubeLogger()
    ytDL = youtubeDL()

    logger.logMsg("Starting script...")

    # Let's pull in an argument parser which will allow us to decide
    # how this program is going to be executed. this flow will offer several
    # different options, but only the modifications to the config.json file
    # will alter the full execution of the program
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="specify the actions list, add, update, or delete to modify the local config file")
    parser.add_argument("--download-path", help="specify an alternative download path for any downloadable YouTube videos, please specify the full path")
    args = parser.parse_args()
    change_config = args.config
    change_download_path = args.download_path

    if change_config is not None:
        if change_config == "list":
            print(ytDL.video_data)
            exit(0)
        elif change_config == "add":
            result = addConfig(ytDL.video_data)
            if result is False:
                print("ERROR: Unable to update config!")
                exit(1)
            else:
                ytDL.updateConfig()
                print("Successfully updated the config!")
                exit(0)
        elif change_config == "update":
            result = updateConfig(ytDL.video_data)
            if result is False:
                print("ERROR: Unable to update config!")
                exit(1)
            else:
                ytDL.updateConfig()
                print("Successfully updated the config!")
                exit(0)
        elif change_config == "delete":
            result = deleteConfig(ytDL.video_data)
            if result is False:
                print("ERROR: Unable to update config!")
                exit(1)
            else:
                ytDL.updateConfig()
                print("Successfully updated the config!")
                exit(0)
        else:
            print("error, unknown config action")
            exit(1)

    if change_download_path is not None:
        result = testPath(os.path.join(change_download_path, ""))
        if result is False:
            logger.logMsg("ERROR: Unable to find or open the provided download path!")
            exit(1)
        else:
            ytDL.download_path = os.path.join(change_download_path, "")
            logger.logMsg(f"Successfully changed the video download path to: {ytDL.download_path}")

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
            grammar = f"There are {queue} videos"
        else:
            grammar = f"There is {queue} video"
        logger.logMsg(f"{grammar} to download! Starting the download process now...")
        ytDL.downloadVideos()
        ytDL.rateVideos(yto._access_token)
    else:
        logger.logMsg("There are no videos in the download queue!")

    logger.logMsg("Script is finished! Bye bye!")

if __name__ == "__main__":
    main()