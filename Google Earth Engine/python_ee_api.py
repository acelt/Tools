#-------------------------------------------------------------------------------
# Name:        testing GEE
# Purpose:
#
# Author:      alaurencetraynor
#
# Created:     15/12/2023
# Copyright:   (c) alaurencetraynor 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import ee
import pandas as pd
import geetools

# Trigger the authentication flow.
ee.Authenticate()

# Initialize the library.
ee.Initialize(project='blm-gee-alex-laurence-traynor')

# Define the time range for analysis
startDate = '2012'
endDate = '2022'

# Load the Rangeland Analysis Platform (RAP) dataset
rap = ee.ImageCollection("projects/rap-data-365417/assets/vegetation-cover-v3").filterDate(startDate, endDate)

aoi = ee.FeatureCollection('projects/blm-gee-alex-laurence-traynor/assets/CLAA')

clipped = rap.filterBounds(aoi)
# SET PARAMS
scale = 30
name_pattern = '{sat}_{system_date}_coverV3'
date_pattern = 'ddMMMy' # dd: day, MMM: month (JAN), y: year
folder = 'MYFOLDER'
data_type = 'uint32'
extra = dict(sat='RAP')
region = aoi

# Create an export task

tasks = geetools.batch.Export.imagecollection.toDrive(
            collection=clipped,
            folder=folder,
            region=region,
            namePattern=name_pattern,
            scale=scale,
            dataType=data_type,
            datePattern=date_pattern,
            extra=extra,
            verbose=True,
            maxPixels=int(1e13),
            crs='EPSG:5070'
        )


# add projections to this
crs='EPSG:5070'