###############################################################################
#                                                                             #
#                                 mouse.py                                    #
#                                                                             #
# This program will take an mp4 file and save the coordinates of the mouse    #
# following a shark into a new file, which can then later be used to produce  #
# postage stamp jpegs of the shark, as well as non-shark postage stamp images #
#                                                                             #
# Pre-requisites for running this are:                                        #
#                                                                             #
# 1. Original mp4 file should be in format SHA-XXX-001.mp4                    #
#                                                                             #
# 2. A downsized version of the mp4 file must be created with dimensions      #
#    960x540. This is achieved through running something like the following   #
#    on the command line:                                                     #
#                                                                             #
#    avconv -i SHA-WHI-019.mp4 -s 960:540 SHA-WHI-019s.mp4                    #
#                                                                             #
# 3. Subsequent clips that are all based on the same original file can be run #
#    by creating symbolic links, eg:                                          #
#    ln -s SHA-XXX-001.mp4 SHA-XXX-002.mp4                                    #
#    ln -s SHA-XXX-001s.mp4 SHA-XXX-002s.mp4                                  #
#                                                                             #
# 4. Invoking this program is done on the command line. eg:                   #
#                                                                             #
#    mouse.py SHA-XXX-001 0 1 6 1 52 21                                       #
#                                                                             #
#    where 0 1 6 are the mins, secs, frames of the start of the clip and      #
#    0 52 21 are the mins, secs, frames of the end of the clip                #
#                                                                             #
# %. The output of this program is a binary file, created with "pickle" in    #
#    the "Arrays" directory. eg: Arrays/SHA-XXX-001.pick. This will be read   #
#    in by the following program, called "mouse2.py"                          #
#                                                                             #
#                                                                             #
#                                    Version 0.1   by Andrew Walsh  25NOV17   #
###############################################################################

import cv2
import numpy as np  
import sys, os, gc, random
import subprocess, pickle

#
# Initialise variables ix and iy, which are used to determine mouse position
#
ix,iy = -1,-1

#
# Initialise "output_stream", which writes out which frame we are currently
# viewing. Apparently, it won't show every single frame, ubt every 64th frame
# or thereabouts.
#
output_stream = sys.stdout

#
# Check to see if the required directories are there. If not, make them.
#
if not os.path.exists('pd01'):
    os.makedirs('pd01')
if not os.path.exists('pd02'):
    os.makedirs('pd02')
if not os.path.exists('Arrays'):
    os.makedirs('Arrays')

#
# Initialise input variables from the command line
#

FileNam = sys.argv[1]
StartMin = int(sys.argv[2])
StartSec = int(sys.argv[3])
StartFrame = int(sys.argv[4])
EndMin = int(sys.argv[5])
EndSec = int(sys.argv[6])
EndFrame = int(sys.argv[7])

#
# Initialise three lists which correspond to the pixel and frame coordinates
# for the mouse when tracking the shark
#
xpos = []
ypos = []
tpos = []

#
# Define global variables - not sure why
#

def draw_circle(event,x,y,flags,param):
    global ix,iy
    ix,iy = x,y


#
# Initialise the original-sized clip (SHA-XXX-001.mp4), so that we can start
# working on it. Note that we use a reduced version of the original clip
# (SHA-XXX-001s.mp4) with dimensions 960x540 elsewhere in this program. Also
# note that we have to separately specify sizeRatX and sizeRatY because some
# videos have slightly different aspect ratios (eg. 4096x2160).
#
# Determine clip frame rate (fps), height and width in pixels based on original
# clip size (capo).
#

capo = cv2.VideoCapture(FileNam+'.mp4')
fps = float(capo.get(cv2.cv.CV_CAP_PROP_FPS))
frameHeight = int(capo.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
frameWidth = int(capo.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
sizeRatX = frameWidth/960.
sizeRatY = frameHeight/540.
capo.release()

#
# Determine starting and ending frames from command line inputs
# Use them to also determine length of clip in term of the number of frames
#

sframe = int(((60*StartMin)+StartSec)*fps + StartFrame)
eframe = int(((60*EndMin)+EndSec)*fps + EndFrame)
length = eframe-sframe
print 'Start Frame =',sframe, 'End Frame=',eframe, 'Number of Frames=', length

#
# Initialise two windows. The first is 'clip', which is the main window,
# showing the full clip. The second is 'crop', which shows the effective
# 300x300 pixel zoom around the mouse position. This window shows the same
# FOV that will be saved as the postage stamp jpeg. The first frame is dislayed
# in 'clip'. A keystroke is required to start the video, once the mouse is
# positioned over the shark.
#
cap = cv2.VideoCapture(FileNam+'s.mp4')
cv2.namedWindow('clip',cv2.WINDOW_NORMAL)
cv2.resizeWindow('clip',1450,800)
cv2.namedWindow('crop',cv2.WINDOW_NORMAL)
cv2.resizeWindow('crop',450,450)
cap.set(1,sframe)
ret,frame = cap.read()
cv2.imshow('clip',frame)
cv2.waitKey(0)

#
# Loop over all 500 frames in the clip, show the frame and
# capture the mouse position in xpos, ypos and tpos, making sure that
# the mouse is no closer than 226 pixels from any edge
#
# NOTE: all videos have been downsampled by a factor of 4, so 3840:2160
# shrinks to 960:540. This allows the video to play quicker. All crop
# pixels have been changed accordingly: 226 -> 57 and 150 -> 38.
#
# values for ix and iy are also different, so they need to be appended
# to xpos and ypos with x4 bigger. 
#
for i in range(sframe,eframe):
    output_stream.write('Frame %s of %s\r' % (i-sframe, length))
    cap.set(1,i)
    ret,frame = cap.read()

    cv2.imshow('clip',frame)
    cv2.waitKey(5)
    cv2.setMouseCallback('clip',draw_circle)
    if ix>(225/sizeRatX) and iy>(225/sizeRatY) and ix<((frameWidth-225)/sizeRatX) and iy<((frameHeight-225)/sizeRatY):
        crop = frame[int(iy-(150/sizeRatY)):int(iy+(150/sizeRatY)), int(ix-(150/sizeRatX)):int(ix+(150/sizeRatX))]
        cv2.imshow('crop', crop)
        xpos.append(int(ix*sizeRatX))
        ypos.append(int(iy*sizeRatY))
        tpos.append(i)

    #
    # The gc.collect() step is required to clean up any leaking memory.
    # Otherwise the program can throw a core dump.
    #
    gc.collect()

#
# Release the video stream, close the clip and crop windows.
#
cap.release()
cv2.destroyAllWindows()

# Save lists of tpos, xpos, ypos into binary file in Arrays directory.
# This allows mouse positions to be recalled at a later date. Positions
# can be recalled with code such as:
#
#with open('Arrays/'+FileNam+'.pick','rb') as f:
#    ttpos = pickle.load(f)
#    xxpos = pickle.load(f)
#    yypos = pickle.load(f)
#
#print ttpos, xxpos, yypos
#

with open('Arrays/'+FileNam+'.pick','wb') as f:
    pickle.dump(tpos, f)
    pickle.dump(xpos, f)
    pickle.dump(ypos, f)

print '\nFinished!'
