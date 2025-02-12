    #-------------------------------------------------------------------------------
# Name:        Revist Report for Terra with Species List.py
# Purpose:
#   Using ReportLab and PIL to create a PDF Plot Revisit report for each PrimaryKey given
#   in a txt file. Importing revisit info from terradat and sample design database
#
# Author:      alaurencetraynor
#
# Created:     4/10/2024
#
#
#   Modified
##
#   Dependencies - need ReportLab installed by IT in order for this script to work
#                - need to install Pil
#               - in the BLM use this from the C:\Python27\ArcGIS10.8\Scripts python -m pip install --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --trusted-host pypi.org PIL
#
#   Start pages at 20,760
#
#   Added a list of species from Spec Ind tables to a new page 4
#   Added a way to handle soil dups form when people reuse DIMAs
#   Added a way to order Horizons

# Feature/content requests:
# Pull plot photos from the most recent visit to a plot, not the first visit.
# - to do this: need to grab all connected visits - should be connected via v1 PK; sort by date, then select most recent visit to pull photos
# Provide species lists from all prior visits to a plot, not just the first visit (making sure they're clearly distinguished). Or, if only providing one species list, make it the most recent rather than the first.
# - same as above but list all PKs connect to V1PK and loop through species indicators for each
# Note on the revisit report whether a plot was moved from the original location when it was established.
# - dont currently have the ability to do this reliably/rapidly
# file named by plot ID shown in field map
# - will need CO plot service to do this and then simple join and rename. However making this change will require changes to pop-up config  so report link still works
#-------------------------------------------------------------------------------
# added for ArcPro to get ReportLab
import sys
reportlabPath = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Data\Software\ReportLab for Python 3"
sys.path.append(reportlabPath)

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm, inch, pica
from PIL import Image
import arcpy, os, textwrap
import pandas as pd
from arcgis.features import GeoAccessor, GeoSeriesAccessor
from arcgis import GIS
import datetime

# Setup your paths here!!
sdeConn = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\AIMDataTools\SDE\AIMTerrestrialPub.sde"
photosDir = r"\\blm.doi.net\dfs\loc\EGIS\ReferenceNational\environment\BLM_AIM\TerrADat"
LMFphotosDir = r"\\blm.doi.net\dfs\loc\EGIS\ReferenceNational\environment\BLM_AIM\LMF" # adding this for LMF

# Instead of a text file well use a layer from the tool input
# this should be a selection from the plot service
pkLayer = arcpy.GetParameterAsText(0)

# output folder
outputFolder = arcpy.env.scratchFolder

# Have to build a PK list for TerraDat and a list for LMF seperate
terrapkList = [row[0] for row in arcpy.da.SearchCursor(pkLayer, ["PrimaryKey"], "ProjectName <> 'LMF'")]
lmfpkList = [row[0] for row in arcpy.da.SearchCursor(pkLayer, ["PrimaryKey"], "ProjectName = 'LMF'")]

# warning for too large a list - could make this an error too, to prevent long load times
if len(terrapkList)+len(lmfpkList) >20:
    arcpy.AddWarning("More than 20 points selected, this may take a while...")
    #arcpy.AddError("More than 20 points selected, select fewer points to run tool")

stateList = set([row[0] for row in arcpy.da.SearchCursor(pkLayer, ["SpeciesState"])])

arcpy.AddMessage("Got list of PrimaryKeys - " + str(len(terrapkList)) + " plots from TerraDat and " + str(len(lmfpkList)) + " LMF plots")

# Colorados copy of the SDD
## May want to use this service instead: https://gis.dev.blm.doi.net/arcgis/rest/services/AIM/BLM_Natl_AIM_TerrestrialSDD/FeatureServer

#this will get messy if theres more than one state including CO, so maybe add an error message for now
if len(stateList)>1 and "CO" in stateList:
    arcpy.AddError("Plots from more than one State were selected - Currently this tool only works for individual states")

if stateList == "CO":
    SDD = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Projects\CO\CO_SDD\CO_SDD_20230613_NAD83.gdb"
