# --------------------------------------------------------------------------------
# This software is in the public domain, furnished "as is", without technical
# support, and with no warranty, express or implied, as to its usefulness for
# any purpose.
#
# BUFKIT Data Downloader - download_data.py
# A script to allow for automated downloading of BUFR profile data for BUFKIT.
#
# Author:   Carter Humphreys, carter.humphreys@noaa.gov
# --------------------------------------------------------------------------------

import re
import json
import shutil
import platform
import requests
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


class BufkitDataDownloader:

    def __init__(self, model_name, data_source, archive_data):
        # Set inputs
        self.model = model_name
        self.data_source = data_source
        self.archive_data = archive_data

        # Set the program path
        script_path = Path(__file__).parent
        self.program_path = script_path.parent

        # Load the config
        self.config = self.load_config()

        # Get model run time
        self.model_run = self.get_latest_run()

        # Download data for each site
        for site in self.config['models'][self.model]['sites']:
            self.download_data(site)

        # Copy data directory
        self.copy_data()

    def load_config(self):
        config_file = Path(self.program_path, 'etc', 'config.json')
        with open(config_file) as config_file:
            return json.load(config_file)

    def get_latest_run(self):
        now = datetime.now(timezone.utc)
        now_hour = now.hour
        runs = self.config['models'][self.model]['runs']

        # Convert to list of tuples [(run_hour, available_hour)]
        sorted_runs = sorted(
            ((int(run), int(available)) for run, available in runs.items()),
            key=lambda x: x[1]
        )

        latest_run_hour = None
        for run_hour, available_hour in sorted_runs:
            if now_hour >= available_hour:
                latest_run_hour = run_hour
            else:
                break

        # If no run is yet available today, fall back to last run from yesterday
        if latest_run_hour is None:
            latest_run_hour = sorted_runs[-1][0]
            run_date = now.date() - timedelta(days=1)
        else:
            run_date = now.date()

        # Build datetime object with the correct date and run hour
        run_time = datetime.combine(run_date, datetime.min.time()).replace(hour=latest_run_hour)

        return run_time

    def download_data(self, site):
        # Set the download folder
        download_folder = Path(self.program_path, 'data', 'latest')
        archive_folder = Path(self.program_path, 'data', 'archive')

        # Ensure directories exists
        if not download_folder.exists():
            download_folder.mkdir(parents=True)
        if not archive_folder.exists() and self.archive_data:
            archive_folder.mkdir(parents=True)

        # Build the download URL
        download_url = self.build_download_url(site)

        # Download the file
        try:
            # Proceed with GET request to download the file
            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            # Determine filename from URL
            filename = Path(download_url).name
            file_path = download_folder / filename

            # Save file to disk
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f'Downloaded {self.model_run} {self.model} data for {site}')

            # Archive the data
            if self.archive_data:
                archive_path = archive_folder / f'{self.model_run:%y%m%d%H}.{filename}'
                shutil.copy2(file_path, archive_path)
                print(f'Added {self.model_run} {self.model} data for {site} to archive.')

        except requests.RequestException as e:
            print(f'Download failed for {self.model} {site}: {e}')

    def build_download_url(self, site):
        # Get the current run time
        run = self.model_run

        # Get model file name
        model_filename = self.config['models'][self.model]['name']

        # Build IA State BUFKIT url
        if self.data_source == 'iastate':
            base_url = 'https://mtarchive.geol.iastate.edu/'
            path = f'{run:%Y}/{run:%m}/{run:%d}/bufkit/{run:%H}/{self.model.lower()}/'

            # namnest is nam4km at iastate, so this will need to be corrected
            model_filename = model_filename.lower().replace('namnest', 'nam4km')
            path = path.lower().replace('namnest', 'nam4km')

        # Build PSU BUFKIT url
        elif self.data_source == 'psu':
            base_url = 'https://www.meteo.psu.edu/bufkit/data/'
            path = f'{self.model.upper()}/{run:%H}/'

        else:
            return None

        return f'{base_url}{path}{model_filename}_{site}.buf'

    def copy_data(self):
        # Get data directory
        source = Path(self.program_path, 'data').resolve().as_posix() + '/'

        # Set remote path from config
        remote = self.config['data_copy_path']

        # Copy files to remote
        if remote is not None and remote != "":

            # rsync is usually unavailable on windows, so use scp
            if platform.system() == 'Windows':
                subprocess.run(['scp', '-r', source, remote], check=True)

            # rsync on Linux
            else:
                subprocess.run(['rsync', '-azvh', source, remote, '--delete'], check=True)


if __name__ == '__main__':
    # Add command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, required=True, help="Model name to download data for")
    parser.add_argument('--data-source', required=True, choices=['iastate', 'psu'], help='Source to download data from')
    parser.add_argument('--archive', action='store_true', default=False, help='Copy data to data archive')

    # Read arguments
    args = parser.parse_args()

    # Run the script
    BufkitDataDownloader(args.model, args.data_source, args.archive)
