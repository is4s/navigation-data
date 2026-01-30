from subprocess import Popen
import argparse
from .log_files import EXAMPLE_LCM_LOG, EXAMPLE_ROS_LOG


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Play LCM or ROS example data.'
    )
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument(
        '-t',
        '--transport',
        choices=('lcm', 'ros'),
        default='lcm',
        help='Whether to playback the LCM or ROS dataset. Defaults to LCM.',
    )
    parser.add_argument(
        '-r',
        '--ros_rate',
        default='1',
        help='When using ROS, rate at which to play back the bagfile. Defaults to 1x.',
    )
    return parser.parse_args()


def play_dataset() -> None:
    args = get_args()
    if args.transport == 'lcm':
        cmd = [
            'lcm-logplayer-gui',
            '--paused',
            '--lcm-url=tcpq://localhost',
            EXAMPLE_LCM_LOG,
        ]
    elif args.transport == 'ros':
        cmd = [
            'ros2',
            'bag',
            'play',
            '--start-paused',
            f'-r {args.ros_rate}',
            EXAMPLE_ROS_LOG,
        ]
    else:
        raise ValueError(f'Invalid transport flag: "{args.transport}".')
    if args.verbose:
        print(f'Running the command:\n{" ".join(cmd)}')
    process = Popen(cmd)
    process.wait()


if __name__ == '__main__':
    play_dataset()
