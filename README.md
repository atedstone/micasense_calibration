# README

## Environment requirements

    conda install -c conda-forge python=3.5 ipython matplotlib pillow numpy pandas opencv tkinter

Place micasense repository (https://github.com/micasense/imageprocessing) on `PYTHONPATH`.

And install `pyexiftools` as per micasense instructions.

Need piexif: http://piexif.readthedocs.io/en/latest/installation.html


## Workflow

Need to compute rad-refl factor for every band for every flight.

## Supplementary files needed

### Panel reflectance factor

A CSV file containing panel reflectance factor data for your particular panel. You can request this data from Micasense: 

https://support.micasense.com/hc/en-us/articles/224590508-Where-can-I-find-reflectance-values-for-my-panels

The CSV file must have columns of 'band' and 'factor'. Each row must contain the factor for each band. Each band must use the name specified in the RedEdge image metadata. See the example file provided in this repository.


### Camera Calibration Model

Only relevant if using a RedEdge camera with firmware version < 2.1.0. In newer firmware versions of the metadata describing the camera calibration model are stored automatically in the image. (See https://support.micasense.com/hc/en-us/articles/115000351194-RedEdge-Camera-Radiometric-Calibration-Model for more information).

The file must contain the following:

    [Model]
    RadiometricCalibration=
    VignettingPolynomial=
    VignettingCenter=
    PerspectiveDistortion=
    PerspectiveFocalLength=

