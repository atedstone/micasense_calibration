#! /usr/bin/env python
"""
Driver script for a flight bounded by reflectance panels pre- and post-flight.
"""

import statsmodels.api as sm
import matplotlib.pyplot as plt
from PIL import Image
import piexif
import pandas as pd
import glob
from libtiff import TIFFimage
import subprocess
import argparse
import os
import datetime as dt

import micasense.utils as msutils
import micasense_calibration as mc

parser = argparse.ArgumentParser('Calibrate and correct all RedEdge images \
	acquired in a flight. You must already have run calc_rad2refl.py in \
	order to generate the file rad2refl_params.csv.')

parser.add_argument('flight_loc', type=str, help='str, absolute path to \
	top-level directory of this flight.')
parser.add_argument('-calmodel', dest='cal_model_fn', default=None, type=str, 
	help='str, absolute path to configuration file containing calibration \
	parameters for camera used in this flight. Only needed when camera \
	firmware < 2.1.0.')

args = parser.parse_args()

try:
	refl_factors = pd.read_csv(args.flight_loc + '/rad2refl_params.csv', 
		index_col='band')
except FileNotFoundError:
	print('Could not find rad2refl_params.csv in %s. Are you sure you have \
		run calc_rad2refl.py?')
	raise FileNotFoundError

images = glob.glob(args.flight_loc + 'raw/**/*.tif', recursive=True)

# Generate copy of directory structure under refl/
for dirpath, dirnames, filenames in os.walk(args.flight_loc + 'raw/'):
    structure = os.path.join(args.flight_loc + 'refl/', 
    				dirpath[len(args.flight_loc + 'raw/'):])
    if not os.path.isdir(structure):
        os.mkdir(structure)

n = 1
total_im = len(images)
for fl_im_name in images:
	print('%s / %s' %(n, total_im))

	# Load image and metadata
	fl_im_raw = plt.imread(fl_im_name)
	meta = mc.load_metadata(fl_im_name)

	# Add calibration model metadata
	if not mc.check_firmware_version(meta):
		meta = mc.add_cal_metadata(meta, cal_model_fn)

	band = meta.get_item('XMP:BandName')
	acq_time = dt.datetime.strptime(meta.get_item('EXIF:CreateDate'),
									 '%Y:%m:%d %H:%M:%S')
	# Convert acquisition time to julian to do time-dependent interpolation
	acq_time_julian = pd.Series([0], index=[acq_time]).index \
		.to_julian_date().values

	# Calculate rad2refl factor
	m = refl_factors.loc[band, 'm']
	c = refl_factors.loc[band, 'c']
	rad2refl = m * acq_time_julian + c

	# Apply corrections/conversions
	fl_im_refl_cor = mc.calibrate_correct_image(fl_im_raw, meta, rad2refl)

	# Create a tiff structure from image data
	tiff = TIFFimage(fl_im_refl_cor, description='')
	filename = args.flight_loc + 'refl/' + fl_im_name.split(args.flight_loc + 'raw/')[1]
	tiff.write_file(filename, compression='none') # or 'lzw'
	del tiff # flushes data to disk

	# Copy metadata to refl TIFF from radiance TIFF
	# Note that if calibration model is provided by user then this won't be 
	# written to output tiff.
	cmd = 'exiftool %s -overwrite_original -q -tagsFromFile %s' %(filename, fl_im_name)
	subprocess.call(cmd, shell=True)

	# Increment display counter
	n += 1



