# Copyright (c) Prophesee S.A. - All Rights Reserved
#
# Subject to Prophesee Metavision Licensing Terms and Conditions ("License T&C's").
# You may not use this file except in compliance with these License T&C's.
# A copy of these License T&C's is located in the "licensing" folder accompanying this file.

"""
Script used to track objects, based on metavision_generic_tracking.py.
The script will:
- Track objects found in the input RAW file. If no RAW file is passed, then it will get the live stream of the first available camera.
- Return CSV files containg the timestamp, x and y coordinates (and the corresponding floor values), height and width of bounding boxes, object ID and event ID.
- Show the corresponding video feed of the camera.
"""

import cv2
import numpy as np
import datetime
import os, sys
import csv

from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_analytics import TrackingAlgorithm, TrackingConfig, draw_tracking_results
from metavision_sdk_core import OnDemandFrameGenerationAlgorithm
from metavision_sdk_cv import ActivityNoiseFilterAlgorithm, TrailFilterAlgorithm
from metavision_sdk_ui import EventLoop, BaseWindow, MTWindow, UIAction, UIKeyEvent

class Inputs:
    def __init__(self, args):
        self.input_path = args.raw_file_path
        self.process_from = args.process_from * 1e6
        if args.process_to is not None:
            self.process_to = args.process_to * 1e6
        else:
            self.process_to = None
        self.bias_file = args.bias_file_path
        self.update_frequency = float(args.update_frequency)
        if args.accumulation_time > 0:
            self.accumulation_time = int(args.accumulation_time * 1e6)
        else:
            self.accumulation_time = int(1e6/args.update_frequency)
        self.min_size = args.min_size
        self.max_size = args.max_size
        self.activity_time_ths = args.activity_time_ths
        self.activity_ths = args.activity_ths
        self.activity_trail_ths = args.activity_trail_ths
        if args.output_csv_path:
            self.output_csv_path = args.output_csv_path
        else:
            self.output_csv_path = os.getcwd() + '/EVK_'
        self.measurement_time = args.outputs_csv_interval * 1e6
        self.save_flag = args.save_flag
        self.out_video = args.out_video
        self.draw_bb = args.draw_bounding_boxes
        self.replay_factor = args.replay_factor
        self.no_runs = args.no_runs

def parse_args():
    import argparse
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description='Object Tracking', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # Base options
    base_options = parser.add_argument_group('Base options')
    base_options.add_argument('-i', '--input-raw-file', dest='raw_file_path', default='',
                              help='Path to input RAW file. If not specified, the live stream of the first available camera is used.'
                              "If it's a camera ID, it will try to open that camera instead.")
    base_options.add_argument('-pf','--process-from', dest='process_from', type=int, default=0,
                              help='Time at which the algorithm starts processing events. If not specified, the algorithm starts processing events from the beginning. Unit: seconds. Default value: 0s.')
    base_options.add_argument('-pt','--process-to', dest='process_to', type=int, default=None,
                              help='Time at which the algorithm stops processing events. If not specific, the algorithm will have to be manually stopped. Unit: seconds. Default value: None.')
    base_options.add_argument('-bf', '--bias-file', dest='bias_file_path',default='',
                              help='Path to BIAS file to modify the parameters of the sensor of the event-based camera. Default: \'\'.')
    #add ROI as input?
    # Algorithm options
    algorithm_options = parser.add_argument_group('Algorithm options')
    algorithm_options.add_argument('-uf', '--update-frequency', dest='update_frequency', type=int, default=1000,
                              help='Frequency of the frame generation of the tracking algorithm. Unit: Hertz. Default: 1000Hz.')
    algorithm_options.add_argument('-at', '--accum-time', dest='accumulation_time', type=float, default=0.,
                              help='Time interval that the tracking algorithm uses to accumulate events into a frame. Unit: seconds. Default: inverse of [update_frequency].')
    # Object options
    object_size_options = parser.add_argument_group('Object options')
    object_size_options.add_argument('-mins', '--min-size', dest='min_size', type=int, default=10,
                                    help='Minimal size of an object to track (or the resulting bounding box). Unit: pixels. Default: 10px.')
    object_size_options.add_argument('-maxs', '--max-size', dest='max_size', type=int, default=100,
                                    help='Maximal size of an object to track (or the resulting bounding box). Unit: pixels. Default: 100px.')
    # Filtering options
    filter_options = parser.add_argument_group('Filtering options')
    filter_options.add_argument('--activity-time-ths', dest='activity_time_ths', type=int, default=10000,
                                help='Length of the time window for activity filtering (Disabled if the threshold is equal to 0).')
    filter_options.add_argument('--activity-ths', dest='activity_ths', type=int, default=1,
                                help='Minimum number of events in the neighborhood.')
    filter_options.add_argument('--activity-trail-ths', dest='activity_trail_ths', type=int, default=1000,
                                help='Length of the time window for trail filtering (in us).')
    # Saving Options
    saving_options = parser.add_argument_group('Saving options')
    saving_options.add_argument('-csv', '--save-csv-path', dest='output_csv_path', type=str, default='',
                                help='File path of output CSV files that contain the information of detected objects, excluding the file extension. Default: \'EVK_\{timestamp\}.csv\' at location of script.')
    saving_options.add_argument('-csvt', '--save-csv-interval', dest='outputs_csv_interval', type=int, default=60,
                                help='Time interval of tracked information saved into a single CSV file. For measurement times longer than the input interval time, several CSV files are saved with their corresponding timestamps. Unit: seconds. Default: 60s.')
    saving_options.add_argument('-csvf', '--save-flag', dest='save_flag', type=bool, default=True,
                                help="Flag that determines if measurements are recorded. Default: True.")
    saving_options.add_argument('-csvn', '--csv-runs', dest='no_runs', type=int, default=5,
                                help="Determines the number of runs that are required for saving. Default: 5 runs.")
    # Outcome Options
    outcome_options = parser.add_argument_group('Outcome options')
    outcome_options.add_argument('-ov', '--out-video', dest='out_video', type=str, default='',
                                help='File path of output AVI where the video feed is saved with [update frequency] frames per second. If not specified, the video feed will not be saved. Default: \'\'.')
    outcome_options.add_argument('-dbb', '--draw-bb', dest='draw_bounding_boxes', type=bool, default=False,
                                help='Defines if bounding boxes of tracked objects need to be shown in video feed. Default: False.')
    # Replay Option
    replay_options = parser.add_argument_group('Replay options')
    replay_options.add_argument('-rf', '--replay_factor', dest='replay_factor', type=float, default=1.,
                                help='Replay factor. If greater than 1.0 we replay with slow-motion, otherwise this is a speed-up over real-time. Default: 1.0')

    args = parser.parse_args()

    if args.process_to and args.process_from > args.process_to:
        print(f'The processing time interval is not valid. [{args.process_from,}, {args.process_to}]')
        exit(1)

    if args.replay_factor < 0:
        print(f'The replay factor is not valid. [{args.replay_factor}]')
        exit(1)

    return args


