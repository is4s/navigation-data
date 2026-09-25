from subprocess import Popen
import argparse
from .log_files import EXAMPLE_LCM_LOG


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Play LCM example data.'
    )
    parser.add_argument('-v', '--verbose', action='store_true')
    return parser.parse_args()


def play_lcm_dataset() -> None:
    args = get_args()
    cmd = [
        'lcm-logplayer-gui',
        '--paused',
        '--lcm-url=tcpq://localhost',
        EXAMPLE_LCM_LOG,
    ]
    if args.verbose:
        print(f'Running the command:\n{" ".join(cmd)}')
    process = Popen(cmd)
    process.wait()


if __name__ == '__main__':
    play_lcm_dataset()