else:
    SDD = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\AIMDataTools\SDE\AIMDev.sde"

# create empty lists to fill with missing photo pks and info
missing_photos = []
missing_ids = []
missing_project = []
missing_state = []

# Using Pub SDE
terraFC = "ilmocAIMdev.ILMNATAIMDEV.TerraDat"
terraSDE = os.path.join(SDD, terraFC) # switching out for AIMdev to get designpointkeys
photoFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblTerraDatPhotoLinks"
photoSDE = os.path.join(sdeConn, photoFC)
linesFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblLines"
linesSDE = os.path.join(sdeConn, linesFC)
lpiheaderFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblLPIHeader"
lpiheaderSDE = os.path.join(sdeConn,  lpiheaderFC)
plotsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblPlots"
plotsSDE = os.path.join(sdeConn, plotsFC)
soilpitsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblSoilPits"
soilpitsSDE = os.path.join(sdeConn, soilpitsFC)
soilhorFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblSoilPitHorizons"
soilhorSDE = os.path.join(sdeConn, soilhorFC)
specindFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.TerrADatSpeciesIndicators"
specindSDE = os.path.join(sdeConn, specindFC)

if stateList == "CO":
    designPoints = "CO_TerrestrialPlotFates_20230515"
    designPointsFC = os.path.join(SDD, designPoints)
else:
    designPoints = "ilmocAIMdev.ILMNATAIMDEV.DesignPoints"
    designPointsFC = os.path.join(SDD,designPoints)

# LMF specific paths
lmfterraFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.LMF"
lmfterraSDE =  os.path.join(sdeConn,lmfterraFC)
lmfplotsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.POINT"
lmfplotsSDE =  os.path.join(sdeConn,  lmfplotsFC)
lmfsoilhorFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.SOILHORIZON"
lmfsoilhorSDE =  os.path.join(sdeConn,lmfsoilhorFC)
lmfspecindFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.LMFSpeciesIndicators"
lmfspecindSDE =  os.path.join(sdeConn,lmfspecindFC)
gpsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.GPS"
gpsSDE =  os.path.join(sdeConn,gpsFC)

# Functions---------------------------------------------------------
def fill_page_with_image(path, canvas):
    """
    Given the path to an image and a reportlab canvas, fill the current page
    with the image.

    This function takes into consideration EXIF orientation information (making
    it compatible with photos taken from iOS devices).

    This function makes use of ``canvas.setPageRotation()`` and
    ``canvas.setPageSize()`` which will affect subsequent pages, so be sure to
    reset them to appropriate values after calling this function.

    :param   path: filesystem path to an image
    :param canvas: ``reportlab.canvas.Canvas`` object
    """
    from PIL import Image

    page_width, page_height = canvas._pagesize

    try:
        image = Image.open(path)

        image_width, image_height = image.size
        # Plot Drawings are failing here so added a check
        if hasattr(image, '_getexif') and image._getexif() is not None:
        #if hasattr(image, '_getexif'):
            orientation = image._getexif().get(274, 1)  # 274 = Orientation
        else:
            orientation = 1

        # These are the possible values for the Orientation EXIF attribute:
        ORIENTATIONS = {
            1: "Horizontal (normal)",
            2: "Mirrored horizontal",
            3: "Rotated 180",
            4: "Mirrored vertical",
            5: "Mirrored horizontal then rotated 90 CCW",
            6: "Rotated 90 CW",
            7: "Mirrored horizontal then rotated 90 CW",
            8: "Rotated 90 CCW",
        }
        draw_width, draw_height = page_width-10, page_height-10
        if orientation == 1:
            canvas.setPageRotation(0)
        elif orientation == 3:
            canvas.setPageRotation(180)
        elif orientation == 6:
            image_width, image_height = image_height, image_width
            draw_width, draw_height = page_height-10, page_width-10
            canvas.setPageRotation(90)
        elif orientation == 8:
            image_width, image_height = image_height, image_width
            draw_width, draw_height = page_height-10, page_width-10
            canvas.setPageRotation(270)
        else:
            newsize = (600,600) # getting some issues here with odd sized photos so resizing to catch those
            image = image.resize(newsize)

        if image_width > image_height:
            page_width, page_height = page_height, page_width  # flip width/height
            draw_width, draw_height = draw_height, draw_width
            canvas.setPageSize((page_width, page_height))

        canvas.drawImage(path, 0, 0, width=draw_width, height=draw_height,
                         preserveAspectRatio=True)
    except:
        print("Issue reading photo from "+ path)
