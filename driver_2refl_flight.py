"""
Driver script for a flight bounded by reflectance panels at the beginning and end
"""

import statsmodels.api as sm
import matplotlib.pyplot as plt
from PIL import Image
import piexif
import pandas as pd
import glob

import micasense.utils as msutils
import micasense_calibration as mc

panel_factors = mc.load_panel_factors('/scratch/rededge_calibration/panel_RP02-1603157-SC.csv')
cal_model_fn = '/scratch/rededge_calibration/calmodel_sn1620051.config'

#flight_refl1 = '/scratch/rededge_calibration/20170723/0006SET/000/IMG_0000_'

# Calculate factors at start of flight
flight_refl1 = '/home/at15963/scripts/micasense-proc/data/0000SET/000/IMG_0000_'
factors1 = []
for n in range(1, 6):
	fn = flight_refl1 + str(n) + '.tif'
	print('Handling %s' %fn)
	f, date1 = mc.radrefl_factor(panel_factors, image_name=fn, 
		#cal_model_fn=cal_model_fn,
		return_date=True)
	factors1.append(f)
	plt.close('all')


# Calculate factors at end of flight
flight_refl2 = '/home/at15963/scripts/micasense-proc/data/0000SET/000/IMG_0000_'
factors2 = []
for n in range(1, 6):
	fn = flight_refl2 + str(n) + '.tif'
	f, date2 = mc.radrefl_factor(panel_factors, image_name=fn, 
		#cal_model_fn=cal_model_fn,
		return_date=True)
	factors2.append(f)
	plt.close('all')


# Time-dependent interpolation
mm = []
cc = []
for n in range(0, 5):
	df = pd.DataFrame({'factor':[factors1[n], factors2[n]]}, index=[date1, date2])
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
#panel_factors.to_csv('/scratch/rededge_calibration/flight20170723.csv')
panel_factors.to_csv('/scratch/rededge_calibration/testing.csv')






## check that the image we are looking at has a timestamp the puts it with the flight

## Now process images ...
#pre_path = '/scratch/rededge_calibration/20170723/'
#images = glob.glob(pre_path + 'raw/**/*.tif', recursive=True)
pre_path = '/home/at15963/scripts/micasense-proc/data/'
images = glob.glob(pre_path + 'raw/**/*.tif', recursive=True)

# Generate copy of directory structure under refl/
for dirpath, dirnames, filenames in os.walk(pre_path + 'raw/'):
    structure = os.path.join(pre_path + 'refl/', dirpath[len(pre_path + 'raw/'):])
    if not os.path.isdir(structure):
        os.mkdir(structure)

n = 1
total_im = len(images)
for fl_im_name in images:
	print('%s / %s' %(n, total_im))
	fl_im_raw = plt.imread(fl_im_name)
	meta = mc.load_metadata(fl_im_name)
	# Add calibration model metadata
	#meta = mc.add_cal_metadata(meta, cal_model_fn)
	band = meta.get_item('XMP:BandName')
	acq_time = dt.datetime.strptime(meta.get_item('EXIF:CreateDate'), '%Y:%m:%d %H:%M:%S')
	acq_time_julian = pd.Series([0], index=[acq_time]).index.to_julian_date().values

	m = panel_factors.loc[band, 'm']
	c = panel_factors.loc[band, 'c']
	rad2refl_factor = m * acq_time_julian + c

	fl_im_rad, _, _, _ = msutils.raw_image_to_radiance(meta, fl_im_raw)
	fl_im_refl = fl_im_rad * rad2refl_factor
	fl_im_refl_cor = msutils.correct_lens_distortion(meta, fl_im_refl)

	to_save = Image.fromarray(fl_im_refl_cor)
	exif_bytes = piexif.dump(meta.exif)
	#filename = fl_im_name.split(pre_path + 'raw/')[1]
	filename = fl_im_name.split(pre_path + 'raw/')[1]
	to_save.save(pre_path + 'refl/' + filename, exif=exif_bytes)
	to_save = None

	n += 1