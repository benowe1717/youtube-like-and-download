#!/usr/bin/env python3
from datetime import datetime
import logging, logging.config, os

class youtubeLogger():
    'This class servers to support the youtubeDL and youtubeOauth classes through standardized log formatting'

    # Note that there are no "private" objects or methods in the
    # Python class structure, but it is generally accepted that
    # methods and objects with a single "_" (underscore) preceding
    # the name indicates something "not to be messed with". So I'm
    # adopting that convention to denote "private" objects and methods

    #########################
    ### PRIVATE CONSTANTS ###
    #########################
    _HOSTNAME = os.uname().nodename
    _PID = os.getpid()
    _PROGRAM = "youtubeDL"
    _TIME_FORMAT = "%b %d %H:%M:%S"

    ########################
    ### PUBLIC CONSTANTS ###
    ########################

    #######################
    ### PRIVATE OBJECTS ###
    #######################

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    # If you need to specify another configuration file for logging
    # or need to specify another name or different path
    # change the config variable to your named conf file
    config = "logging.conf"
    logger = ""

    def __init__(self):
        try:
            logging.config.fileConfig(self.config)
            self.logger = logging.getLogger("youtubeDL")
        except KeyError as e:
            # If the conf file is missing or messed up then we'll get an error
            # about the key "formatters" not existing, but it's simply b/c they're gone
            print(f"ERROR: Unable to locate the configuration file: {self.config}!")
            print(f"DEBUG: Error Description: {e}")
            exit(1)

    def _getCurrentTime(self):
        'This method is used to get the current time in the appropriate SYSLOG format'
        # https://strftime.org/
        return datetime.now().strftime(self._TIME_FORMAT)

    def logMsg(self, msg):
        'This method is used to log all messages out to the configured log file and should be used for all standard messages'
        self.logger.info(f"{self._getCurrentTime()} {self._HOSTNAME} {self._PROGRAM}[{self._PID}] {msg}")

    def logDebugMsg(self, msg):
        'This method is used to log all messages out to the configured log file and should only be used for debugging level messages'
        self.logger.debug(f"{self._getCurrentTime()} {self._HOSTNAME} {self._PROGRAM}[{self._PID}] {msg}")