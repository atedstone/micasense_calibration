"""
Driver script for a flight bounded by reflectance panels at the beginning and end
"""

import statsmodels.api as sm

import micasense_calibration as mc

panel_factors = mc.load_panel_factors('/scratch/rededge_calibration/panel_RP02-1603157-SC.csv')

#flight_refl1 = '/scratch/rededge_calibration/20170723/0006SET/000/IMG_0000_'

# Calculate factors at start of flight
flight_refl1 = '~/scripts/micasense-proc/data/0000SET/000/IMG_0000_'
factors1 = []
for n in range(1, 5):
	fn = flight_refl1 + str(n) + '.tif'
	f, date1 = mc.radrefl_factor(panel_factors, image_name=fn, return_date=True)
	factors1.append(f)

# Calculate factors at end of flight
flight_refl2 = '~/scripts/micasense-proc/data/0000SET/000/IMG_0000_'
factors2 = []
for n in range(1, 5):
	fn = flight_refl2 + str(n) + '.tif'
	f, date2 = mc.radrefl_factor(panel_factors, image_name=fn, return_date=True)
	factors2.append(f)

# Time-dependent interpolation
mm = []
cc = []
for n in range(0, 4):
	X = [date1, date2] 
	X = sm.add_constant(X)
	y = [factors1[n], factors2[n]]
	model = sm.OLS(y, X)
	ols_fit = model.fit() 
	m = ols_fit.params[1]
	c = ols_fit.params[0]

# Add m and c terms of regression to DataFrame
panel_factors = panel_factors.to_frame()
panel_factors['m'] = mm
panel_factors['c'] = cc


## Now process images ...


