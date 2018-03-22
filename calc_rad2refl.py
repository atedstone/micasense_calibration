#! /usr/bin/env python
"""
Derive radiance-reflectance parameters for a flights bounded at start and 
end by photos of reflectance panels.

This script is interactive and plots figure windows. If using over SSH you 
must enable X-window forwarding.

e.g. calc_rad2refl.py /scratch/rededge_calibration/panel_RP02-1603157-SC.csv /scratch/rededge_calibration/20170723/raw/000/IMG_0000 /scratch/rededge_calibration/20170723/raw/001/IMG_0032 /scratch/rededge_calibration/20170723/ -calmodel /scratch/rededge_calibration/calmodel_sn1620051.config

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

print('Interactive? %s' %(plt.isinteractive()))


# Calculate factors at start of flight
print('Processing pre-flight images')
print('.....................................................................')
factors1 = []
for n in range(1, 6):
	fn = args.flight_loc + args.p_pre + str(n) + '.tif'
	print('Handling %s' %fn)
	f, date1 = mc.radrefl_factor(panel_factors, image_name=fn, 
		cal_model_fn=args.cal_model_fn,
		return_date=True)
	factors1.append(f)
	mc.plotutils.plt.close()


# Calculate factors at end of flight
print('Processing post-flight images')
print('.....................................................................')
factors2 = []
for n in range(1, 6):
	fn = args.flight_loc + args.p_post + str(n) + '.tif'
	print('Handling %s' %fn)
	f, date2 = mc.radrefl_factor(panel_factors, image_name=fn, 
		cal_model_fn=args.cal_model_fn,
		return_date=True)
	factors2.append(f)
	mc.plotutils.plt.close()


# Time-dependent interpolation
mm = []
cc = []
for n in range(0, 5):
	df = pd.DataFrame({'factor':[factors1[n], factors2[n]]},
			index=[date1, date2])
	df['jDate'] = df.index.to_julian_date()
	X = sm.add_constant(df['jDate'], has_constant='add')
	model = sm.OLS(df['factor'], X)
	ols_fit = model.fit() 
	m = ols_fit.params[1]
	c = ols_fit.params[0]
	mm.append(m)
	cc.append(c)

# Add m and c terms of regression to DataFrame
panel_factors = panel_factors.to_frame()
panel_factors['p1'] = factors1
panel_factors['p2'] = factors2
panel_factors['m'] = mm
panel_factors['c'] = cc

# Save for future use
fn_out = args.flight_loc + '/' + 'rad2refl_params.csv'
panel_factors.to_csv(fn_out)
print('Parameters saved to %s.' %(fn_out))