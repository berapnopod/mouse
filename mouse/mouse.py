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
# Initialise four lists which correspond to the pixel and frame coordinates
# for the mouse when tracking the shark, plus the expand factor used to
# try and mimic the drone always being at 60 metres.
#
xpos = []
ypos = []
tpos = []
exppos = []

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
# clip size (capo). Sometimes, opencv cannot read the fps and so this has to be
# hard-coded in.
#

capo = cv2.VideoCapture(FileNam+'.mp4')
#fps = float(capo.get(cv2.cv.CV_CAP_PROP_FPS))
fps =24.8574
frameHeight = int(capo.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
frameWidth = int(capo.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
sizeRatX = frameWidth/960.
sizeRatY = frameHeight/540.
print fps, frameHeight, frameWidth
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
# Initialise a window: 'clip', showing the full clip. A square is drawn around
# the mouse cursor position which is equivalent to the size of the 300x300
# pixel jpeg created at the end. There is also a black and white scale bar,
# which is equivalent to 2 metres, when the drone is flown at 60 metres.
# The first frame is dislayed in 'clip'. A keystroke is required to start the
# video, once the mouse is positioned over the shark.
#
cap = cv2.VideoCapture(FileNam+'s.mp4')
cv2.namedWindow('clip',cv2.WINDOW_NORMAL)
cv2.resizeWindow('clip',1450,800)
cap.set(1,sframe)
ret,frame = cap.read()
cv2.imshow('clip',frame)
cv2.waitKey(0)

#
# Loop over dwall 500 frames in the clip, show the frame and
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
# Also intialise expandFac to 300, so the first square drawn is 300x300 pixels.
# The size of the box can be changed by hitting any number key.
# If key "3" is hit, then the box will reamin at 300x300 pixels. If "4" is hit,
# the box will increase to 400x400 pixels. This is the case for all numbers up
# to and including "9" - ie. 900x900 pixels. If you press "0", the box
# increases to 1200x1200 pixels, which is the a zoom factor of 4, equivalent to
# the drone flying at 15 metres.
#

expandFac = 300

for i in range(sframe,eframe):
    output_stream.write('Frame %s of %s\r' % (i-sframe, length))
    cap.set(1,i)
    ret,frame = cap.read()

    cv2.setMouseCallback('clip',draw_circle)
    while True:
        k = cv2.waitKey(5)
        if k ==-1:
            break
        elif k == 48:
            expandFac = 1200
        else:
            expandFac = 100*int(chr(k))
    if ix>(0.75*expandFac/sizeRatX) and iy>(0.75*expandFac/sizeRatY) and ix<((frameWidth-0.75*expandFac)/sizeRatX) and iy<((frameHeight-0.75*expandFac)/sizeRatY):
        cv2.rectangle(frame, (int(ix-(0.5*expandFac/sizeRatX)),int(iy-(0.5*expandFac/sizeRatY))),(int(ix+(0.5*expandFac/sizeRatX)),int(iy+(0.5*expandFac/sizeRatY))),(0,255,0),2)
        cv2.line(frame, (int(ix+(0.5*expandFac/sizeRatX-10)),int(iy-(0.15*expandFac/sizeRatY))), (int(ix+(0.5*expandFac/sizeRatX-10)),int(iy-(0.15*expandFac/sizeRatY)+(0.2327*expandFac/sizeRatY))),(0,0,0),2)
        cv2.line(frame, (int(ix+(0.5*expandFac/sizeRatX-10)),int(iy-(0.15*expandFac/sizeRatY))), (int(ix+(0.5*expandFac/sizeRatX-10)),int(iy-(0.15*expandFac/sizeRatY)+(0.2327*expandFac/sizeRatY))),(255,255,255),1)
        xpos.append(int(ix*sizeRatX))
        ypos.append(int(iy*sizeRatY))
        tpos.append(i)
        exppos.append(expandFac)
    cv2.imshow('clip',frame)
    cv2.waitKey(5)

    #
    # The gc.collect() step is required to clean up any leaking memory.
    # Otherwise the program can throw a core dump.
    #
    gc.collect()

#
# Release the video stream, close the clip window.
#
cap.release()
cv2.destroyAllWindows()

# Save lists of tpos, xpos, ypos, exppos into binary file in Arrays directory.
# This allows mouse positions to be recalled at a later date. Positions
# can be recalled with code such as:
#
#with open('Arrays/'+FileNam+'.pick','rb') as f:
#    tpos = pickle.load(f)
#    xpos = pickle.load(f)
#    ypos = pickle.load(f)
#    exppos = pickle.load(f)
#
#print ttpos, xxpos, yypos
#

with open('Arrays/'+FileNam+'.pick','wb') as f:
    pickle.dump(tpos, f)
    pickle.dump(xpos, f)
    pickle.dump(ypos, f)
    pickle.dump(exppos, f)

print '\nFinished!'
