"""
sc_PiCam.py

This file includes functions to:
	initialise a raspberry pi camera
	capture image from pi camera

Image size is held in the smart_camera.cnf

Based on the existing sc_webcam.py
"""

import sys
import time
import math
import sc_config
from picamera import PiCamera
import os

class SmartCameraPiCam:

	def __init__(self, instance):

		# health
		#self.healthy = False;

		# record instance
		self.instance = instance
		self.config_group = "camera%d" % self.instance

		# get settings
		self.img_width = sc_config.config.get_integer(self.config_group,'width',640)
		self.img_height = sc_config.config.get_integer(self.config_group,'height',480)
		self.img_output_folder = os.path.expanduser(sc_config.config.get_string(self.config_group, 'image_output_folder', time.strftime("~/smartcamcaptures/%y%m%d_%H%M%S/")))
		self.makesymlink = sc_config.config.get_boolean(self.config_group,"make_symlink", True)


		self.camISO = sc_config.config.get_integer(self.config_group,'iso',0)
		self.camShutterSpeed = sc_config.config.get_integer(self.config_group,'shutter_speed',0)
		self.attitideFilename = sc_config.config.get_boolean(self.config_group,'attitude_in_filename',False)

		self.vehicleLat = 0.0			  # Current Vehicle Latitude
		self.vehicleLon = 0.0			  # Current Vehicle Longitude
		self.vehicleHdg = 0.0			  # Current Vehicle Heading
		self.vehicleAMSL = 0.0			 # Current Vehicle Altitude above mean sea level

		self.vehicleVx = 0.0
		self.vehicleVy = 0.0
		self.vehicleVz = 0.0

		self.vehicleRoll = 0.0			  # Current Vehicle Roll
		self.vehiclePitch = 0.0			  # Current Vehicle Pitch


		# Check for output path
		if not os.path.isdir(self.img_output_folder):
			print "Configured output folder %s does not exist" % (self.img_output_folder)
			print "Creating output folder %s" % (self.img_output_folder)
			os.makedirs(self.img_output_folder)

		if self.makesymlink:
			self.linkname=os.path.join(os.path.dirname(self.img_output_folder),"/latest")
			os.symlink(self.img_output_folder,self.linkname)
			print "Linked %s to %s" % (self.linkname,self.img_output_folder)

		# background image processing variables
		self.img_counter = 0		# num images requested so far


		# Attempt to get pi camera
		self.camera = PiCamera()

		self.camera.resolution= (self.img_width,self.img_height)
		self.camera.iso = self.camISO
		self.camera.shutter_speed = self.camShutterSpeed

		# check we can connect to camera
		#if not self.camera.isOpened():
		#	print "failed to open webcam %d" % self.instance

	# __str__ - print position vector as string
	def __str__(self):
		return "SmartCameraPiCam Object W:%d H:%d" % (self.img_width, self.img_height)

	def boSet_GPS(self, mGPSMessage):
		if mGPSMessage.get_type() == 'GLOBAL_POSITION_INT':
			(self.vehicleLat, self.vehicleLon, self.vehicleHdg, self.vehicleAMSL, self.vehicleVx, self.vehicleVy) = (mGPSMessage.lat*1.0e-7, mGPSMessage.lon*1.0e-7, mGPSMessage.hdg*0.01, mGPSMessage.alt*0.001, mGPSMessage.vx*0.01, mGPSMessage.vy*0.01)

	def boSet_Attitude(self, mAttitudeMessage):
		if mAttitudeMessage.get_type() == 'ATTITUDE':
			(self.vehicleRoll, self.vehiclePitch) = (math.degrees(mAttitudeMessage.roll), math.degrees(mAttitudeMessage.pitch))

	def boSetISO(self, u16ISO):
		if u16ISO == 1:
			#Set to auto (mavlink specifies that 0 value is ignored)
			self.camera.iso=0
		else :
			self.camera.iso=u16ISO

	def boSetShutterSpeed(self,u16ShutterSpeed):
		if u16ShutterSpeed == 1:
			#Set to auto (mavlink specifies that 0 value is ignored)
			self.camera.shutter_speed=0
		else:
			#PiCam expects shutter speed in microseconds
			self.camera.shutter_speed=int(1000000/u16ShutterSpeed)

	# latest_image - returns ppath to latest image captured
	def get_latest_image(self):
		# write to file
		imgfilename = en_file_path(self.get_image_counter())
		return imgfilename

	# gen_file_path - returns file path given image number
	def gen_file_path(self, img_number):
		#return os.path.join(self.img_output_folder, "img%d-%d.jpg" % (self.instance,img_number))
		if (self.attitideFilename):
			return os.path.join(self.img_output_folder, "img%d-%d_%d_%d.jpg" % (self.instance,img_number,int(100*self.vehicleRoll),int(100*self.vehiclePitch)))
		else:
			return os.path.join(self.img_output_folder, "img%d-%d.jpg" % (self.instance,img_number))

	# get_image_counter - returns number of images captured since startup
	def get_image_counter(self):
		return self.img_counter

	# take_picture - take a picture
	#   returns True on success
	def take_picture(self):
		# setup video capture



		#TODO: find a way of verifying camera object

		# Insert EXIF GPS tags
		self.camera.exif_tags['GPS.GPSAltitudeRef'] = '0'
		self.camera.exif_tags['GPS.GPSAltitude'] = '%d/100' % int(100 * self.vehicleAMSL)

		hspeed= math.hypot(self.vehicleVx, self.vehicleVy)
		self.camera.exif_tags['GPS.GPSSpeedRef'] = 'K'
		self.camera.exif_tags['GPS.GPSSpeed'] = '%d/1000' % int(3600 * hspeed)

		self.camera.exif_tags['GPS.GPSLatitudeRef'] = 'N' if self.vehicleLat > 0 else 'S'
		alat = math.fabs(self.vehicleLat)
		dlat = int(alat)
		mlat = int(60 * (alat - dlat))
		slat = int(60000 * (60 * (alat - dlat) - mlat))
		self.camera.exif_tags['GPS.GPSLatitude'] = '%d/1,%d/1,%d/1000' % (dlat, mlat, slat)

		self.camera.exif_tags['GPS.GPSLongitudeRef'] = 'E' if self.vehicleLon > 0 else 'W'
		alon = math.fabs(self.vehicleLon)
		dlon = int(alon)
		mlon = int(60 * (alon - dlon))
		slon = int(60000 * (60 * (alon - dlon) - mlon))
		self.camera.exif_tags['GPS.GPSLongitude'] = '%d/1,%d/1,%d/1000' % (dlon, mlon, slon)

		self.camera.exif_tags['GPS.GPSImgDirection'] = '%d/100' % int(100 * self.vehicleHdg)

		#Generate new image path
		imagepath=self.gen_file_path(self.img_counter+1)
		print("Capturing image to: %s" % (imagepath))

		#Attempt to capture image
		try:
			self.camera.capture(imagepath)
		except:
			import traceback
			print(traceback.format_exc())
			print("Couldn't take picture. Attempted path: %s" % (imagepath))
			return False
		else:
			self.img_counter = self.img_counter+1
			return True


		# return failure
		return False

	# main - tests SmartCameraWebCam class
	def main(self):
		while true:
		#	# send request to image capture for image
		#	if self.take_picture():
		#		# display image
		#		cv2.imshow ('image_display', self.get_latest_image())
		#	else:
		#		print "no image"
			# check for ESC key being pressed
			k = cv2.waitKey(5) & 0xFF
			if k == 27:
				break

			time.sleep(0.01)

# run test run from the command line
if __name__ == "__main__":
	sc_picam0 = SmartCameraPiCam(0)
	sc_picam0.main()
