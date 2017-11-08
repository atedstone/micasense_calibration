"""
Compute radiance-reflectance relationship for flight

Based on https://github.com/micasense/imageprocessing

Andrew Tedstone (a.j.tedstone@bristol.ac.uk), November 2017

"""

import cv2
import matplotlib.pyplot as plt
import numpy as np
import os, glob
import math
import pandas as pd
import datetime as dt

import sys
import configparser

import tkinter as tk
from tkinter import filedialog

import micasense.plotutils as plotutils
import micasense.metadata as metadata
import micasense.utils as msutils



# Check location of exiftool
exiftoolPath = None
if os.name == 'nt': # MS Windows
    exiftoolPath = 'C:/exiftool/exiftool.exe'


def radrefl_factor(panel_cal, image_name=None, plot_steps=False, cal_model=None,
		return_date=False):
	""" Compute radiance-reflectance factor for a RedEdge band from panel.

	Uses photo of calibrated reflectance panel acquired in band of interest to
	calculate a flight-specific radiance-reflectance factor which can be 
	applied to image collected while in flight.

	:param panel_cal: Panel reflectance factors for the panel used in the 
		image. (use load_panel_factors to open).
	:type panel_cal: pd.Series
	:param image_name: filepath to the image of the reflectance panel. If None
		you will be prompted to choose a file using a pop-up file dialog.
	:type image_name: str or None
	:param plot_steps: If True, plot panel image at every step of correction.
	:type plot_steps: bool
	:param cal_model_fn: filename of calibration model parameters for camera 
		(only for images acquired with RedEdge firmware < 2.1.0).
	:type cal_model_fn: str
	:param return_date: If True, return a datetime representation of image 
		acquisition date and time.
	:type return_date: bool

	:returns: radiance (, return_date)
	:rtype: float or tuple

	"""

	# Load file
	if image_name == None:
		# Ask for filename of refl image
		# https://stackoverflow.com/questions/9319317/quick-and-easy-file-dialog-in-python
		root = tk.Tk()
		root.withdraw()
		image_name = filedialog.askopenfilename()

	print(image_name)

	# Read raw image DN values
	# reads 16 bit tif - this will likely not work for 12 bit images
	imageRaw = plt.imread(image_name)

	# Display the image
	if plot_steps:
		fig, ax = plt.subplots(figsize=(8,6))
		ax.imshow(imageRaw, cmap='gray')
		plt.show()
		fig = plotutils.plotwithcolorbar(imageRaw, title='Raw image values with colorbar')

	# Load metadata
	meta = metadata.Metadata(image_name, exiftoolPath=exiftoolPath)
	cameraMake = meta.get_item('EXIF:Make')
	cameraModel = meta.get_item('EXIF:Model')
	bandName = meta.get_item('XMP:BandName')

	# Check firmware version
	firmwareVersion = meta.get_item('EXIF:Software')
	print('{0} {1} firmware version: {2}'.format(cameraMake, 
                                             cameraModel, 
                                             firmwareVersion))
	# Extract major [0], minor [1] and point [2] versions
	ver = [i for i in firmwareVersion[1:].split('.')]
	if int(ver[0]) < 2 and int(ver[1] < 1):
		if cal_model_fn == None:
			print('Firmware version < 2.1.0 and no calibration model data provided.')
			raise ValueError
	
	# Add calibration data to metadata if required.
	if cal_model != None:
		print('WARNING: Using user-provided calibration model data.')
		meta = add_cal_metadata(meta, cal_model_fn)
	else:
		print('Using in-camera calibration model data.')

	# Correct the image of refl panel
	radianceImage, L, V, R = msutils.raw_image_to_radiance(meta, imageRaw)
	if plot_steps:
		plotutils.plotwithcolorbar(V,'Vignette Factor')
		plotutils.plotwithcolorbar(R,'Row Gradient Factor')
		plotutils.plotwithcolorbar(V*R,'Combined Corrections')
		plotutils.plotwithcolorbar(L,'Vignette and row gradient corrected raw values')

	# Display the corrected refl panel image
	plotutils.plotwithcolorbar(radianceImage,'All factors applied and scaled to radiance')

	# Ask user to select rectangle points of refl panel area
	print('Click the top-left then bottom-right corners of the reflectance panel ...')
	points = plt.ginput(n=2, show_clicks=True)
	plt.close()

	# Mark points on image
	markedImg = radianceImage.copy()
	ulx = int(points[0][0]) # upper left column (x coordinate) of panel area
	uly = int(points[0][1]) # upper left row (y coordinate) of panel area
	lrx = int(points[1][0]) # lower right column (x coordinate) of panel area
	lry = int(points[1][1]) # lower right row (y coordinate) of panel area
	if plot_steps:
		# Plot rectangle on image
		cv2.rectangle(markedImg,(ulx,uly),(lrx,lry),(0,255,0),3)
		plotutils.plotwithcolorbar(markedImg, 'Panel region in radiance image')

	# Select panel region from radiance image
	panelRegion = radianceImage[uly:lry, ulx:lrx]
	meanRadiance = panelRegion.mean()
	print('Mean Radiance in panel region: {:1.3f} W/m^2/nm/sr'.format(meanRadiance))
	panelReflectance = panel_cal[bandName]
	radianceToReflectance = panelReflectance / meanRadiance
	print('Radiance to reflectance conversion factor: {:1.3f}'.format(radianceToReflectance))

	# Create reflectance image
	reflectanceImage = radianceImage * radianceToReflectance
	if plot_steps:
		plotutils.plotwithcolorbar(reflectanceImage, 'Converted Reflectance Image')

	# Blur the panel to check for trends - we want a consistent reflectance.
	panelRegionRefl = reflectanceImage[uly:lry, ulx:lrx]
	panelRegionReflBlur = cv2.GaussianBlur(panelRegionRefl,(55,55),5)
	plotutils.plotwithcolorbar(panelRegionReflBlur, 'Smoothed panel region in reflectance image')
	print('Min Reflectance in panel region: {:1.2f}'.format(panelRegionRefl.min()))
	print('Max Reflectance in panel region: {:1.2f}'.format(panelRegionRefl.max()))
	print('Mean Reflectance in panel region: {:1.2f}'.format(panelRegionRefl.mean()))
	print('Standard deviation in region: {:1.4f}'.format(panelRegionRefl.std()))

	if return_date:
		# Get time of image acquisition
		create_date = dt.datetime.strptime(meta.get_item('EXIF:CreateDate'), '%Y:%m:%d %H:%M:%S')
		return radianceToReflectance, create_date
	else:
		return radianceToReflectance



