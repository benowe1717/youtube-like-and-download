#!/usr/bin/env python3
import constants
import argparse

class arg_parse():
    """
        This class is a wrapper for the argparse python3 library
    """

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    PROGRAM_NAME = constants.PROGRAM_NAME
    PROGRAM_DESCRIPTION = constants.PROGRAM_DESCRIPTION
    VERSION = constants.VERSION
    AUTHOR = constants.AUTHOR
    REPO = constants.REPO

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    parser = ""
    args = ""
    action = ""
    config_action = ""
    debug = False
    download_path = ""
    target = ""
    hours = -1

    def __init__(self, args):
        self.parser = argparse.ArgumentParser(
            prog=self.PROGRAM_NAME, description=self.PROGRAM_DESCRIPTION
        )
        self.parser.add_argument(
            "-v", "--version", action="store_true", required=False,
            help="Show this program's current version"
        )
        self.parser.add_argument(
            "-d", "--debug", action="store_true", required=False,
            help="Enable debug logging"
        )
        self.parser.add_argument(
            "-t", "--test", action="store_true", required=False,
            help="""Test the API using the credentials on file 
            before taking any actions"""
        )
        self.parser.add_argument(
            "-o", "--download-path", nargs=1, required=False,
            help="Specify the full path to where videos should be saved"
        )
        self.parser.add_argument(
            "-i", "--video", nargs="+", required=False,
            help="Like and download a specific video by it's URL or ID"
        )
        self.parser.add_argument(
            "-p", "--playlist", nargs="+", required=False,
            help="Like and download every video from a playlist URL or ID"
        )
        self.parser.add_argument(
            "-s", "--search", nargs=1, required=False,
            help="""Search for any newly released videos from the 
            configured channels for the past N hours"""
        )
        self.parser.add_argument(
            "-c", "--config", nargs=1, required=False,
            help="""[add|list|update|remove] the configuration file 
            of YouTube channels to download videos from"""
        )
        self.args = self.parser.parse_args()

        if len(args) == 1:
            self.parser.print_help()
            self.parser.exit()

        if self.args.version:
            self.printVersion()
            self.parser.exit()

        if self.args.debug:
            self.debug = True

        if self.args.test:
            self.action = "test"

        if self.args.video:
            if self.args.download_path is None:
                self.parser.error("--video requires --download-path")

            else:
                self.action = "video"
                self.download_path = self.args.download_path
                self.target = self.args.video

        if self.args.playlist:
            if self.args.download_path is None:
                self.parser.error("--playlist requires --download-path")

            else:
                self.action = "playlist"
                self.download_path = self.args.download_path
                self.target = self.args.playlist

        if self.args.config:
            if self.args.config[0] in constants.CONFIG_ACTIONS:
                self.action = "config"
                self.config_action = self.args.config[0]

            else:
                self.parser.error(
                    "--config only supports " + 
                    ", ".join(constants.CONFIG_ACTIONS)
                )

        if self.args.search:
            self.action = "search"
            self.hours = self.args.search[0]

    def printVersion(self):
        """
            This function is used in the argparse library to print the
            current version of this application
        """
        print(f"{self.PROGRAM_NAME} v{self.VERSION}")
        print(
            "This is free software:",
            "you are free to change and redistribute it."
        )
        print("There is NO WARRANTY, to the extent permitted by law.\n")
        print(f"Written by {self.AUTHOR}; see below for original code")
        print(f"<{self.REPO}>")