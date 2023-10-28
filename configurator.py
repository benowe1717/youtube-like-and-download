#!/usr/bin/env python3
import constants
import os, logging, yaml

class youtube_configurator():
    """
        This class is designed to help manage the local configuration
        file that stores the YouTube Channel Names and IDs
    """

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    base_path = os.path.dirname(os.path.realpath(__file__))
    conf = f"{base_path}/config.yaml"
    config = {}
    logger = ""

    def __init__(self):
        if not os.path.exists(self.conf):
            print(f"ERROR: Unable to locate {self.conf}!")
            exit(1)

        self.logger = logging.getLogger(constants.NAME)
        with open(self.conf, "r") as file:
            self.config = yaml.safe_load(file)

    def get_channel(self, name):
        for key, value in self.config['channels'].items():
            if value['channel_name'].lower() == name:
                return key
        return False

    def split_titles(self, titles):
        if "," in titles:
            title_list = titles.split(",")
            i = 0
            while i < len(title_list):
                title_list[i] = title_list[i].strip()
                i += 1
            return title_list
        return False

    def add_channel(self, name, id, titles=None):
        try:
            if id in self.config['channels'].keys():
                print(
                    "This YouTube Channel is already configured! Please",
                    "use the -c/--config update command instead!"
                )

            if titles:
                self.config['channels'][id] = {
                    'channel_name': name,
                    'channel_titles': titles
                }

            else:
                self.config['channels'][id] = {
                    'channel_name': name,
                    'channel_titles': None
                }
        except AttributeError:
            # AttributeError: 'NoneType' object has no attriute 'keys'
            # This happens if there are no channels configured yet,
            # this is fine
            if titles:
                self.config = {
                    'channels': {
                        id: {
                            'channel_name': name,
                            'channel_titles': titles
                        }
                    }
                }

            else:
                self.config = {
                    'channels': {
                        id: {
                            'channel_name': name,
                            'channel_titles': None
                        }
                    }
                }

        with open(self.conf, "w") as file:
            yaml.dump(self.config, file)

    def list_channel(self, name=None):
        if name:
            for key, value in self.config["channels"].items():
                if value["channel_name"].lower() == name:
                    print(yaml.dump(value, default_flow_style=False))
                    return True

            print("No channels match that name!")

        else:
            print(yaml.dump(self.config, default_flow_style=False))

    def update_channel(self, id, titles, update_type):
        if update_type == "update" or update_type == "u":
            if isinstance(
                self.config['channels'][id]['channel_titles'], list
            ):
                for title in titles:
                    self.config['channels'][id]['channel_titles'].append(title)

            else:
                title_list = []
                title_list.append(
                    self.config['channels'][id]['channel_titles']
                )
                for title in titles:
                    title_list.append(title)

                self.config['channels'][id]['channel_titles'] = title_list

        elif update_type == "overwrite" or update_type == "o":
            self.config['channels'][id]['channel_titles'] = titles

        with open(self.conf, "w") as file:
            yaml.dump(self.config, file)

    def remove_channel(self, id):
        self.config['channels'].pop(id)

        with open(self.conf, "w") as file:
            yaml.dump(self.config, file)