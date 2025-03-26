# BUFKIT Data Downloader

## Usage
```shell
$ python bin/download_data.py --model <model> [--archive]
```

* `--model`: Name of the model to download (required)

* `--archive`: Add downloaded model data to archive for dProg/dT (optional)

## Requirements
* Python 3.8 or later
* requests

## Configuration
All configuration of the script is handled in `etc/config.json`, below is an example.

```json
{
  "models": {
    "gfs": {
      "name": "gfs3",
      "sites": [
        "flg",
        "kflg"
      ],
      "runs": {
        "00": 4,
        "06": 10,
        "12": 16,
        "18": 22
      }
    },
    "hrrr": {
      "name": "hrrr",
      "sites": [
        "flg",
        "kflg"
      ],
      "runs": {
        "00": 3,
        "01": 4,
        "02": 5,
        "03": 6,
        "04": 7,
        "05": 8,
        "06": 9,
        "07": 10,
        "08": 11,
        "09": 12,
        "10": 13,
        "11": 14,
        "12": 15,
        "13": 16,
        "14": 17,
        "15": 18,
        "16": 19,
        "17": 20,
        "18": 21,
        "19": 22,
        "20": 23,
        "21": 0,
        "22": 1,
        "23": 2
      }
    }
  },
  "data_copy_path": ""
}
```

The models list should contain the name of each model you will run. For each model entry, there should be:
* `name` which is the filename of the model from the URL.
* `sites` a list of location identifiers to download data for.
* `runs` a dictionary with the model run hour in UTC as the key and then the hour in UTC that the model becomes available to download.

The `data_copy_path` is optional and can be left blank. This is to allow for copying the data from the download directory to another directory or server. To enable, just add a directory path or remote path and the data will be copied over either rsync or scp.