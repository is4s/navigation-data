#!/usr/bin/env python3
# mypy:ignore-errors


import argparse
import os

import numpy as np
import random
from scipy.linalg import block_diag
from aspn23_lcm import (
    measurement_position_velocity_attitude,
    measurement_position,
    measurement_velocity,
    measurement_direction_3d_to_points,
    type_direction_3d_to_point,
)
from lcm import Event, EventLog
from navtk.navutils import (
    quat_to_dcm,
    delta_lat_to_north,
    delta_lon_to_east,
    north_to_delta_lat,
)
from matplotlib.pyplot import (
    show,
    subplots,
)
from matplotlib.patches import (
    Circle,
)

VEL_CHANNEL = '/sensor/simulated/velocity'
INSD_CHANNEL = '/sensor/ins-d/pva'
NOISE_STD = 0.05
random.seed(42)

DIRECTIONTOKNOWNFEATURE_CHANNEL = '/sensor/simulated/directiontoknownfeature'
directiontoknownfeature_noise = 0.01
vision_sensor_leverarm = np.array([0.80, 0.0, 0.05]).reshape(3,1)

lat, lon, alt = [[] for i in range(3)]


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

def simulate_bearing_noise(bearing, R_bearing, sigma_noise):
    """Simulates sensor noise for a body velocity sensor"""
    if isinstance(sigma_noise, (tuple, list)):
        noise_std = np.array([sigma_noise[0], sigma_noise[1]])
    else:  # assumes uniform sigma across axes
        noise_std = np.array([sigma_noise, sigma_noise])

    noise = np.random.normal(0, noise_std, size=(2,))
    noise = noise.reshape(2,1)

    # Inject noise into measurement
    bearing = bearing + noise

    # Inject noise covariance into measurement covariance
    R_bearing = R_bearing + np.diag(noise_std**2)

    return bearing, R_bearing

def generate_known_features(num_points, x_range, y_range, z_range):

    x = np.random.uniform(x_range[0], x_range[1], num_points)
    y = np.random.uniform(y_range[0], y_range[1], num_points)
    z = np.random.uniform(z_range[0], z_range[1], num_points)

    return np.column_stack((x, y, z))

KNOWN_FEATURES_LLA = generate_known_features(100, (0.693700, 0.694200), (-1.469000, -1.467800), (0, 3))
BOUND = []

def generate_example_dataset(logfile: str):
    basename, ext = os.path.splitext(logfile)
    log = EventLog(logfile)
    out_filename = f'{basename}_mod{ext}'
    out_log = EventLog(out_filename, 'w', True)

    msg: Event
    msg_count = 0
    bound_count = 0
    pos = None
    vel = None
    for msg in log:
        if msg.channel == '/sensor/ins-d/pva':
            pva = measurement_position_velocity_attitude.decode(msg.data)
            pva.v3 *= -1

            lat.append(pva.p1)
            lon.append(pva.p2)
            alt.append(pva.p3)

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
                out_log.write_event(msg.timestamp, VEL_CHANNEL, velbody_meas.encode())

                # Basic Kinematics
                pos_truth_lla = np.array([pva.p1, pva.p2, pva.p3]).reshape(3,1)

                C_ned_to_body = quat_to_dcm(pva.quaternion).T

                C_body_to_sensor = np.array(
                    [
                        [ 0, 0, 1],
                        [ 0, 1, 0],
                        [-1, 0, 0],
                    ]
                )

                # Initialize LCM message for multiple observations
                multi_feature_msg = measurement_direction_3d_to_points()
                multi_feature_msg.time_of_validity.elapsed_nsec = pva.time_of_validity.elapsed_nsec
                multi_feature_msg.num_obs = 0
                multi_feature_msg.obs = []

                theta_max = 60 * np.pi / 180
                sensor_bound = 0

                for i, feature_lla in enumerate(KNOWN_FEATURES_LLA):

                    delta_lla = feature_lla.reshape(3,1) - pos_truth_lla

                    dn = delta_lat_to_north(delta_lla[0].item(), pva.p1, pva.p3)
                    de = delta_lon_to_east(delta_lla[1].item(), pva.p1, pva.p3)
                    dd = -delta_lla[2].item()

                    r_ned = np.array([dn, de, dd]).reshape(3,1)
                    r_body = C_ned_to_body @ r_ned
                    r_sensor = C_body_to_sensor @ (r_body - vision_sensor_leverarm)

                    sensor_bound = r_ned[2] * np.tan(theta_max)

                    if -sensor_bound <= r_ned[0] <= sensor_bound and -sensor_bound <= r_ned[1] <= sensor_bound:

                        # Unit Vector & Sine Space
                        u = r_sensor / np.linalg.norm(r_sensor)
                        sine_meas = np.array([u[1], u[2]]).reshape(2,1)

                        # Noise injection
                        R_dir = np.zeros((2,2))
                        noisy_sine, _ = simulate_bearing_noise(
                            sine_meas, R_dir, directiontoknownfeature_noise
                        )

                        # Populate Measurement
                        obs = type_direction_3d_to_point()
                        obs.reference_frame = type_direction_3d_to_point.REFERENCE_FRAME_SINE_SPACE
                        obs.obs = [float(noisy_sine[0,0]), float(noisy_sine[1,0])]
                        obs.covariance = [[directiontoknownfeature_noise**2, 0],
                                        [0, directiontoknownfeature_noise**2]]

                        obs.remote_point.id = i + 1
                        obs.remote_point.position1 = float(feature_lla[0].item())
                        obs.remote_point.position2 = float(feature_lla[1].item())
                        obs.remote_point.position3 = float(feature_lla[2].item())
                        obs.remote_point.position_reference_frame = 1
                        obs.remote_point.num_position_components = 3
                        obs.remote_point.position_covariance = [
                            [1.0, 0.0, 0.0],
                            [0.0, 1.0, 0.0],
                            [0.0, 0.0, 1.0]
                        ]

                        multi_feature_msg.obs.append(obs)
                        multi_feature_msg.num_obs += 1


                if bound_count % 20 == 0:
                    sensor_bound_lat = north_to_delta_lat(sensor_bound.item(), pos_truth_lla[0].item(), pos_truth_lla[2].item())
                    circle = Circle((pos_truth_lla[1].item(), pos_truth_lla[0].item()), sensor_bound_lat, color='black', fill=False, lw=2, alpha=0.6)
                    BOUND.append(circle)

                bound_count += 1

                # Write the message containing all observed features
                if multi_feature_msg.num_obs > 0:
                    out_log.write_event(msg.timestamp, DIRECTIONTOKNOWNFEATURE_CHANNEL, multi_feature_msg.encode())

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

            out_log.write_event(msg.timestamp, '/sensor/ublox-ZED-F9T/pva', pva.encode())
        elif msg.channel == '/sensor/vn-100/imu':
            out_log.write_event(msg.timestamp, msg.channel, msg.data)
        elif msg.channel == '/sensor/bmp388/baro_pressure':
            out_log.write_event(msg.timestamp, msg.channel, msg.data)

    log.close()
    out_log.close()

    fig, ax = subplots(num="Trajectory")

    ax.plot(lon, lat)
    ax.scatter(KNOWN_FEATURES_LLA[:,1], KNOWN_FEATURES_LLA[:,0])

    for c in BOUND:
        ax.add_patch(c)

    ax.relim()
    ax.autoscale_view()
    ax.set_aspect('equal')
    show()

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
