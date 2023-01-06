# YouTube Like and Download

YouTube Like and Download is a tool that allows you to automatically download and like YouTube videos from your favorite YouTubers.

The tool allows you to configure which YouTubers you want to download videos from and "filter" any specific titles of videos you want to download, while also "leaving a like" on the downloaded video to show your support.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- You will need an Developer API Key from Google: [How to Create a Google Developer Account](https://developers.google.com/youtube/v3/getting-started#intro)
- Python3 (I tested on Python 3.8.10)
- Linux (I did not test on Windows or MacOS) (I did test on Ubuntu 20.04.5 LTS though I imagine any Linux Distribution should work)

## Installing

To install YouTube Like and Download, follow these steps:

- Download and extract the file from: [YouTube Like and Download Main](https://github.com/benowe1717/youtube-like-and-download/archive/refs/heads/main.zip)
- Replace all lines in `.creds` with a single line containing your API Key
- Download your `client_secrets.json` file from the GCP (Google Cloud Platform, your Developer account) and replace the placeholder `client_secrets.json` file with yours

## Using

To use YouTube Like and Download, follow these steps:

- Start by configuring the script to look at YouTubers you want by: ```python3 main.py --config add``` and follow the prompts
- List your current configuration by running: ```python3 main.py --config list```
- To update any YouTubers information (say if the Channel Name changes or if you want to filter on a new title): ```python3 main.py --config update```
- Finally to remove any YouTubers and stop downloading their videos: ```python3 main.py --config delete```
- If you need to change the download path for saving the videos to: ```python3 main.py --download-path /some/path/goes/here```
    - NOTE: Please make sure that you have write permissions to this location or the videos will fail to save
- Last but not least, to actually run the script and download videos: ```python3 main.py```

## Contributing to YouTube Like and Download

To contribute to YouTube Like and Download, follow these steps:

1. Fork this repository
2. Create a branch: `git checkout -b <branch_name>`
3. Make your changes and commit them: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <youtube-like-and-download>/<branch_name>`
5. Create the Pull Request

Alternatively see the GitHub documentation on [creating a pull request](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/creating-a-pull-request).

## Contributors

Thanks to the following people who have contributed to this project:

- @benowe1717

## Contact

For help or support on this repository, follow these steps:

- [Issues](https://github.com/benowe1717/youtube-like-and-download/issues)