# End Functions -----------------------------------------------------------

# Get a list of PrimaryKeys from a supplied layer
# make a report for each PrimaryKey
for pk in terrapkList:

    # Get PrimaryKeys from all visits

    if "CO" in stateList :
        designPoints_df = pd.DataFrame.spatial.from_featureclass(designPointsFC)
        designPoints_df_pk = designPoints_df.loc[designPoints_df.PrimaryKey == pk, ['PlotID', 'Visit', 'DateVisited', 'PrimaryKey', 'Visit1PrimaryKey', 'Comments']]
    else:
        # designpoints doesnt have primarykey so need to join to sampled points first via designpointkey
        designPoints_df = pd.DataFrame.spatial.from_featureclass(terraSDE)
        designPoints_df_pk = designPoints_df.loc[designPoints_df.PrimaryKey == pk, ['PlotID', 'PrimaryKey', 'DesignPointKey','DateVisited','Visit1PrimaryKey']]

    plotid = designPoints_df_pk['PlotID'].values[0]

    arcpy.AddMessage("Building Revisit Report for " + pk + " also known as "+ plotid)

    # Join to get plot info
    arcpy.MakeFeatureLayer_management(terraSDE, "terraLayer")
    arcpy.AddJoin_management("terraLayer", "PrimaryKey", plotsSDE, "PrimaryKey")

    # Grab info from SDD too and join to terra layer
    arcpy.MakeFeatureLayer_management(designPointsFC, "designLayer")
    # join via teh designpointkey to link to SDD
    arcpy.AddJoin_management("terraLayer", "DesignPointKey", "designLayer", "DesignPointKey")

    fields = [terraFC + '.PrimaryKey', terraFC + '.PlotID', terraFC + '.Latitude_NAD83', terraFC + '.Longitude_NAD83', terraFC + ".State", plotsFC + ".Elevation", plotsFC + ".Slope",
            plotsFC + ".Aspect", plotsFC + ".LandscapeType", plotsFC + ".LandscapeTypeSecondary", plotsFC + ".EcolSite", plotsFC + ".Soil", plotsFC + ".Directions", terraFC + ".Visit1PrimaryKey", designPoints + ".PlotID"]
    whereClause = terraFC + ".PrimaryKey = '" + pk + "'"

    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor("terraLayer", fields, whereClause) as cursor:
        for row in cursor:
            # Adding a check for wierd characters in plot ID (e.g. "/")
            # import re
            # re.sub("/", "_", row[1])
            # it doesnt quite work yet

            # Start the PDF
            pdfOut = canvas.Canvas(os.path.join(outputFolder, "Visit Report for " + plotid + ".pdf"))

            # change font
            pdfOut.setFont("Helvetica", 14)

            # grad for photo part later
            # Terradat has a difference in state here compared to the directory on EGIS
            if row[4] == 'WA':
                photoState = 'OR'
            elif row[4] == 'SD' or row[4] == 'ND':
                photoState = 'MT'
            else:
                photoState = row[4]
            photoKey = row[0]
            plotID = row[1]

            lineOffset = 760
            pdfOut.drawString(200,792,"Visit report for PlotID " + row[1])
            pdfOut.drawString(20,lineOffset,"PrimaryKey: " + row[0])
            pdfOut.drawString(20,lineOffset-20,"Latitude_NAD83: " + str(row[2]))
            pdfOut.drawString(20,lineOffset-40,"Longitude_NAD83: " + str(row[3]))
            pdfOut.drawString(20,lineOffset-60,"State: " + row[4])
            if row[5] is None:
                pdfOut.drawString(20,lineOffset-80,"Elevation Meters: <NULL> ")
            else:
                pdfOut.drawString(20,lineOffset-80,"Elevation Meters: " + str(int(row[5])))
            pdfOut.drawString(20,lineOffset-100,"Slope Percent: " + str(row[6]))
            if row[7] is None:
                pdfOut.drawString(20,lineOffset-120,"Aspect Degrees: <NULL> ")
            else:
                pdfOut.drawString(20,lineOffset-120,"Aspect Degrees: " + row[7])
            pdfOut.drawString(20,lineOffset-140,"Landscape Type: " + str(row[8]))
            pdfOut.drawString(20,lineOffset-160,"Landscape Type Secondary: " + str(row[9]))
            # Added check here for NAs
            if row[10] is None:
                arcpy.AddWarning(pk + ' has erroneous EcolSite')
                pdfOut.drawString(20,lineOffset-180,"Ecological Site: <NULL>")
            else:
                pdfOut.drawString(20,lineOffset-180,"Ecological Site: " + row[10])
            #pdfOut.drawString(20,lineOffset-200,"Soil: " + str(row[11]))

            pdfOut.drawString(20,lineOffset-220,"Directions: ")
            # have to worry about long strings here
            lineOffset = lineOffset-240

            if row[12] is None:
                 pdfOut.drawString(30, lineOffset, "<NULL>")
            else:  # Adding encode here in case of wierd non-ascii characters
                for line in textwrap.wrap(text = str(row[12]), width = 80, drop_whitespace = True):
                    pdfOut.drawString(30, lineOffset, str(line))
                    lineOffset -= 20

    # Adding Revisit info here

    # assume directions are like 20 lines
    lineOffset = 200

    # Add check to see if df is empty
    if len(designPoints_df_pk) > 0 and designPoints_df_pk['Visit1PrimaryKey'].values[0] != 'NA':
        pdfOut.drawString(20, lineOffset - 20, "Visit Information:")
        pdfOut.drawString(20, lineOffset - 40, "Date Visited: " + str(designPoints_df_pk.DateVisited.values[0])[:10])
        pdfOut.drawString(20, lineOffset - 60,
                          "Visit 1 Primary Key: " + str(designPoints_df_pk.Visit1PrimaryKey.values[0]))

        designPoints_df_v1 = designPoints_df.loc[
            designPoints_df.Visit1PrimaryKey == designPoints_df_pk.Visit1PrimaryKey.values[0], ['PrimaryKey',
                                                                                                'DateVisited']]
        # get most recent date
        # make sure dates is date format first
        designPoints_df_v1['DateVisited'] = pd.to_datetime(designPoints_df_v1.DateVisited, errors='ignore')
        last_visit = designPoints_df_v1['DateVisited'].max()
        most_recent = designPoints_df_v1[designPoints_df_v1['DateVisited'] == last_visit]
        photo_pk = most_recent['PrimaryKey'].values[0]
    else:
        pdfOut.drawString(20, lineOffset, "No revisit information available")
        photo_pk = pk

    arcpy.RemoveJoin_management("terraLayer")
    arcpy.Delete_management("terraLayer")

    # end page 1
    pdfOut.showPage()

