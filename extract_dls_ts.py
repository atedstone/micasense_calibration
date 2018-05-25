"""

Extract Irradiance time series from Micasense RedEdge images acquired with 
Downwelling Light Sensor (DLS) attached.

"""

import glob
import datetime as dt
import pandas as pd

import micasense_calibration as mc

images = glob.glob('/scratch/rededge_calibration/20170723/raw/**/*.tif', recursive=True)

irrad = []
total_im = len(images)
n = 0
for fl_im_name in images:

	n += 1

	if n % 100 == 0:
		print('%s / %s (%s)' %(n, total_im, fl_im_name))	

	# Load image and metadata
	meta = mc.load_metadata(fl_im_name)

	band = meta.get_item('XMP:BandName')
	acq_time = dt.datetime.strptime(meta.get_item('EXIF:CreateDate'),
									 '%Y:%m:%d %H:%M:%S')

	irradiance = float(meta.get_item('XMP:Irradiance'))
	iyaw = float(meta.get_item('XMP:IrradianceYaw'))
	ipitch = float(meta.get_item('XMP:IrradiancePitch'))
	iroll = float(meta.get_item('XMP:IrradianceRoll'))
	igain = float(meta.get_item('XMP:IrradianceGain'))
	iexpt = float(meta.get_item('XMP:IrradianceExposureTime'))
	irrad.append(dict(acq_time=acq_time, band=band, i=irradiance, 
							yaw=iyaw, pitch=ipitch, roll=iroll,
							gain=igain, expo=iexpt))

dls = pd.DataFrame(irrad)

writer = pd.ExcelWriter('/scratch/rededge_calibration/20170723/DLS_TS.xlsx')
for band in dls.band.unique():
	dls_band = dls[dls.band == 'Red']
	dls_band.index = dls_band.acq_time
	dls_band = dls_band.drop('acq_time', axis=1)
	dls_band.to_excel(writer, sheet_name=band)
writer.save()      