def get_biases_from_file(path: str):
    """
    Helper function to read bias from a file. Return biases list with elements: 0 = value, 1 = name.
    """
    biases = {}
    try:
        biases_file = open(path, 'r')
    except IOError:
        print('Cannot open bias file: ' + path)
    else:
        for line in biases_file:
            # Skip lines starting with '%': comments
            if line.startswith('%'):
                continue

            split = line.split("%")
            biases[split[1].strip()] = int(split[0])
    return biases



def main():
    """
    Main
    """
    args = parse_args()
    inputs = Inputs(args)

    total_results = []
    measurement_index = 0

    # Events iterator on Camera or RAW file - CD PRODUCER
    mv_iterator = EventsIterator(input_path=inputs.input_path, start_ts=inputs.process_from,
                                 max_duration=inputs.process_to - inputs.process_from if inputs.process_to else None,
                                 delta_t=1e2)

    if is_live_camera(inputs.input_path): #EVK camera connected
        device = mv_iterator.reader.device
        #i_roi = device.get_i_roi()
        if os.path.isfile(inputs.bias_file):
                b = get_biases_from_file(inputs.bias_file)

                i_ll_biases = device.get_i_ll_biases()
                for bias_name, bias_value in b.items():
                    print(f'Applying {bias_name} = {bias_value}')
                    i_ll_biases.set(bias_name, bias_value)
    elif inputs.replay_factor > 0: #Using a RAW file
        mv_iterator = LiveReplayEventsIterator(mv_iterator, replay_factor=inputs.replay_factor)

    sensor_height, sensor_width = mv_iterator.get_size() # Sensor Geometry

    # Noise + Trail filter that will be applied to events
    activity_noise_filter = ActivityNoiseFilterAlgorithm(sensor_width, sensor_height, inputs.activity_time_ths)
    trail_filter = TrailFilterAlgorithm(sensor_width, sensor_height, inputs.activity_trail_ths)
    events_buf = ActivityNoiseFilterAlgorithm.get_empty_output_buffer()

    # Tracking Algorithm
    tracking_config = TrackingConfig()  # Default configuration
    tracking_algo = TrackingAlgorithm(sensor_width=sensor_width, sensor_height=sensor_height, tracking_config=tracking_config)
    tracking_algo.update_frequency = inputs.update_frequency
    tracking_algo.min_size = inputs.min_size
    tracking_algo.max_size = inputs.max_size

    # Event Frame Generator #acc_time = int(2.0e4 / inputs.update_frequency)
    events_frame_gen_algo = OnDemandFrameGenerationAlgorithm(sensor_width, sensor_height, inputs.accumulation_time)
    output_img = np.zeros((sensor_height, sensor_width, 3), np.uint8)

    # Window - Graphical User Interface (Display tracking results and process keyboard events)
    with MTWindow(title="Generic Tracking", width=sensor_width, height=sensor_height, mode=BaseWindow.RenderMode.BGR) as window:

        window.show_async(output_img)

        if inputs.out_video:
            fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
            video_name = inputs.out_video + ".avi"
            video_writer = cv2.VideoWriter(video_name, fourcc, 20, (sensor_width, sensor_height))

        # def keyboard_cb(key, scancode, action, mods):
        #     """
        #     Keyboard callback function that allows the use of shortcuts
        #     """
        #     SIZE_STEP = 2
        #
        #     if action != UIAction.RELEASE:
        #         return
        #     if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
        #         print('Program closing...')
        #         window.set_close_flag()
        #     # A: Increase minimum size of the object to track
        #     elif key == UIKeyEvent.KEY_A:
        #         if inputs.min_size + SIZE_STEP <= inputs.max_size:
        #             inputs.min_size += SIZE_STEP
        #             print("Increase min size to {}".format(inputs.min_size))
        #             tracking_algo.min_size = inputs.min_size
        #     # B: Decrease minimum size of the object to track
        #     elif key == UIKeyEvent.KEY_B:
        #         if inputs.min_size - SIZE_STEP >= 0:
        #             inputs.min_size -= SIZE_STEP
        #             print("Decrease min size to {}".format(inputs.min_size))
        #             tracking_algo.min_size = inputs.min_size
        #     # C: Increase maximum size of the object to track
        #     elif key == UIKeyEvent.KEY_C:
        #         inputs.max_size += SIZE_STEP
        #         print("Increase max size to {}".format(inputs.max_size))
        #         tracking_algo.max_size = inputs.max_size
        #     # D: Decrease maximum size of the object to track
        #     elif key == UIKeyEvent.KEY_D:
        #         if inputs.max_size - SIZE_STEP >= inputs.min_size:
        #             inputs.max_size -= SIZE_STEP
        #             print("Decrease max size to {}".format(inputs.max_size))
        #             tracking_algo.max_size = inputs.max_size
        #     # R: Start/stop recording of tracked objects
        #     elif key == UIKeyEvent.KEY_R:
        #         inputs.save_flag = not inputs.save_flag
        #         if inputs.save_flag:
        #             print('Started recording of events...')
        #         else:
        #             print('Stopped recording events.')
        #
        # window.set_keyboard_callback(keyboard_cb)
        #
        # print('--------------------------------------------------------------\n')
        # print('Press \'q\' or \'ESC\' to leave the program.\n'
        #         'Press \'a\' to increase the minimum size of the object to track.\n'
        #         'Press \'b\' to decrease the minimum size of the object to track.\n'
        #         'Press \'c\' to increase the maximum size of the object to track.\n'
        #         'Press \'d\' to decrease the maximum size of the object to track.\n'
        #         'Press \'r\' to start/stop recording information of tracked objects.\n')
        # print('--------------------------------------------------------------\n')

        # Output callback of the tracking algorithm Events Iterator
        def tracking_cb(ts, tracking_results):
            """
            Tracking callback that is triggered whenever an object is detected.
            """
            nonlocal output_img
            nonlocal total_results
            nonlocal measurement_index

            if measurement_index < inputs.no_runs:
                events_frame_gen_algo.generate(ts, output_img)
                if inputs.save_flag:
                    callback_results = tracking_results.numpy().tolist()  # Gets results as numpy.void type

                    if len(callback_results) > 0: # Only stores results if not empty IS THIS REALLY NECESSARY???
                        total_results.extend(callback_results)

                        current_time = callback_results[0][2]
                        start_time = inputs.measurement_time*measurement_index

                        if (current_time >= start_time + inputs.measurement_time):
                            # Save run
                            measurement_index += 1 # The first interval saved is interval 1
                            file_timestamp = str(datetime.datetime.now().strftime('%Y%m%d_%H-%M-%S'))
                            file_path = inputs.output_csv_path + file_timestamp + '.csv'

                            with open(file_path,'w') as new_file:
                                writer = csv.writer(new_file, delimiter=',', lineterminator='\n')
                                writer.writerows(total_results)

                            print(len(total_results))
                            print("Results saved at " + file_path)
                            new_file.close()
                            total_results = []
            else:
                sys.exit()

                    #         del file_timestamp
                    #         del  file_path
                    #         del total_results
                    #         total_results = []
                    #     del current_time
                    #     del start_time
                    # del callback_results

            if inputs.draw_bb:
                draw_tracking_results(ts, tracking_results, output_img)
            window.show_async(output_img)
            if inputs.out_video:
                video_writer.write(output_img)

        # Setting output callback to tracking algorithm (asynchronous)
        tracking_algo.set_output_callback(tracking_cb)
        # print(sys.getsizeof(events_buf))

        # Process events
        for evs in mv_iterator:
            # Dispatch system events to the window
            EventLoop.poll_and_dispatch()

            # Process events
            activity_noise_filter.process_events(evs, events_buf)
            trail_filter.process_events_(events_buf)
            events_frame_gen_algo.process_events(events_buf)
            tracking_algo.process_events(events_buf)

            # print("Length of Buffer " + len(events_buf))
            # del events_buf
            # events_buf = ActivityNoiseFilterAlgorithm.get_empty_output_buffer()
            if window.should_close():
                break

        if inputs.out_video:
            video_writer.release()
            print("Video has been saved in " + video_name)

if __name__ == "__main__":
        main()