#----Page2
    # change font
    pdfOut.setFont("Helvetica", 14)
    # Print out the line info on Page 2
    # Just get PrimaryKey records
    whereClause = "PrimaryKey = '" + pk + "'"
    arcpy.MakeTableView_management(linesSDE, "linesLayer", whereClause)
    # Join lines to LPIHeader
    arcpy.AddJoin_management("linesLayer", "LineKey", lpiheaderSDE, "LineKey")

    fields = [linesFC + ".LineID", linesFC + ".LatitudeStart", linesFC + ".LongitudeStart", linesFC + ".LatitudeEnd", linesFC + ".LongitudeEnd", linesFC + ".Azimuth", lpiheaderFC + ".Direction", lpiheaderFC + ".LineLengthAmount", \
            lpiheaderFC + ".SpacingIntervalAmount", lpiheaderFC + ".SpacingType"]

    pdfOut.drawString(200,792,"Transect Information for " + plotID)
    with arcpy.da.SearchCursor("linesLayer", fields, sql_clause=(None, 'ORDER BY LineID')) as cursor:

        for row in cursor:
            # some plots have things like 1b in them
            if len(row[0]) > 1:
                continue # for plots that have both lineID of 1 and 1b this is causing errors
                # lets just SKIP them for now
            else:
                lineNum = row[0]

            lineOffset = 760 - (220 * (int(lineNum) - 1))
            pdfOut.drawString(20,lineOffset,"LineID: " + str(row[0]))
            pdfOut.drawString(20,lineOffset - 20,"Latitude Start: " + str(row[1]))
            pdfOut.drawString(20,lineOffset - 40,"Longitude Start: " + str(row[2]))
            pdfOut.drawString(20,lineOffset - 60,"Latitude End: " + str(row[3]))
            pdfOut.drawString(20,lineOffset - 80,"Longitude End: " + str(row[4]))
            pdfOut.drawString(20,lineOffset - 100,"Azimuth: " + str(row[5]))
            pdfOut.drawString(20,lineOffset - 120,"Direction: " + str(row[6]))
            pdfOut.drawString(20,lineOffset - 140,"Line Length Amount: " + str(row[7]))
            if row[8] is None:
                pdfOut.drawString(20,lineOffset - 160,"Spacing Interval Amount: <NULL>")
            else:
                pdfOut.drawString(20,lineOffset - 160,"Spacing Interval Amount: " + str(int(row[8])))
            pdfOut.drawString(20,lineOffset - 180,"Spacing Type: " + str(row[9]))

    arcpy.RemoveJoin_management("linesLayer")
    arcpy.Delete_management("linesLayer")
    # end page 2
    pdfOut.showPage()

