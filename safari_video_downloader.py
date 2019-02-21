#!/usr/bin/env python3
# A resumable Safari Books Online Video downloader
# Main reference: https://mvdwoord.github.io/tools/2017/02/02/safari-downloader.html

from bs4 import BeautifulSoup
import requests
import os
import subprocess
import unicodedata
import string

import config

class SafariDownloader:
    def __init__(self, url, output_folder, username, password, domain, downloader_path):
        self.output_folder = output_folder
        self.username = username
        self.password = password
        self.domain = domain
        self.downloader_path = downloader_path

        req = requests.get(url)
        soup = BeautifulSoup(req.text, 'html.parser')
        self.title = soup.find('h1').text
        self.topics = soup.find_all('li', class_='toc-level-1') # top-level topic titles
        # Update youtube-dl first
        subprocess.run([self.downloader_path, "-U"])

    def validify(self, filename):
        valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
        valid_chars = frozenset(valid_chars)
        # The unicodedata.normalize call replaces accented characters with the unaccented equivalent,
        # which is better than simply stripping them out. After that all disallowed characters are removed.
        cleaned_filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')
        return ''.join(c for c in cleaned_filename if c in valid_chars)

    def download(self):
        for index, topic in enumerate(self.topics):
            topic_name = topic.a.text
            # Creating folder to put the videos in
            save_folder = '{}/{}/{:03d} - {}'.format(self.output_folder, self.title, index + 1, topic_name)
            os.makedirs(save_folder, exist_ok=True)
            # You can choose to skip these topic_name, comment these three lines if you do not want to skip any
            if topic_name in ('Keynotes', 'Strata Business Summit', 'Sponsored'):
                print("Skipping {}...".format(topic_name))
                continue
            for index, video in enumerate(topic.ol.find_all('a')):
                video_name = '{:03d} - {}'.format(index + 1, video.text)
                video_name = self.validify(video_name)
                video_url = self.domain + video.get('href')
                video_out = '{}/{}.mp4'.format(save_folder, video_name)
                video_out = video_out.replace(':', '-')
                # Check if file already exists
                if os.path.isfile(video_out):
                    print("File {} already exists! Skipping...".format(video_out))
                    continue
                print("Downloading {} ...".format(video_name))
                subprocess.run([self.downloader_path, "-u", self.username, "-p", self.password, "--verbose", "--output", video_out, video_url])

if __name__ == '__main__':
    app_config = config.Config
    for url in app_config.URLS:
        downloader = SafariDownloader(url=url, output_folder=app_config.OUTPUT_FOLDER,
                                      username=app_config.USERNAME, password=app_config.PASSWORD,
                                      domain=app_config.DOMAIN, downloader_path=app_config.DOWNLOADER)
        downloader.download()
