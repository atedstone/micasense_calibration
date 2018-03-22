#! /usr/bin/env python
"""
Use after process_flight_images.py
Call with path to the flight, e.g. 
sort_images.py /scratch/process/rededge/20170723/
"""

import glob
import subprocess
import sys

path_in = sys.argv[1]

images = glob.glob(path_in + '/refl/**/*.tif', recursive=True)

# Rename each image so that folder details are in file name; move to main folder
for image in images:
	folders = image.split('/')
	new_fn = path_in + '/refl/' + folders[-3] + '_' + folders[-2] + '_' + folders[-1]
	subprocess.call('mv %s %s' %(image, new_fn), shell=True)
	print(new_fn)

# create one directory per band and move images into them
for n in range(1,6):
	subprocess.call('mkdir %s/band%s' %(path_in, n), shell=True)
	subprocess.call('mv %s/refl/*_%s.tif band%s/' %(path_in,n,n), shell=True)


