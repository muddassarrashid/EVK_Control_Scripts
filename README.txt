1) Use metavision_player to check the particle

2) Use metavision_player --show-biases to dinamically tune the sensor parameters (aka biases) and observe their effect.
- Increasing diff_on reduces sensitivity to positive events.
- Reducing diff_off reduces sensitivity to negative events.
Last time we carried out telegraph noise, the default biases were used except for diff_on, which was increased.

3) With metavision_player --show-biases, pressing b in the keyboard saves the biases values into a file (.bias), under Documents/Prophesee.

4) Use python3 evk_tracking_video.py -dbb True -bf [.bias path] will show the video feed of the tracking algorithm with the corresponding bounding boxes, using the saved biases.
This can be used to modify the maximum and minimum size of particles (-mins and -maxs, in pixels), or quickly identify any other weird behaviour. This eventually ends up consuming
the RAM, so I do not use it for long runs, but can be used for shorter runs since it stores the .csv files.

5) Use python3 evk_tracking_wo_video.py -bf [.bias path] to track the particle and save the resulting .csv files. No video feed is shown. This function is used for calibration, where a
continuous long run is measured while modifying the voltages (voltage values are modified every ~30s).

6) Other comments:

	- By reducing the sensitivity to positive events, the update frequency AND the accumulation time, the position distributions obtained with telegraph noise improved;
	but missing time stamps caused changes in particle ID, leading to the peaks observed for larger taus
	- Missing timestamps occurr when no object is detected in the given time interval defined by the accumulation time, so:
		> Increasing the accumulation time might solve this problem, but a high accumulation time leads to an incorrect tracking due to the trail of negative events
		> Increasing the sensitvity to positive events (which could be just using default biases) and using 1000Hz update frequency and low accumulation time may solve
		the problem, since a higher number of events should be detected
		> Increasing the update frequency originally led to larger response times
	- The filter parameters of the algorithm could also be tuned if necessary, which would result in solving the problem (haven't tried them).
	- The default time interval saved in the .csv is 60s, this can be modified with -csvt input
	- The accumulation time is passed as an input -at in seconds. The value previously used was 0.00002s (quite small)
	- The update frequency can also be passed as an input -uf, although the default value (1000Hz) was previously used.
	- The tracking algorithm cannot be used with the live feed if metavision_player is being used


7) The columns of each -csv file have (from left to right):
	Column 1: floor value of the x coordinate (pixels)
	Column 2: floor value of the y coordinate (pixels)
	Column 3: timestamp (us)
	Column 4: x coordinate (pixels)
	Column 5: y coordinate (pixels)
	Column 6: bounding box width (pixels)
	Column 7: bounding box height (pixels)
	Column 8: object ID
	Column 9: event ID
