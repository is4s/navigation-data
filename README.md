# Navigation Data

The purpose of this repo is to store data for other projects. Any commits which modify or remove
data files should be squashed in order to minimize download size.

## Source Data

 `WW15MGH.GRD` contains the EGM96 15 minute interpolation grid (difference between MSL and
  HAE) data from [the NGA website](https://earth-info.nga.mil/).

## Test Data

This repo contains the following test data:

#### bogota.tif
A simulated GeoTIFF data set located in South America taken from
[osgeo.com](https://download.osgeo.org/geotiff/samples/made_up/). It contains the following
coordinates:

```gdalinfo
Upper Left    ( 440720.000, 100000.000)  ( 79d 6'28.18"W,  3d31'34.94"S)
Lower Left    ( 440720.000,  69280.000)  ( 79d 6'33.75"W,  3d48'11.17"S)
Upper Right   ( 471440.000, 100000.000)  ( 78d49'56.53"W,  3d31'40.18"S)
Lower Right   ( 471440.000,  69280.000)  ( 78d50' 1.80"W,  3d48'16.83"S)
Center        ( 456080.000,  84640.000)  ( 78d58'15.06"W,  3d39'55.82"S)
```

#### n30_w082.dt2

A DTED file from the SRTM data set located in Florida taken from
[EarthExplorer](https://earthexplorer.usgs.gov/). From the Datasets tab, go to:
`Digital Elevation > SRTM > SRTM 1 Arc-second Global`. In the `Additional Criteria` tab,
enter `SRTM1N30W082V3` for the `Entity ID`.

This file was downsampled from 30m to 90m spacing to improve test times via the command:

```sh
gdal_translate -outsize 1201 1201 ~/Downloads/n30_w082_1arc_v3.dt2 n30_w082.dt2
```

It contains the following coordinates:

```gdalinfo
Upper Left  ( -82.0004167,  31.0004167) ( 82d 0' 1.50"W, 31d 0' 1.50"N)
Lower Left  ( -82.0004167,  29.9995833) ( 82d 0' 1.50"W, 29d59'58.50"N)
Upper Right ( -80.9995833,  31.0004167) ( 80d59'58.50"W, 31d 0' 1.50"N)
Lower Right ( -80.9995833,  29.9995833) ( 80d59'58.50"W, 29d59'58.50"N)
Center      ( -81.5000000,  30.5000000) ( 81d30' 0.00"W, 30d30' 0.00"N)
```
