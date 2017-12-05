###############################################################################
#                                                                             #
#                               mouse2.py                                     #
#                                                                             #
# This program will take an mp4 file and a binary-encoded 'pickle' file with  #
# frame-by-frame coordinates to make jpeg postage stamp images of both the    #
# shark at the mouse and a random selection of 8 non-shark images. It will    #
# also rotate the shark image by a sucession of 45 degree turns to make 8     #
# shark images at various angles. Thus, there sohuld be an equal number of    #
# shark and non-shark images in the end.                                      #
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
#    mouse2.py SHA-XXX-001 0 1 6 1 52 21                                      #
#                                                                             #
#    where 0 1 6 are the mins, secs, frames of the start of the clip and      #
#    0 52 21 are the mins, secs, frames of the end of the clip                #
#                                                                             #
# 5. The outputs of this program are jpeg images. Shark images will be saved  #
#    to the directory pd01/ and non-shark images will be saved to the         #
#    directory pd02/.                                                         #
#                                                                             #
#                                                                             #
#                                    Version 0.1   by Andrew Walsh  25NOV17   #
###############################################################################

import cv2
import numpy as np  
import sys, os, gc, random
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
#fps = float(cap.get(cv2.cv.CV_CAP_PROP_FPS))
fps = 24.8574
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

#
# Define negax etc. These variables are the number of full 300-pixel regions
# before and after the shark region. These regions are used to create images
# that do not contain sharks.
#
for i in range(len(xpos)):
    output_stream.write('Frame %s of %s\r' % (i, len(xpos)))
    negax = -int((xpos[i]-150)/300)
    negbx = int((frameWidth-150-xpos[i])/300)
    negay = -int((ypos[i]-150)/300)
    negby = int((frameHeight-150-ypos[i])/300)
    cap.set(1,tpos[i])
    ret,frame = cap.read()
    #
    # First extract all the on-shark images. Also rotate them through 45
    # degree increments to increase the dataset size by a factor of 8,
    # which also alleviates the problem of sharks always travelling up.
    # Need to use a larger crop for this so that the corners are not cut
    # off.
    #
    crop2 = frame[ypos[i]-(exppos[i]/2):ypos[i]+(exppos[i]/2), xpos[i]-(exppos[i]/2):xpos[i]+(exppos[i]/2)]
    resized_image2 = cv2.resize(crop2, (300,300))
    cv2.imwrite('pd01/'+FileNam+'-'+str(tpos[i])+'-'+str(xpos[i])+'-'+str(ypos[i])+'.jpg', resized_image2)

    crop = frame[ypos[i]-(3*exppos[i]/4):ypos[i]+(3*exppos[i]/4), xpos[i]-(3*exppos[i]/4):xpos[i]+(3*exppos[i]/4)]
    for p in range(45,360,45):
        M = cv2.getRotationMatrix2D((3*exppos[i]/4,3*exppos[i]/4),p,1)
        dst = cv2.warpAffine(crop,M,(3*exppos[i]/2,3*exppos[i]/2))
        resized_image = cv2.resize(dst, (450,450))
        dstsub = resized_image[75:375, 75:375]
        cv2.imwrite('pd01/'+FileNam+'-'+str(tpos[i])+'-'+str(xpos[i])+'-'+str(ypos[i])+'-'+str(p)+'.jpg', dstsub)

    #
    # Create an array (combarr) which has all the off-shark positions
    # (excludes (0,0)). Randomly take 8 positions and save them as
    # off-shark images in pd02. This ensures that both on-shark and
    # off-shark datasets have the same number of images: 8 per frame.
    #
    combarr = []
    for t in range(negax,negbx+1):
        for u in range(negay,negby+1):
            if abs(t)+abs(u)>2:
                combarr.append([t,u])
            elif sizeRatX<3 and abs(t)+abs(u)>0:
                combarr.append([t,u])
    random.shuffle(combarr)
    for q in range(8):
        crop2 = frame[ypos[i]-150+(300*combarr[q][1]):ypos[i]+150+(300*combarr[q][1]), xpos[i]-150+(300*combarr[q][0]):xpos[i]+150+(300*combarr[q][0])]
        cv2.imwrite('pd02/'+FileNam+'-'+str(tpos[i])+'-'+str(xpos[i]+(300*combarr[q][0]))+'-'+str(ypos[i]+(300*combarr[q][1]))+'.jpg', crop2)

cap.release()
cv2.destroyAllWindows()

print '\nFinished!'
