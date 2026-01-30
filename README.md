# pntos-python-dataset

This repository contains a collection of example datasets for pntos-python:

`cobra_gps_ins_example_data.log` is based off of `2025_05_19_route07.log`. Specifically, it
contains a subset of the following channels:
* `/sensor/bmp388/baro_pressure`
* `/sensor/ins-d/pva`
* `/sensor/ublox-ZED-F9T/position`
* `/sensor/ublox-ZED-F9T/velocity`
* `/sensor/ublox-ZED-F9T/pva`
* `/sensor/simulated/velocity`
* `/sensor/vn-100/imu`

The example log can be recreated from the original log using `generate_example_dataset.py`. To run
this script the necessary python environment must be set up.

### Python Environment Setup
Create clean venv:

```Shell
python3 -m venv .venv --prompt pntos-python-datasets
```

Source the virtual environment (bash/zsh):
```Shell
source .venv/bin/activate
```

Upgrade pip (recommended):
```Shell
pip install --upgrade pip
```

Install dependencies via `requirements.txt`:
```Shell
pip install -v -r requirements.txt --extra-index-url=$UV_INDEX
```

### Generating New Log
Generating a log can be done by:
```Shell
pntos_python_datasets/generate_example_dataset.py <path_to_logfile>
```

> [!Note]
> `generate_example_datasets.py` will create an output logfile in the same directory as the input logfile under the the new name `<input_logfile_name>_mod.log`.
> To update `EXAMPLE_LCM_LOG` with a new log for downstream projects, the new log must be renamed to replace any existing `cobra_gps_ins_example_data.log`.