#----Page3
    # change font
    pdfOut.setFont("Helvetica", 14)
    # Just get PrimaryKey records
    whereClause = "PrimaryKey = '" + pk + "'"
    arcpy.MakeTableView_management(soilhorSDE, "soilhorLayer", whereClause)
    # Join SoilPitHorizons to SoilPits
    arcpy.AddJoin_management("soilhorLayer", "SoilKey", soilpitsSDE, "SoilKey")

    fields = [soilpitsFC + ".SoilDepthLower", soilpitsFC + ".DepthMeasure", soilpitsFC + ".Notes", soilhorFC + ".Texture", soilhorFC + ".RockFragments", \
            soilhorFC + ".Effer", soilhorFC + ".HorizonDepthUpper", soilhorFC + ".HorizonDepthLower"]

    pdfOut.drawString(200,792,"Soil Pit Information for " + plotID)
    recCount = 1
    # need to worry about dups so added PK whereclause and need to order the horizons so added order by
    whereClause = soilpitsFC + ".PrimaryKey = '" + pk + "'"
    with arcpy.da.SearchCursor("soilhorLayer", fields, whereClause, sql_clause=(None, 'ORDER BY HorizonDepthUpper')) as cursor:
        for row in cursor:
            lineOffset = 680 - (20 * (recCount - 1))
            # Only need the Header info once
            if recCount == 1:
                if row[0]:
                    pdfOut.drawString(20,760,"Soil Pit Depth: " + str(int(row[0])))
                else:
                    pdfOut.drawString(20,760,"Soil Pit Depth: None")
                pdfOut.drawString(20,740,"Depth Unit:  " + row[1])
                pdfOut.drawString(20,720,"Notes: " + str(row[2]))
                pdfOut.drawString(20,700,"Soil Pit Horizons")
            pdfOut.drawString(20,lineOffset,"     Depth Upper: " + str(int(row[6] or 0)).rjust(2,' ') + "    Depth Lower: " + str(int(row[7] or 0)).rjust(2,' ') + "    Texture: " + str(row[3]) + "    Effer: " + str(row[5]) + "    Rock Fragments: " + str(int(row[4] or 0)))

            recCount += 1

    arcpy.RemoveJoin_management("soilhorLayer")
    arcpy.Delete_management("soilhorLayer")
    # end page 3
    pdfOut.showPage()

