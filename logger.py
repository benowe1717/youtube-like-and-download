#!/usr/bin/env python3
import constants
from datetime import datetime
import logging, logging.config, os, sys

class youtube_logger():
    """
        This class is a wrapper for the logging python3 library
    """

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    TIME_FORMAT = constants.TIME_FORMAT
    NAME = constants.NAME

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    logger = ""
    logger_conf = "logging.conf"
    pid = os.getpid()
    hostname = os.uname().nodename

    def __init__(self):
        if not os.path.exists(self.logger_conf):
            print(f"ERROR: Unable to locate {self.logger_conf}!")
            exit(1)

        logging.config.fileConfig(self.logger_conf)
        self.logger = logging.getLogger(self.NAME)
        format_dict = {
            "event_date": self.get_current_time(),
            "hostname": self.hostname,
            "program": self.NAME,
            "pid": self.pid
        }
        self.logger = logging.LoggerAdapter(self.logger, format_dict)

    def get_current_time(self):
        return datetime.now().strftime(self.TIME_FORMAT)