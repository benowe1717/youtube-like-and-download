#!/usr/bin/env python3
from youtubeDL import youtubeDL
from youtubeOauth import youtubeOauth

def main():

    # Instantiate the first class
    # This gives us access to the logging class
    # and access to the debug variable
    ytDL = youtubeDL()

    ### ONLY UNCOMMENT THIS DURING TROUBLESHOOTING ###
    # ytDL.debug = True

    ytDL.logMsg("Starting script...")

    # Now we need to set the list of Content Creators
    # that we want to check for new videos from
    # Even if you only want to check for one, just 
    # put one in this list, we can iterate over one
    # or many
    content_creators = ["ChristopherOdd"]

    # Before we ge started on checking for videos
    # and downloading them, we need to be able to "like"
    # each video that we download, to do that we will need
    # an OAuth access token
    yto = youtubeOauth("like")
    ytDL.logMsg("Attempting to refresh the access_token...")
    status = yto.refreshAccessToken()
    if status is False:
        ytDL.logMsg("Access token was not refreshed, so we need to get a new one...")
        
        # So the first thing we need to do is get the Device Code, the User Code, 
        # and the Verification URL so that we can work through Youtube's "Device"
        # OAuth authorization flow. This will require manual user intervention
        codes = yto.requestDeviceAndUserCodes()
        yto.displayUserCode(codes)

        # So now we've gotten the codes and displayed them to the user, we need to poll
        # the authorization server at the given interval to see if the user has authorized
        # us yet or not
        yto.pollAuthServer(codes)

    for creator in content_creators:
        # The first thing that we need to do is get the content creator's
        # main playlist called "uploads". this allows us to see all of their uploaded
        # videos, though the request will set a max return value of 5 (and we're ok with that)

        # BTW this function doesn't return anything, so no need to
        # store it's content in a variable
        ytDL.getUploadsId(creator)

        # Once we have the playlistID for the content creator's "uploads" playlist
        # we can grab the 5 most recently released videos and get their relevant details
        # like the publishedAt (release time), resourceId (specific video id), and title
        ytDL.findVideos()

        # The details were appended to list objects, so now it's time to loop through them
        # to see if they're worth downloading or if we need to skip them
        ytDL.parseVideos()

        # Ok now that we've finished parsing the videos (basically moving the matching videos to
        # the to_download list), it's time to download them. But we should only attempt a download if
        # the list has at least one item in it
        if len(ytDL.to_download) >= 1:
            ytDL.logMsg("Found at least one video to download for %s!" % creator)
            ytDL.logMsg("Attempting to download newly released videos...")
            ytDL.downloadVideos()
            yto.rateVideos()
        else:
            ytDL.logMsg("No new videos to download for %s! Looks like we're finished here..." % creator)

    ytDL.logMsg("Script is finished! Bye bye!")

if __name__ == "__main__":
    main()