#--Page4 Species List from Species Ind
    # change font
    pdfOut.setFont("Helvetica", 14)
    # add loop here to get lists from all visits
    pdfOut.drawString(200,792,"Species List for " + plotID)
    lineOffset = 760
    fields = ["Species"]

    if len(designPoints_df_pk) > 0:
        for i in designPoints_df_v1['PrimaryKey']:
            whereClause = "PrimaryKey = '" + i + "'"
            speciesList = ""

            # Get a list of species
            with arcpy.da.SearchCursor(specindSDE, fields, whereClause) as cursor:
               for row in cursor:
                if row[0] is None:
                    pdfOut.drawString(20,lineOffset,"Species List: <NULL>") # when theres no species list just print "<NULL>" on this page
                    pdfOut.showPage()
                else:
                    speciesList = speciesList + row[0] + ', '

            # remove trailing , to be fancy
            speciesList = speciesList[:-2]

            pdfOut.drawString(20,lineOffset,("Species List for "+ i + ":"))
            # have to worry about long strings here
            lineOffset = lineOffset-20
            for line in textwrap.wrap(speciesList, 70):
                pdfOut.drawString(30, lineOffset, str(line))
                lineOffset -= 20
            lineOffset -= 200
    else:
        whereClause = "PrimaryKey = '" + pk + "'"
        speciesList = ""
        # Get a list of species
        with arcpy.da.SearchCursor(specindSDE, fields, whereClause) as cursor:
            for row in cursor:
                if row[0] is None:
                    pdfOut.drawString(20, lineOffset,
                                      "Species List: <NULL>")  # when theres no species list just print "<NULL>" on this page
                    pdfOut.showPage()
                else:
                    speciesList = speciesList + row[0] + ', '

        # remove trailing , to be fancy
        speciesList = speciesList[:-2]

        pdfOut.drawString(20, lineOffset, "Species List: ")
        # have to worry about long strings here
        lineOffset = lineOffset - 20
        for line in textwrap.wrap(speciesList, 81):
            pdfOut.drawString(30, lineOffset, str(line))
            lineOffset -= 20


    # end page 4
    pdfOut.showPage()

#---Page5 and on
    # Grad the images and add all of them.  Easier to use file path than URL
    photoPath = os.path.join(photosDir, photoState, photoKey)

    # If the photo directory doesnt exist, create one

    if not os.path.exists(photoPath):
        fields = ['PrimaryKey', 'PlotID','ProjectName','SpeciesState']
        whereClause = "PrimaryKey = '" + photo_pk + "'"

        with arcpy.da.SearchCursor(terraSDE, fields, whereClause) as cursor:
            for row in cursor:
                missing_photos.append(row[0])
                missing_ids.append(row[1])
                missing_project.append(row[2])
                missing_state.append(row[3])

        arcpy.AddWarning(photoPath + "- Photo path does not exist")
        pdfOut.showPage()
        ## Add a line here to create folder in \\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Data\Development\Terrestrial\ImageStaging
    else:
        photoLinks = os.listdir(photoPath)
        for photo in photoLinks:
            arcpy.AddMessage("Photo " + photo)
            if photo.endswith(".jpg") or photo.endswith(".JPG"):
                #im = Image.open(photoPath + "\\" + photo)
                #width, height = im.size
                #pdfOut.drawImage(photoPath + "\\" + photo, width/4*inch, height/4*inch, width/2*inch, height/2*inch, mask='auto', preserveAspectRatio=True, anchor='c')
                fill_page_with_image(photoPath + "\\" + photo, pdfOut)
                # Add photo name
                pdfOut.drawString(200, 792, photo) # hopefully adding this after photo will put it on top?
            # end the page
            pdfOut.showPage()
    arcpy.Delete_management("designLayer")
    # Save the pdf
    pdfOut.save()

