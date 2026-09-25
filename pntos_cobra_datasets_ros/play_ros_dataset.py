from subprocess import Popen
import argparse
from .log_files import EXAMPLE_ROS_LOG


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Play ROS example data.'
    )
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument(
        '-r',
        '--ros_rate',
        default='1',
        help='When using ROS, rate at which to play back the bagfile. Defaults to 1x.',
    )
    return parser.parse_args()


def play_ros_dataset() -> None:
    args = get_args()
    cmd = [
        'ros2',
        'bag',
        'play',
        '--start-paused',
        f'-r {args.ros_rate}',
        EXAMPLE_ROS_LOG,
    ]
    if args.verbose:
        print(f'Running the command:\n{" ".join(cmd)}')
    process = Popen(cmd)
    process.wait()


if __name__ == '__main__':
    play_ros_dataset()
