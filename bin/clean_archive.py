# --------------------------------------------------------------------------------
# This software is in the public domain, furnished "as is", without technical
# support, and with no warranty, express or implied, as to its usefulness for
# any purpose.
#
# BUFKIT Data Downloader - clean_archive.py
# Cleans out archive files after X number of days
#
# Author:   Carter Humphreys, carter.humphreys@noaa.gov
# --------------------------------------------------------------------------------

import os
import json
from time import time
from pathlib import Path


def remove_old_files(directory, days):
	# Convert days to seconds (86400 seconds in a day)
	cutoff_time = time() - (days * 86400)

	for filename in os.listdir(directory):
		file_path = os.path.join(directory, filename)

		if os.path.isfile(file_path):
			file_mtime = os.path.getmtime(file_path)
			if file_mtime < cutoff_time:
				try:
					os.remove(file_path)
					print(f'Removed: {file_path}')
				except Exception as e:
					print(f'Error removing {file_path}: {e}')


def load_config(root_path):
	with open(root_path / 'etc' / 'config.json') as config_file:
		return json.load(config_file)


if __name__ == '__main__':
	# Set the program path
	script_path = Path(__file__).parent
	program_path = script_path.parent

	# Get the config
	config = load_config(program_path)

	# Get number of days to keep in archive
	num_days = int(config['num_days_to_archive'])

	# Clear out the archive directory
	remove_old_files(program_path / 'data' / 'archive', num_days)