# make a report for each LMF PrimaryKey
for pk in lmfpkList:

    #pdfOut = canvas.Canvas(outputFolder + "\\" + "Revisit Report for " + pk + ".pdf")

    arcpy.AddMessage("Building Revisit Report for " + pk)

    # Join to get
    arcpy.MakeFeatureLayer_management(lmfterraSDE, "lmfLayer")
    arcpy.AddJoin_management("lmfLayer", "PrimaryKey", lmfplotsSDE, "PrimaryKey")

    # adding one more join to pull in elevation
    arcpy.AddJoin_management("lmfLayer", "PrimaryKey", gpsSDE, "PrimaryKey")

    fields = [lmfterraFC + '.PrimaryKey', lmfterraFC + '.PlotID', lmfterraFC + '.Latitude_NAD83', lmfterraFC + '.Longitude_NAD83', lmfterraFC + ".State", lmfplotsFC + ".SLOPE_PERCENT", \
            lmfplotsFC + ".SLOPE_ASPECT", lmfterraFC + ".EcologicalSiteId", lmfplotsFC + ".COMPONENT_NAME", lmfplotsFC + ".PSU", lmfplotsFC + ".POINT", lmfplotsFC + ".SURVEY", lmfplotsFC + ".STATE", lmfplotsFC + ".COUNTY", gpsFC + ".ELEVATION"]
    whereClause = lmfterraFC + ".PrimaryKey = '" + pk + "'"

    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor("lmfLayer", fields, whereClause) as cursor:
        for row in cursor:
            # Adding a check for wierd characters in plot ID (e.g. "/")
            # import re
            # re.sub("/", "_", row[1])
            # it doesnt quite work yet

            # Start the PDF
            pdfOut = canvas.Canvas(os.path.join(outputFolder,("Revisit Report for " + row[1] + ".pdf")))
            # grad for photo part later

            # need to add leading zeros to state/county if they arent there already
            photoState = str(row[12]).zfill(2)
            photoCounty = str(row[13]).zfill(3)

            photoKey = photoState + photoCounty

            photoPSU = str(row[9])
            photoYear = str(row[11])
            photoPoint = 'point' + str(row[10])

            plotID = row[1]

            lineOffset = 760
            pdfOut.drawString(200,792,"Revist report for PlotID " + row[1])
            pdfOut.drawString(20,lineOffset,"PrimaryKey: " + row[0])
            pdfOut.drawString(20,lineOffset-20,"Latitude_NAD83: " + str(row[2]))
            pdfOut.drawString(20,lineOffset-40,"Longitude_NAD83: " + str(row[3]))
            pdfOut.drawString(20,lineOffset-60,"State: " + row[4])
            pdfOut.drawString(20,lineOffset-80,"Elevation Feet: " + str(int(row[14])))
            pdfOut.drawString(20,lineOffset-100,"Slope Percent: " + str(row[5]))
            pdfOut.drawString(20,lineOffset-120,"Aspect: " + row[6])

            # Added check here for NAs
            if row[8] is None:
                arcpy.AddWarning(pk + ' has erroneous EcolSite')
                pdfOut.drawString(20,lineOffset-180,"EcolSite: <NULL>")
            else:
                pdfOut.drawString(20,lineOffset-180,"EcolSite: " + row[7])
            pdfOut.drawString(20,lineOffset-200,"Soil: " + str(row[8]))

    # end page 1
    pdfOut.showPage()

