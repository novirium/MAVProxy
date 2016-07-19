"""
sc_PiCam.py

This file includes functions to:
    initialise a web cam
    capture image from web cam

Image size is held in the smart_camera.cnf
"""

import sys
import time
import math
import cv2
import sc_config
from picamera import PiCamera
import os

class SmartCameraWebCam:

    def __init__(self, instance):

        # health
        self.healthy = False;

        # record instance
        self.instance = instance
        self.config_group = "camera%d" % self.instance

        # get image resolution
        self.img_width = sc_config.config.get_integer(self.config_group,'width',640)
        self.img_height = sc_config.config.get_integer(self.config_group,'height',480)
        self.img_output_folder = sc_config.config.get_string(self.config_group, 'image_output_folder', "~/smartcamcaptures/")

        if not os.path.isdir(self.img_output_folder):
            print "Configured output folder %s does not exist" % (self.img_output_folder)

        # background image processing variables
        self.img_counter = 0        # num images requested so far


        # Attempt to get pi camera
        self.camera = PiCamera()

        camera.resolution= (self.img_width,self.img_height)

        # check we can connect to camera
        #if not self.camera.isOpened():
        #    print "failed to open webcam %d" % self.instance

    # __str__ - print position vector as string
    def __str__(self):
        return "SmartCameraPiCam Object W:%d H:%d" % (self.img_width, self.img_height)

    # latest_image - returns ppath to latest image captured
    def get_latest_image(self):
        # write to file
        imgfilename = en_file_path(self.get_image_counter())
        return imgfilename

    # gen_file_path - returns file path given image number
    def gen_file_path(img_number):
        return os.path.join(self.img_output_folder, "img%d-%d.jpg" % (self.instance,img_number))

    # get_image_counter - returns number of images captured since startup
    def get_image_counter(self):
        return self.img_counter

    # take_picture - take a picture
    #   returns True on success
    def take_picture(self):
        # setup video capture
        print("Taking Picture")


        # TODO: find a way of verifying camera object
        # check we can connect to camera
        #if not self.camera.isOpened():
        #    self.healty = False
        #    return False

        # get an image from the webcam
        try:
            camera.capture(gen_file_path(self.img_counter+1))
        except:
            return False
        else:
            self.img_counter = self.img_counter+1
            return True


        # return failure
        return False

    # main - tests SmartCameraWebCam class
    def main(self):

        while True:
        #    # send request to image capture for image
        #    if self.take_picture():
        #        # display image
        #        cv2.imshow ('image_display', self.get_latest_image())
        #    else:
        #        print "no image"
#
#            # check for ESC key being pressed
#            k = cv2.waitKey(5) & 0xFF
#            if k == 27:
#                break
#
#            time.sleep(0.01)

# run test run from the command line
if __name__ == "__main__":
    sc_webcam0 = SmartCameraWebCam(0)
    sc_webcam0.main()
