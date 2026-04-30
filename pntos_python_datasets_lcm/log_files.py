from os import path
from site import getsitepackages


def find_file(file: str) -> str:
    for site in getsitepackages():
        candidate = f'{site}/pntos_python_datasets_lcm/{file}'
        if path.exists(candidate):
            return candidate
    raise FileNotFoundError(f'Could not find {file} in site-packages.')

EXAMPLE_LCM_LOG = find_file('cobra_gps_ins_example_data.log')