#----Page2
    # Just get PrimaryKey records
    whereClause = "PrimaryKey = '" + pk + "'"
    arcpy.MakeTableView_management(lmfsoilhorSDE, "soilhorLayer", whereClause)

    fields = ["DEPTH", "HORIZON_TEXTURE", "TEXTURE_MODIFIER","EFFERVESCENCE_CLASS"]

    pdfOut.drawString(200,792,"Revist report for PlotID " + plotID)
    recCount = 1
    # need to worry about dups so added PK whereclause and need to order the horizons so added order by
    whereClause = "PrimaryKey = '" + pk + "'"
    with arcpy.da.SearchCursor("soilhorLayer", fields, whereClause, sql_clause=(None, 'ORDER BY DEPTH')) as cursor:
        for row in cursor:
            lineOffset = 680 - (20* (recCount-1))
            pdfOut.drawString(20,lineOffset,"     Depth (inches): " + str(int(row[0] or 0)).rjust(2,' ') + "     Texture: " + str(row[1]) + "    Effer: " + str(row[3]) + "    Texture Modifier: " + str(row[2] or 0))
            recCount += 1

    arcpy.Delete_management("soilhorLayer")
    # end page 3
    pdfOut.showPage()

#--Page3 Species List from Species Ind
    pdfOut.drawString(200,792,"Revist report for PlotID " + plotID)
    lineOffset = 760
    fields = ["Species"]
    whereClause = "PrimaryKey = '" + pk + "'"
    speciesList = ""

    # Get a list of species
    with arcpy.da.SearchCursor(lmfspecindSDE, fields, whereClause) as cursor:
       for row in cursor:
        if row[0] is None:
            pdfOut.drawString(20,lineOffset,"Species List: <NULL>") # when theres no species list just print "<NULL>" on this page
            pdfOut.showPage()
        else:
            speciesList = speciesList + row[0] + ', '

    # remove trailing , to be fancy
    speciesList = speciesList[:-2]

    pdfOut.drawString(20,lineOffset,"Species List: ")
    # have to worry about long strings here
    lineOffset = lineOffset-20
    for line in textwrap.wrap(speciesList, 81):
        pdfOut.drawString(30, lineOffset, str(line))
        lineOffset -= 20

    # end page 4
    pdfOut.showPage()

    arcpy.RemoveJoin_management("lmfLayer")
    arcpy.Delete_management("lmfLayer")

#---Page5 and on
    # Grad the images and add all of them.  Easier to use file path than URL
    photoPath = LMFphotosDir + "\\" + photoKey + "\\" + photoPSU + "\\" + photoPoint + "\\" + photoYear

    # If the photo directory doesnt exist, create one
    import os
    if not os.path.exists(photoPath):
        fields = ['PrimaryKey', 'PlotID','ProjectName','SpeciesState']
        whereClause = "PrimaryKey = '" + pk + "'"

        with arcpy.da.SearchCursor(lmfterraSDE, fields, whereClause) as cursor:
            for row in cursor:
                missing_photos.append(row[0])
                missing_ids.append(row[1])
                missing_project.append(row[2])
                missing_state.append(row[3])

        arcpy.AddMessage(photoPath)
        arcpy.AddWarning(photoPath + "Photo path does not exist")
        pdfOut.showPage()
    else:
        photoLinks = os.listdir(photoPath)
        for photo in photoLinks:
            arcpy.AddMessage("Photo " + photo)
            if photo.endswith(".jpg") or photo.endswith(".JPG"):
                #im = Image.open(photoPath + "\\" + photo)
                #width, height = im.size
                #pdfOut.drawImage(photoPath + "\\" + photo, width/4*inch, height/4*inch, width/2*inch, height/2*inch, mask='auto', preserveAspectRatio=True, anchor='c')
                fill_page_with_image(photoPath + "\\" + photo, pdfOut)
            # end the page
            pdfOut.showPage()

    # Save the pdf
    pdfOut.save()

dict = {'PrimaryKey':missing_photos, 'PlotID':missing_ids, 'ProjectName':missing_project, 'State':missing_state}
df = pd.DataFrame(dict)
# Add plot id, project name and species state on here

df.to_csv(path_or_buf = os.path.join(outputFolder, 'missing_photos.csv'),header = True, index = False) # copy this to \\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Data\Development\Terrestrial\ImageStaging

arcpy.AddMessage("All Done")
