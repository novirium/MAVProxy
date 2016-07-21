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

class SmartCamerPiCam:

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

        self.vehicleLat = 0.0              # Current Vehicle Latitude
        self.vehicleLon = 0.0              # Current Vehicle Longitude
        self.vehicleHdg = 0.0              # Current Vehicle Heading
        self.vehicleAMSL = 0.0             # Current Vehicle Altitude above mean sea level

        self.vehicleVx = 0.0
        self.vehicleVy = 0.0
        self.vehicleVz = 0.0

        self.vehicleRoll = 0.0              # Current Vehicle Roll
        self.vehiclePitch = 0.0              # Current Vehicle Pitch


        if not os.path.isdir(self.img_output_folder):
            print "Configured output folder %s does not exist" % (self.img_output_folder)

        # background image processing variables
        self.img_counter = 0        # num images requested so far


        # Attempt to get pi camera
        self.camera = PiCamera()

        self.camera.resolution= (self.img_width,self.img_height)

        # check we can connect to camera
        #if not self.camera.isOpened():
        #    print "failed to open webcam %d" % self.instance

    # __str__ - print position vector as string
    def __str__(self):
        return "SmartCameraPiCam Object W:%d H:%d" % (self.img_width, self.img_height)

    def boSet_GPS(self, mGPSMessage):
        if mGPSMessage.get_type() == 'GLOBAL_POSITION_INT':
            (self.vehicleLat, self.vehicleLon, self.vehicleHdg, self.vehicleAMSL, self.vehicleVx, self.vehicleVy) = (mGPSMessage.lat*1.0e-7, mGPSMessage.lon*1.0e-7, mGPSMessage.hdg*0.01, mGPSMessage.alt*0.001, mGPSMessage.vx*0.01, mGPSMessage.vy*0.01)

    def boSet_Attitude(self, mAttitudeMessage):
        if mAttitudeMessage.get_type() == 'ATTITUDE':
            (self.vehicleRoll, self.vehiclePitch) = (math.degrees(mAttitudeMessage.roll), math.degrees(mAttitudeMessage.pitch))

    # latest_image - returns ppath to latest image captured
    def get_latest_image(self):
        # write to file
        imgfilename = en_file_path(self.get_image_counter())
        return imgfilename

    # gen_file_path - returns file path given image number
    def gen_file_path(img_number):
        #return os.path.join(self.img_output_folder, "img%d-%d.jpg" % (self.instance,img_number))
        return os.path.join(self.img_output_folder, "img%d-%d_%d-%d.jpg" % (self.instance,img_number,int(100*self.vehicleRoll),int(100*self.vehiclePitch)))

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

        ## Set picture date and time to GPS values.
		#	now = parser.parse(report.get('time', datetime.now().isoformat()))
		#	print now.strftime('%s')
		#	cam.exif_tags['EXIF.DateTimeOriginal'] = now.strftime('%Y:%m:%d %H:%M:%S')

		#	# Set altitude to GPS value.
		#	alt = report.get('alt', 0.0)
		#	print alt
		self.camera.exif_tags['GPS.GPSAltitudeRef'] = '0'
		self.camera.exif_tags['GPS.GPSAltitude'] = '%d/100' % int(100 * self.vehicleAMSL)

		#	# Convert speed from m/s to km/h and set tag.
		#	speed = report.get('speed', 0.0)
		#	print speed
        hspeed= math.hypot(self.vehicleVx, self.vehicleVy)
		self.camera.exif_tags['GPS.GPSSpeedRef'] = 'K'
		self.camera.exif_tags['GPS.GPSSpeed'] = '%d/1000' % int(3600 * hspeed)

		#	# Set direction of motion and direction along which the picture is taken (assuming frontal view).
		#	track = report.get('track', 0.0)
		#	print track
		#	cam.exif_tags['GPS.GPSTrackRef'] = 'T'
		#	cam.exif_tags['GPS.GPSTrack'] = '%d/10' % int(10 * track)
		#	cam.exif_tags['GPS.GPSImgDirectionRef'] = 'T'
		#	cam.exif_tags['GPS.GPSImgDirection'] = '%d/10' % int(10 * track)

		#	# Set GPS latitude.
		#	lat = report.get('lat', 0.0)
		#	print lat
		self.camera.exif_tags['GPS.GPSLatitudeRef'] = 'N' if self.vehicleLat > 0 else 'S'
		alat = math.fabs(self.vehicleLat)
		dlat = int(alat)
		mlat = int(60 * (alat - dlat))
		slat = int(6000 * (60 * (alat - dlat) - mlat))
		self.camera.exif_tags['GPS.GPSLatitude'] = '%d/1,%d/1,%d/100' % (dlat, mlat, slat)

		#	# Set GPS longitude.
		#	lon = report.get('lon', 0.0)
		#	print lon
		self.camera.exif_tags['GPS.GPSLongitudeRef'] = 'E' if self.vehicleLon > 0 else 'W'
		alon = math.fabs(self.vehicleLon)
		dlon = int(alon)
		mlon = int(60 * (alon - dlon))
		slon = int(6000 * (60 * (alon - dlon) - mlon))
		self.camera.exif_tags['GPS.GPSLongitude'] = '%d/1,%d/1,%d/100' % (dlon, mlon, slon)

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
