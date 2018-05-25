#! /usr/bin/env python
"""
Derive radiance-reflectance parameters for a flights bounded at start and 
end by photos of reflectance panels.

This script is interactive and plots figure windows. If using over SSH you 
must enable X-window forwarding.

e.g. calc_rad2refl.py /scratch/rededge_calibration/panel_RP02-1603157-SC.csv /scratch/rededge_calibration/20170723/raw/000/IMG_0000 /scratch/rededge_calibration/20170723/raw/001/IMG_0032 /scratch/rededge_calibration/20170723/ -calmodel /scratch/rededge_calibration/calmodel_sn1620051.config
calc_rad2refl.py /scratch/rededge_calibration/panel_RP02-1603157-SC.csv /scratch/rededge_calibration/20170724/raw/0000SET/000/IMG_0000 /scratch/rededge_calibration/20170723/raw/0001SET/001/IMG_0163 /scratch/rededge_calibration/20170724/ -calmodel /scratch/rededge_calibration/calmodel_sn1620051.config

Andrew Tedstone (a.j.tedstone@bristol.ac.uk), November 2017

"""
import matplotlib
matplotlib.use('TkAgg')
matplotlib.rcParams['interactive'] = True

import statsmodels.api as sm
import matplotlib.pyplot as plt
import pandas as pd
import argparse

import micasense_calibration as mc

parser = argparse.ArgumentParser('Derive radiance-reflectance parameters for \
 a flights bounded at start and end by photos of reflectance panels.')

parser.add_argument('panel', type=str, help='str, absolute path to CSV file \
	containing calibration factors for your reflectance panel.')
parser.add_argument('p_pre', type=str, help='str, absolute path to pre-flight \
 set of images of reflectance panel, ending before band number. \
 e.g. /scratch/SET/IMG_0000_')
parser.add_argument('p_post', type=str, help='str, absolute path to \
	post-flight set of images of reflectance panel, ending before band \
	number. e.g. /scratch/SET/IMG_0000_')
parser.add_argument('flight_loc', type=str, help='str, absolute path to \
	top-level directory of this flight.')
parser.add_argument('-calmodel', dest='cal_model_fn', default=None, type=str, 
	help='str, absolute path to configuration file containing calibration \
	parameters for camera used in this flight. Only needed when camera \
	firmware < 2.1.0.')

args = parser.parse_args()

panel_factors = mc.load_panel_factors(args.panel)
print(panel_factors)

print('Interactive? %s' %(plt.isinteractive()))


# Calculate factors at start of flight
print('Processing pre-flight images')
print('.....................................................................')
factors1d = {}
for index, row in panel_factors.iterrows():
	print('IX: ', index)
	fn = args.flight_loc + args.p_pre + str(int(row['band_number'])) + '.tif'
	print('Handling %s' %fn)
	f, date1 = mc.radrefl_factor(panel_factors, image_name=fn, 
		cal_model_fn=args.cal_model_fn,
		return_date=True)
	factors1d[index] = f
	mc.plotutils.plt.close()


# Calculate factors at end of flight
print('Processing post-flight images')
print('.....................................................................')
factors2d = {}
for index, row in panel_factors.iterrows():
	fn = args.flight_loc + args.p_post + str(int(row['band_number'])) + '.tif'
	print('Handling %s' %fn)
	f, date2 = mc.radrefl_factor(panel_factors, image_name=fn, 
		cal_model_fn=args.cal_model_fn,
		return_date=True)
	factors2d[index] = f
	mc.plotutils.plt.close()

p1 = pd.Series(factors1d)
p1.name = 'p1'
p2 = pd.Series(factors2d)
p2.name = 'p2'
factors = pd.concat((p1, p2), axis=1)

# Time-dependent interpolation
mm = {}
cc = {}
for index, row in factors.iterrows():
	df = pd.DataFrame({'factor':[row.p1, row.p2]},
			index=[date1, date2])
	df['jDate'] = df.index.to_julian_date()
	X = sm.add_constant(df['jDate'], has_constant='add')
	model = sm.OLS(df['factor'], X)
	ols_fit = model.fit() 
	m = ols_fit.params[1]
	c = ols_fit.params[0]
	mm[index] = m
	cc[index] = c

mmpd = pd.Series(mm, name='m')
ccpd = pd.Series(cc, name='c')
# Add m and c terms of regression to DataFrame
panel_factors_complete = pd.concat((panel_factors, factors, mmpd, ccpd), axis=1)

# Save for future use
fn_out = args.flight_loc + '/' + 'rad2refl_params.csv'
panel_factors_complete.to_csv(fn_out)
print('Parameters saved to %s.' %(fn_out))