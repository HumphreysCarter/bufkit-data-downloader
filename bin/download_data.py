import json
import shutil
import requests
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path


class BufkitDataDownloader:

	def __init__(self, model_name, archive_data):
		# Set inputs
		self.model = model_name
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
			download_folder.mkdir()
		if not archive_folder.exists() and self.archive_data:
			archive_folder.mkdir()

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

		# Build the URL
		base_url = 'https://mtarchive.geol.iastate.edu/'
		model_url = f'{run:%Y}/{run:%m}/{run:%d}/bufkit/{run:%H}/{self.model}/{self.model.replace('gfs', 'gfs3')}_{site}.buf'

		return base_url + model_url

	def copy_data(self):
		# Get data directory
		source = Path(self.program_path, 'data').resolve().as_posix() + '/'

		# Set remote path from config
		remote = self.config['data_copy_path']

		# Run scp
		if remote is not None and remote != "":
			subprocess.run(['scp', '-r', source, remote], check=True)


if __name__ == '__main__':
	# Add command line arguments
	parser = argparse.ArgumentParser()
	parser.add_argument('--model', type=str, required=True, help="Model name to download data for")
	parser.add_argument('--archive', action='store_true', default=False, help="Copy data to data archive")

	# Read arguments
	args = parser.parse_args()

	# Run the script
	BufkitDataDownloader(args.model, args.archive)
