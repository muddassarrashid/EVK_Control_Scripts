"""
This python script will run the Heat Engine cycle.

------------------
THE ALGORITHM
------------------
0. User Checks: Prompts to remind the user to make sure that
(a) calibration using the EVENT Camera has been done
(b) a REFERENCE save has been taken
(c) the picoscope is setup to save the necessary filenames
(d) the Work function is setup
(e) the bath is Setup

1. Check Connections to Instruments: The script begins by doing preliminary checks such as:
-- Is connection to the Signal generator open, this Siggen will pulse all rest of the instruments.
-- Is the event camera connected and ready?

2. Setup Parameters and Saving folder files
-- Set up the HE Parameters, each run should save them automatically into a csv file
-- Set up the saving folders and filenames for saving each run of the tracked trajectories.
-- the event camera parameters and biases
-- the event camera

3. Data Taking
(a) Send trigger ON to Siggen, this should trigger to all other siggens and picoscope to save the applied work function
(b) begin recording
(c) save trajectory data for given run paramaters
(d) check if desired trajectory run number reached
(e) Loop begins again


"""

# import devices
import pyvisa
import devices
import os
import sys
import fcntl
from time import sleep
import psutil
from pynput.keyboard import Key, Controller
# from subprocess import Popen, PIPE, run
import subprocess
from metavision_core.event_io import EventsIterator, LiveReplayEventsIterator, is_live_camera
from metavision_sdk_analytics import TrackingAlgorithm, TrackingConfig
from metavision_sdk_core import OnDemandFrameGenerationAlgorithm
from metavision_sdk_cv import ActivityNoiseFilterAlgorithm, TrailFilterAlgorithm
from metavision_sdk_ui import EventLoop

# savingLocation = "/home/levitech/millen2/MacroTrap/DATA/20220720/HE_ramping_plus_noise_1.0V/signal/"
savingLocation = "/home/levitech/millen2/ElectroMech/Data/20221219/Optimize_Biases/signal/"
biasFileLocation = "/home/levitech/millen2/ElectroMech/Data/20221219/out.bias"
duration = 12
NFiles = 1
uf = 1000
bmax = 220
bmin = 0

EVKcommand_novid  = "python3 evk_tracking_wo_video.py " + " -bf " + biasFileLocation + " -csv " + savingLocation + " -csvt " + str(duration) + " -csvn " + str(NFiles) + " -uf " + str(uf) + " -mins " + str(bmin) + " -maxs " + str(bmax)

EVKcommand_vid = "python3 evk_tracking_video.py -dbb True " + " -mins " + str(bmin) + " -maxs " + str(bmax) + " -bf " + biasFileLocation + " -csv " + savingLocation + " -csvt " + str(duration) + " -csvn " + str(NFiles) + " -uf " + str(uf)

# def ChangeEVKBias(biasFile, SearchBias, newValue):
#         tempFile = open( biasFile, 'r+' )
#         for line in fileinput.input( fileToSearch ):
#             if SearchBias in line :
#                 print('Match Found')
#             else:
#                 print('Match Not Found!!')
#             tempFile.write( line.replace( SearchBias, textToReplace ) )
#         tempFile.close()

EVKMetaCommand = "metavision_player"

PORT = 'ASRL/dev/ttyUSB2::INSTR'
ds335 = devices.ds335(PORT)

k = 0;
print('Run Begun')
ds335.sendCmd('OFFS 0')

while k<2:
    k += 1
    print('Run No: ' + str(k-1))
    ds335.sendCmd('OFFS 2')
    try:
        process = subprocess.run(EVKcommand_vid, shell = True, check=True, stdout = subprocess.PIPE)
        print(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total)
    except subprocess.CalledProcessError:
        sleep(5)
        print("EBC script was killed... restarting metavision...")
        p = subprocess.Popen("exec " + EVKMetaCommand, stdin=subprocess.PIPE, shell=True)
        sleep(5)
        keyboard = Controller()
        key = "q"
        keyboard.press(key)
        keyboard.release(key)
        p.kill()

        p = subprocess.Popen("exec " + EVKMetaCommand, stdin=subprocess.PIPE, shell=True)
        sleep(5)
        keyboard = Controller()
        key = "q"
        keyboard.press(key)
        keyboard.release(key)
        p.kill()

        print("reset done using metavision_player")
    except:
        print("Something else went wrong")

    sleep(5)


    ds335.sendCmd('OFFS 0')
    # print('Offset Value: ' + str(ds335.getStatus()))

ds335.sendCmd('OFFS 0')
