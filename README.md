# README

This repo provides a processing chain for converting raw MicaSense RedEdge images to undistorted reflectance images suitable for orthomosaic generation in Agisoft PhotoScan.

It uses the common approach of radiometric calibration using images of reflectance panels acquired before and after a UAV flight. The Downwelling Light Sensor (DLS) data are not utilised at this point in time.


## Environment requirements

Recommend creating a new conda/mini-conda environment which fulfills the MicaSense-mandated requirements and those needed by this repository:

    conda install -c conda-forge python=3.5 ipython matplotlib pillow numpy pandas opencv statsmodels libtiff

You may also want to add `tkinter` via conda if you want to use the pop-up file dialog option in `micasense_calibration.radrefl_factor`, but this is not required by the current driver scripts.

Place the MicaSense Image Processsing repository (<https://github.com/micasense/imageprocessing>) on `PYTHONPATH`.

You must also install `exiftool` and `pyexiftool` as specified in <https://micasense.github.io/imageprocessing/MicaSense%20Image%20Processing%20Setup.html.>

Finally, consider adding the path to this repository to your system `$PATH` so that you can use the scripts directly regardless of your present working directory.


## Supplementary files needed

### Panel reflectance factor

A CSV file (known later in this readme as `panel_values.csv`) containing panel reflectance factor data for your particular panel. You can request this data from Micasense: 

https://support.micasense.com/hc/en-us/articles/224590508-Where-can-I-find-reflectance-values-for-my-panels

The CSV file must have columns of 'band' and 'factor'. Each row must contain the factor for each band. Each band must use the name specified in the RedEdge image metadata. See the example file provided in this repository.


### Camera Calibration Model

Only relevant if using a RedEdge camera with firmware version < 2.1.0. In newer firmware versions of the metadata describing the camera calibration model are stored automatically in the image. (See https://support.micasense.com/hc/en-us/articles/115000351194-RedEdge-Camera-Radiometric-Calibration-Model for more information).

The file (known later in this readme as `camera.config`) must contain the following:

    [Model]
    RadiometricCalibration=
    VignettingPolynomial=
    VignettingCenter=
    PerspectiveDistortion=
    PerspectiveFocalLength=


## Workflow

Arrange your working environment as follows:

    all_flights /
        panel_values.csv
        camera.config
        flight<date>/   (flight_directory)
            raw/
                <all camera files, in their original hierarchy - e.g...>
                0000SET/
                    000/
                        <lots of TIFs>
                    001/
                        <lots of TIFs>
                0010SET/
                    000/
                        <lots of TIFs>
            refl/
                <the processing chain will automatically recreate the raw hierarchy here and save TIFFs of undistorted reflectance>
        flight<date>.../
            as above.

Processing for each UAV flight then consists of two steps (undertaken on your system command line):

1. Run `calc_rad2refl.py <panel_file> <pre_flight_images> <post_flight_images> <flight_directory>`. This is an interactive script which generates a CSV file of radiance-reflectance parameters, stored in your flight directory. It will display each band of each of the two sets of reflectance panel images one-by-one, and will ask you to click first the top-left then the bottom-right of the panel region in each image. Format of pre_ and post_flight_image filenames: '/scratch/SET/IMG_0000_'.
2. Run `process_flight_images.py <flight_directory>`. This script applies the radiance-reflectance parameters generated in Step 1 to a whole flight of images. This script can be run unattended.

The images saved to `refl/` are then ready to be imported to AgiSoft PhotoScan.


## Format of output files

16-bit TIFFs, with all original EXIF metadata attached. Values saved as reflectance (floating-point), so they will appear blank in most software, but PhotoScan does understand them.


## Example

This example uses the `data/` folder provided as part of the MicaSense Image Processing repository.

The panel calibration values for the panel used in the MicaSense example data are in `panel_example_ds.csv`.

Note in this example that only the pre-flight reflectance panel images are available, so we will use them twice in order to imitate panels being available pre- and post-flight.

    export PATH=$PATH:path/to/this/repository
    cd path/to/micasense/imageprocessing/data
    mkdir raw
    mkdir refl
    mv 0000SET raw/
    calc_rad2refl.py path/to/this/repository/panel_example_ds.csv raw/0000SET/000/IMG_0000_ raw/0000SET/000/IMG_0000_ .
    process_flight_images.py .

(N.b. the `.` signifies 'the current working directory').

This will result in reflectance images being written to `./refl/*`.