def load_panel_factors(panel_cal_fn):
	"""
	Load reflectance panel calibration data.

	Expects a CSV file with columns 'band' and 'factor', and rows named using 
	the RedEdge camera bands written into image metadata.

	:param panel_cal_fn: File path and name of CSV file to load.
	:type panel_cal_fn: str

	:returns: Series representing CSV file.
	:rtype: pd.Series
	"""

	panel_cal = pd.read_csv(panel_cal_fn, index_col='band').squeeze()
	panel_cal.name = panel_cal_fn
	return panel_cal



def add_cal_metadata(image_meta, camera_model_fn):
	""" Add Camera Radiometric Calibration Model to images without it.

	Adds relevant model parameters to the in-memory representation of an
	image's EXIF metadata, so that it can be used by micasense toolkit.

	:param image_meta: a metadata object to add parameters to.
	:type image_meta: metadata.Metadata
	:param camera_model_fn: filename of configuration file containing parameters
		which correspond to those for the camera which acquired the image.
	:type camera:model_fn: str

	:returns: metadata object with parameters added.
	:rtype: metadata.Metadata

	"""

	params = configparser.ConfigParser()
	params.read_file(open(camera_model_fn))

	for item in params.items('Model'):
		split_items = item[1].split(',') 
		if len(split_items) > 1:
			param = [float(i.strip()) for i in item]
		else:
			param = items[1]
		image_meta.exif[item[0]] = item[1]

	params = None
	return image_meta
