#-------------------------------------------------------------------------------
# Name:        Revist Report for Terra with Species List.py
# Purpose:
#   Using ReportLab and PIL to create a PDF Plot Revisit report for each PrimaryKey given
#   in a txt file
#
# Author:      dbrowning
#
# Created:     7/8/2020
# Modified:    7/8/2020
#
#
#
#   Modified
#
#
#
#   Dependencies - need ReportLab installed by IT in order for this script to work
#                - need to install Pil
#               - in the BLM use this from the C:\Python27\ArcGIS10.8\Scripts python -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org PIL
#
#   Start pages at 20,760
#
#   Added a list of species from Spec Ind tables to a new page 4
#   Added a way to handle soil dups form when people reuse DIMAs
#   Added a way to order Horizons
#-------------------------------------------------------------------------------
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm, inch, pica
from PIL import Image
import arcpy, os, textwrap
import pandas as pd

# Setup your paths here!!
sdeConn = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\AIMDataTools\SDE\AIMTerrestrialPub.sde"
photosDir = r"\\blm.doi.net\dfs\loc\EGIS\ReferenceNational\environment\BLM_AIM\LMF"
outputFolder = r"\\blm\dfs\loc\EGIS\ProjectsNational\AIM\Data\Development\Reports\Revisit\USGS"
pkFile = r"W:\My Documents\ArcGIS\LMF_pks.txt"

# Using Pub SDE
terraFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.LMF"
terraSDE = sdeConn + "\\" + terraFC
plotsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.POINT"
plotsSDE = sdeConn + "\\" + plotsFC
soilhorFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.SOILHORIZON"
soilhorSDE = sdeConn + "\\" + soilhorFC
specindFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.LMFSpeciesIndicators"
specindSDE = sdeConn + "\\" + specindFC
gpsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.GPS"
gpsSDE = sdeConn + "\\" + gpsFC

# create empty lists to fill with missing photo pks and info
missing_photos = []
missing_ids = []
missing_project = []
missing_state = []

# Get a list of PrimaryKeys from a supplied text file
pkFileLink = open(pkFile, 'r')
pkList = pkFileLink.read().splitlines()
pkFileLink.close()
#Test PK 18112809100042272018-09-01
#pkList = ["13072013104551182013-09-01"]

# make a report for each PrimaryKey
for pk in pkList:
    print("Checking photos for " + pk)

    # Join to get
    arcpy.MakeFeatureLayer_management(terraSDE, "terraLayer")
    arcpy.AddJoin_management("terraLayer", "PrimaryKey", plotsSDE, "PrimaryKey")

    # adding one more join to pull in elevation
    arcpy.AddJoin_management("terraLayer", "PrimaryKey", gpsSDE, "PrimaryKey")

    fields = [terraFC + '.PrimaryKey', terraFC + '.PlotID', terraFC + '.Latitude_NAD83', terraFC + '.Longitude_NAD83', terraFC + ".State", plotsFC + ".SLOPE_PERCENT", \
            plotsFC + ".SLOPE_ASPECT", terraFC + ".EcologicalSiteId", plotsFC + ".COMPONENT_NAME", plotsFC + ".PSU", plotsFC + ".POINT", plotsFC + ".SURVEY", plotsFC + ".STATE", plotsFC + ".COUNTY", gpsFC + ".ELEVATION"]
    whereClause = terraFC + ".PrimaryKey = '" + pk + "'"

    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor("terraLayer", fields, whereClause) as cursor:
        for row in cursor:

            # need to add leading zeros to state/county if they arent there already
            photoState = str(row[12]).zfill(2)
            photoCounty = str(row[13]).zfill(3)

            photoKey = photoState + photoCounty

            photoPSU = str(row[9])
            photoYear = str(row[11])
            photoPoint = 'point' + str(row[10])

            plotID = row[1]

    # Grad the images and add all of them.  Easier to use file path than URL
    photoPath = photosDir + "\\" + photoKey + "\\" + photoPSU + "\\" + photoPoint + "\\" + photoYear

    # If the photo directory doesnt exist, create one
    import os
    if not os.path.exists(photoPath):
        fields = ['PrimaryKey', 'PlotID','ProjectName','SpeciesState']
        whereClause = "PrimaryKey = '" + pk + "'"

        with arcpy.da.SearchCursor(terraSDE, fields, whereClause) as cursor:
            for row in cursor:
                missing_photos.append(row[0])
                missing_ids.append(row[1])
                missing_project.append(row[2])
                missing_state.append(row[3])

        print(photoPath)
        print("Photo path does not exist")


    arcpy.RemoveJoin_management("terraLayer")
    arcpy.Delete_management("terraLayer")

dict = {'PrimaryKey':missing_photos, 'PlotID':missing_ids, 'ProjectName':missing_project, 'State':missing_state}
df = pd.DataFrame(dict)
df.to_csv(path_or_buf = outputFolder + '/' + 'missing_photos_lmf.csv',header = False, index = False)

print("All Done")
