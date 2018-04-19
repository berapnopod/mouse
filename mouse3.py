###############################################################################
#                                                                             #
#                               mouse3.py                                     #
#                                                                             #
# This program will take an mp4 file and a binary-encoded 'pickle' file with  #
# frame-by-frame coordinates to make full jpeg images of the                  #
# field of view, plus a csv file containing bounding boxes on sharks in the   #
# jpeg image.
#                                                                             #
# Pre-requisites for running this are:                                        #
#                                                                             #
# 1. Original mp4 file should be in format SHA-XXX-001.mp4                    #
#                                                                             #
# 2. Binary-encoded pickle file should be in Arrays directory as              #
#    Arrays/SHA-XXX-001.pick                                                  #
#                                                                             #
# 4. Invoking this program is done on the command line. eg:                   #
#                                                                             #
#    mouse3.py SHA-XXX-001 0 1 6 1 52 21                                      #
#                                                                             #
#    where 0 1 6 are the mins, secs, frames of the start of the clip and      #
#    0 52 21 are the mins, secs, frames of the end of the clip                #
#                                                                             #
# 5. The outputs of this program are jpeg images and a csv file. Images are   #
#    saved in the pd01/ directory and csv file in the wordking directory      #
#                                                                             #
#                                                                             #
#                                    Version 0.1   by Andrew Walsh  19APR18   #
###############################################################################

import cv2
import csv
import numpy as np  
import sys, os, gc, random, commands, math
import subprocess, pickle

output_stream = sys.stdout

#
# Initialise input variables on the command line
#

FileNam = sys.argv[1]
StartMin = int(sys.argv[2])
StartSec = int(sys.argv[3])
StartFrame = int(sys.argv[4])
EndMin = int(sys.argv[5])
EndSec = int(sys.argv[6])
EndFrame = int(sys.argv[7])

#
# Read in four lists which correspond to the pixel and frame coordinates
# for the mouse when tracking the shark, plus the expand factor.
#
with open('Arrays/'+FileNam+'.pick','rb') as f:
    tpos = pickle.load(f)
    xpos = pickle.load(f)
    ypos = pickle.load(f)
    exppos = pickle.load(f)

#
# Initialise the clip, then read in the clip frames rate (fps), frame height
# and width. sizeRatX is the ratio of the width of the original clip to the
# smaller clip (SHA-XXX-001s.mp4) used in mouse.py. It is used to determine
# if there should be a buffer of one region for negative images or not.
#
# Sometimes the fps needs to be hard-coded in because opencv cannot read it for
# all mp4 files.
#

cap = cv2.VideoCapture(FileNam+'.mp4')
ret,frame = cap.read()
fps = float(cap.get(cv2.cv.CV_CAP_PROP_FPS))
if math.isnan(fps):
    cmd = "exiftool %s | grep 'Video Frame Rate' | awk '{print $5}'" % (FileNam+'.mp4')
    status, fps = commands.getstatusoutput(cmd)
    try:
        fps = float(fps)
    except Exception:
        fps = 25.0
frameHeight = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
frameWidth = int(cap.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
sizeRatX = frameWidth/960

#
# Determine starting and ending frames from command line inputs
# Use them to also determine length of clip in number of frames
#
sframe = int(((60*StartMin)+StartSec)*fps + StartFrame)
eframe = int(((60*EndMin)+EndSec)*fps + EndFrame)
length = eframe-sframe
print 'Start Frame =',sframe, 'End Frame=',eframe, 'Number of Frames=', length

with open('CSV/'+FileNam+'.csv', "wb") as csv_file:
    writer = csv.writer(csv_file, delimiter=',')
    #
    # Define negax etc. These variables are the number of full 300-pixel regions
    # before and after the shark region. These regions are used to create images
    # that do not contain sharks.
    #
    for i in range(len(xpos)):
        output_stream.write('Frame %s of %s\r' % (i, len(xpos)))
        tlcx = int(xpos[i]-(exppos[i]/2))
        tlcy = int(ypos[i]-(exppos[i]/2))
        brcx = int(xpos[i]+(exppos[i]/2))
        brcy = int(ypos[i]+(exppos[i]/2))
    
        cap.set(1,tpos[i])
        ret,frame = cap.read()
        #
        # First extract all the on-shark images. Also rotate them through 45
        # degree increments to increase the dataset size by a factor of 8,
        # which also alleviates the problem of sharks always travelling up.
        # Need to use a larger crop for this so that the corners are not cut
        # off.
        #
        cv2.imwrite('pd01/'+FileNam+'-'+str(tpos[i])+'.jpg', frame)
        #crop2 = frame[tlcy:brcy, tlcx:brcx]
        #cv2.imwrite('pd02/'+FileNam+'-'+str(tpos[i])+'.jpg', crop2)
        writer.writerow([FileNam+'-'+str(tpos[i])+'.jpg',tlcx,tlcy,brcx,brcy,FileNam[4:7]])
    
cap.release()
cv2.destroyAllWindows()

print '\nFinished!'
