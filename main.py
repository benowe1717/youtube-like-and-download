#!/usr/bin/env python3
import constants
from parseargs import arg_parse
from logger import youtube_logger
from configurator import youtube_configurator
from auth import youtube_oauth
from youtube_api import youtube_api
import random, string, sys

def main():
    args = sys.argv
    myparser = arg_parse(args)
    debug = myparser.debug
    logger = youtube_logger()

    logger.logger.info("Starting script...")
    logger.logger.debug("DEBUG logging has been enabled...")

    if myparser.action == "config":
        myconf = youtube_configurator()
        action = myparser.config_action

        if action == "add":
            myapi = youtube_api()
            needle = input(
                "Enter the Youtube Channel Name or URL: "
            )
            titles = input(
                "Enter any Titles, separated by comma, that you " +
                "want to filter for [Leave blank for no filter]: "
            )

            if "http" in needle:
                url = needle.split("/")
                name = url[-1]
                if name in constants.YOUTUBE_TABS:
                    url.pop(-1)
                    name = url[-1]

                if "@" in name:
                    name = name.split("@")[-1]

            else:
                name = needle

            id = myapi.get_channel_id(name)

            if titles:
                title_list = myconf.split_titles(titles)
                if title_list:
                    myconf.add_channel(name, id, title_list)

                else:
                    myconf.add_channel(name, id, titles)

            else:
                myconf.add_channel(name, id)

            print("Channel name successfully added!")


        elif action == "list":
            needle = input(
                "Enter the YouTube Channel Name or ID to list " + 
                "[Leave blank for All]: "
            )
            if needle:
                myconf.list_channel(needle.lower())

            else:
                myconf.list_channel()

        elif action == "update":
            needle = input(
                "Enter the Youtube Channel Name: "
            )
            name = needle.lower()
            id = myconf.get_channel(name)
            if id:
                titles = input(
                    "Enter any Titles, separated by comma, that you " +
                    "want to filter for [Leave blank for no filter]: "
                )
                update_type = input(
                    "Do you want to update the current titles or " +
                    "do you want to overwrite the current titles " +
                    "[update/overwrite] "
                )

                if update_type.lower() not in constants.UPDATE_TYPES:
                    print(
                        "ERROR: Invalid update type! Please specify",
                        "update or ovewrite!"
                    )

                if titles:
                    title_list = myconf.split_titles(titles)

                    if title_list:
                        myconf.update_channel(id, title_list, update_type)

                    else:
                        title_list = [titles]
                        myconf.update_channel(id, title_list, update_type)

            else:
                print(
                    "Channel Name is not configured! Please use the",
                    "-c/--config add command instead!"
                )

            print("Channel name successfully updated!")

        elif action == "remove":
            needle = input(
                "Enter the Youtube Channel Name: "
            )
            name = needle.lower()
            id = myconf.get_channel(name)
            if id:
                myconf.remove_channel(id)

            else:
                print(
                    "Channel name is not configured! Nothing to remove!"
                )

            print("Channel name successfully removed!")

    elif myparser.action == "test":
        myauth = youtube_oauth()
        myauth.test_api()

    elif myparser.action == "video":
        pass

    elif myparser.action == "playlist":
        pass

    elif myparser.action == "search":
        pass

    logger.logger.info("Script finished!")

if __name__ == "__main__":
    main()