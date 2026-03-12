# mypy:ignore-errors
#!/usr/bin/env python3

import argparse
import os

import numpy as np
import random
from scipy.linalg import block_diag
from aspn23_lcm import (
    measurement_position_velocity_attitude,
    measurement_position,
    measurement_velocity,
)
from lcm import Event, EventLog
from navtk.navutils import (
    quat_to_dcm,
)

VEL_CHANNEL = '/sensor/simulated/velocity'
INSD_CHANNEL = '/sensor/ins-d/pva'
NOISE_STD = 0.05
random.seed(42)


def simulate_sensor_noise(vel_body, R_body, sigma_noise):
    """Simulates sensor noise for a body velocity sensor"""
    if isinstance(sigma_noise, (tuple, list)):
        noise_std = np.array([sigma_noise[0], sigma_noise[1], sigma_noise[2]])
    else:  # assumes uniform sigma across axes
        noise_std = np.array([sigma_noise, sigma_noise, sigma_noise])

    noise = np.random.normal(0, noise_std, size=(3,))

    # Inject noise into measurement
    vel_body = vel_body + noise

    # Inject noise covariance into measurement covariance
    R_body = R_body + np.diag(noise_std**2)

    return vel_body, R_body


def generate_example_dataset(logfile: str):
    basename, ext = os.path.splitext(logfile)
    log = EventLog(logfile)
    out_filename = f'{basename}_mod{ext}'
    out_log = EventLog(out_filename, 'w', True)

    msg: Event
    msg_count = 0
    pos = None
    vel = None
    for msg in log:
        if msg.channel == '/sensor/ins-d/pva':
            pva = measurement_position_velocity_attitude.decode(msg.data)
            pva.v3 *= -1

            # Write modified ins-d pva channel
            out_log.write_event(msg.timestamp, msg.channel, pva.encode())

            if (
                msg_count % 200 == 0.0
            ):  # Hard set a 1Hz write rate from 200Hz INS-D msg
                vel_ned = np.array([pva.v1, pva.v2, pva.v3])
                C_ned_to_body = quat_to_dcm(pva.quaternion).T
                vel_body = C_ned_to_body @ vel_ned
                # Compute for converted covariance
                R_body = (
                    np.transpose(C_ned_to_body)
                    @ np.array(pva.covariance)[3:6, 3:6]
                    @ C_ned_to_body
                )
                # Add simulated white noise
                vel_body_sensor, R_body_sensor = simulate_sensor_noise(
                    vel_body, R_body, NOISE_STD
                )

                # Create velocity message
                velbody_meas = measurement_velocity()
                velbody_meas.reference_frame = (
                    measurement_velocity.REFERENCE_FRAME_SENSOR
                )
                velbody_meas.x = vel_body_sensor[0]
                velbody_meas.y = vel_body_sensor[1]
                velbody_meas.z = vel_body_sensor[2]
                velbody_meas.num_meas = 3
                velbody_meas.covariance = R_body_sensor
                velbody_meas.time_of_validity.elapsed_nsec = pva.time_of_validity.elapsed_nsec

                # write event
                out_log.write_event(
                    msg.timestamp, VEL_CHANNEL, velbody_meas.encode()
                )
            msg_count += 1
        elif msg.channel == '/sensor/ublox-ZED-F9T/position':
            out_log.write_event(msg.timestamp, msg.channel, msg.data)
            pos = measurement_position.decode(msg.data)
        elif msg.channel == '/sensor/ublox-ZED-F9T/velocity':
            out_log.write_event(msg.timestamp, msg.channel, msg.data)
            vel = measurement_velocity.decode(msg.data)

            pva = measurement_position_velocity_attitude()
            pva.p1 = pos.term1
            pva.p2 = pos.term2
            pva.p3 = pos.term3
            pva.v1 = vel.x
            pva.v2 = vel.y
            pva.v3 = vel.z
            pva.time_of_validity.elapsed_nsec = (
                pos.time_of_validity.elapsed_nsec
            )
            pva.covariance = block_diag(
                pos.covariance, vel.covariance
            ).tolist()

            pva.num_integrity = 0
            pva.integrity = []
            pva.error_model = (
                measurement_position_velocity_attitude.ERROR_MODEL_NONE
            )
            pva.error_model_params = []
            pva.num_error_model_params = 0
            pva.header.context_id = 0
            pva.header.device_id = 0
            pva.header.sequence_id = 0
            pva.header.vendor_id = 0
            pva.reference_frame = 1
            pva.num_meas = 6
            pva.quaternion = [np.nan, np.nan, np.nan, np.nan]

            out_log.write_event(
                msg.timestamp, '/sensor/ublox-ZED-F9T/pva', pva.encode()
            )
        elif msg.channel == '/sensor/vn-100/imu':
            out_log.write_event(msg.timestamp, msg.channel, msg.data)
        elif msg.channel == '/sensor/bmp388/baro_pressure':
            out_log.write_event(msg.timestamp, msg.channel, msg.data)

    log.close()
    out_log.close()

    print(f'Modified log saved to {out_filename}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate example dataset from input log.'
    )
    parser.add_argument(
        'log', help='LCM log from which to generate example dataset.', type=str
    )
    args = parser.parse_args()
    generate_example_dataset(args.log)
