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
# added for ArcPro to get ReportLab
import sys
reportlabPath = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Data\Software\ReportLab for Python 3"
sys.path.append(reportlabPath)

from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm, inch, pica
from PIL import Image
import arcpy, os, textwrap
import pandas as pd

# Setup your paths here!!
sdeConn = r"\\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\AIMDataTools\SDE\AIMTerrestrialPub.sde"
photosDir = r"\\blm.doi.net\dfs\loc\EGIS\ReferenceNational\environment\BLM_AIM\TerrADat"
outputFolder = r"C:\Users\alaurencetraynor\Documents\Revisit Reports\CA"
pkFile = r"C:\Users\alaurencetraynor\Documents\Revisit Reports\CA\BishopFOrevisitreports.txt"

# create empty lists to fill with missing photo pks and info
missing_photos = []
missing_ids = []
missing_project = []
missing_state = []

# Using Pub SDE
terraFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.TerrADat"
terraSDE = sdeConn + "\\" + terraFC
photoFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblTerraDatPhotoLinks"
photoSDE = sdeConn + "\\" + photoFC
linesFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblLines"
linesSDE = sdeConn + "\\" + linesFC
lpiheaderFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblLPIHeader"
lpiheaderSDE = sdeConn + "\\" + lpiheaderFC
plotsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblPlots"
plotsSDE = sdeConn + "\\" + plotsFC
soilpitsFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblSoilPits"
soilpitsSDE = sdeConn + "\\" + soilpitsFC
soilhorFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblSoilPitHorizons"
soilhorSDE = sdeConn + "\\" + soilhorFC
specindFC = "ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.TerrADatSpeciesIndicators"
specindSDE = sdeConn + "\\" + specindFC

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




# Get a list of PrimaryKeys from a supplied text file
pkFileLink = open(pkFile, 'r')
pkList = pkFileLink.read().splitlines()
pkFileLink.close()
#Test PK 18112809100042272018-09-01
#pkList = ["13072013104551182013-09-01"]

# make a report for each PrimaryKey
for pk in pkList:

    #pdfOut = canvas.Canvas(outputFolder + "\\" + "Revisit Report for " + pk + ".pdf")

    print("Building Revisit Report for " + pk)

    # Join to get
    arcpy.MakeFeatureLayer_management(terraSDE, "terraLayer")
    arcpy.AddJoin_management("terraLayer", "PrimaryKey", plotsSDE, "PrimaryKey")

    # Adding in V2 plot ID here as well
    # this will eventually be from the SDD but for now its a spreadsheet from the FO
    v2_table = r'C:\Users\alaurencetraynor\Documents\Revisit Reports\CA\v2_table.csv'
    arcpy.AddJoin_management("terraLayer", "PrimaryKey", v2_table, "V1PrimaryKey")

    fields = [terraFC + '.PrimaryKey', terraFC + '.PlotID', terraFC + '.Latitude_NAD83', terraFC + '.Longitude_NAD83', terraFC + ".State", plotsFC + ".Elevation", plotsFC + ".Slope", \
            plotsFC + ".Aspect", plotsFC + ".LandscapeType", plotsFC + ".LandscapeTypeSecondary", plotsFC + ".EcolSite", plotsFC + ".Soil", plotsFC + ".Directions",  "v2_table.csv.V2PlotID"]
    whereClause = terraFC + ".PrimaryKey = '" + pk + "'"

    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor("terraLayer", fields, whereClause) as cursor:
        for row in cursor:
            # Adding a check for wierd characters in plot ID (e.g. "/")
            # import re
            # re.sub("/", "_", row[1])
            # it doesnt quite work yet

            # Start the PDF
            pdfOut = canvas.Canvas(outputFolder + "\\" + "Revisit Report for " + str(row[13]) + ".pdf")
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
            pdfOut.drawString(200,792,"Revist report for PlotID " + row[1])
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
            pdfOut.drawString(20,lineOffset-140,"LandscapeType: " + str(row[8]))
            pdfOut.drawString(20,lineOffset-160,"LandscapeTypeSecondary: " + str(row[9]))
            # Added check here for NAs
            if row[10] is None:
                print(pk + ' has erroneous EcolSite')
                pdfOut.drawString(20,lineOffset-180,"EcolSite: <NULL>")
            else:
                pdfOut.drawString(20,lineOffset-180,"EcolSite: " + row[10])
            pdfOut.drawString(20,lineOffset-200,"Soil: " + str(row[11]))
            pdfOut.drawString(20,lineOffset-220,"Directions: ")
            # have to worry about long strings here
            lineOffset = lineOffset-240


            if row[12] is None:
                 pdfOut.drawString(30, lineOffset, "<NULL>")
            else:  # Adding encode here in case of wierd non-ascii characters
                for line in textwrap.wrap(text = str(row[12]), width = 90, drop_whitespace = True):
                    pdfOut.drawString(30, lineOffset, str(line))
                    lineOffset -= 20

    arcpy.RemoveJoin_management("terraLayer")
    arcpy.Delete_management("terraLayer")
    # end page 1
    pdfOut.showPage()

#----Page2
    # Print out the line info on Page 2
    # Just get PrimaryKey records
    whereClause = "PrimaryKey = '" + pk + "'"
    arcpy.MakeTableView_management(linesSDE, "linesLayer", whereClause)
    # Join lines to LPIHeader
    arcpy.AddJoin_management("linesLayer", "LineKey", lpiheaderSDE, "LineKey")

    fields = [linesFC + ".LineID", linesFC + ".LatitudeStart", linesFC + ".LongitudeStart", linesFC + ".LatitudeEnd", linesFC + ".LongitudeEnd", linesFC + ".Azimuth", lpiheaderFC + ".Direction", lpiheaderFC + ".LineLengthAmount", \
            lpiheaderFC + ".SpacingIntervalAmount", lpiheaderFC + ".SpacingType"]

    pdfOut.drawString(200,792,"Revist report for PlotID " + pk)
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
            pdfOut.drawString(20,lineOffset - 20,"LatitudeStart: " + str(row[1]))
            pdfOut.drawString(20,lineOffset - 40,"LongitudeStart: " + str(row[2]))
            pdfOut.drawString(20,lineOffset - 60,"LatitudeEnd: " + str(row[3]))
            pdfOut.drawString(20,lineOffset - 80,"LongitudeEnd: " + str(row[4]))
            pdfOut.drawString(20,lineOffset - 100,"Azimuth: " + str(row[5]))
            pdfOut.drawString(20,lineOffset - 120,"Direction: " + str(row[6]))
            pdfOut.drawString(20,lineOffset - 140,"LineLengthAmount: " + str(row[7]))
            if row[8] is None:
                pdfOut.drawString(20,lineOffset - 160,"SpacingIntervalAmount: <NULL>")
            else:
                pdfOut.drawString(20,lineOffset - 160,"SpacingIntervalAmount: " + str(int(row[8])))
            pdfOut.drawString(20,lineOffset - 180,"SpacingType: " + str(row[9]))

    arcpy.RemoveJoin_management("linesLayer")
    arcpy.Delete_management("linesLayer")
    # end page 2
    pdfOut.showPage()

#----Page3
    # Just get PrimaryKey records
    whereClause = "PrimaryKey = '" + pk + "'"
    arcpy.MakeTableView_management(soilhorSDE, "soilhorLayer", whereClause)
    # Join SoilPitHorizons to SoilPits
    arcpy.AddJoin_management("soilhorLayer", "SoilKey", soilpitsSDE, "SoilKey")

    fields = [soilpitsFC + ".SoilDepthLower", soilpitsFC + ".DepthMeasure", soilpitsFC + ".Notes", soilhorFC + ".Texture", soilhorFC + ".RockFragments", \
            soilhorFC + ".Effer", soilhorFC + ".HorizonDepthUpper", soilhorFC + ".HorizonDepthLower"]

    pdfOut.drawString(200,792,"Revist report for PlotID " + plotID)
    recCount = 1
    # need to worry about dups so added PK whereclause and need to order the horizons so added order by
    whereClause = soilpitsFC + ".PrimaryKey = '" + pk + "'"
    with arcpy.da.SearchCursor("soilhorLayer", fields, whereClause, sql_clause=(None, 'ORDER BY HorizonDepthUpper')) as cursor:
        for row in cursor:
            lineOffset = 680 - (20 * (recCount - 1))
            # Only need the Header info once
            if recCount == 1:
                if row[0]:
                    pdfOut.drawString(20,760,"SoilDepthLower: " + str(int(row[0])))
                else:
                    pdfOut.drawString(20,760,"SoilDepthLower: None")
                pdfOut.drawString(20,740,"DepthMeasure:  " + row[1])
                pdfOut.drawString(20,720,"Notes: " + str(row[2]))
                pdfOut.drawString(20,700,"Soil Pit Horizons")
            pdfOut.drawString(20,lineOffset,"     Depth Upper: " + str(int(row[6] or 0)).rjust(2,' ') + "    Depth Lower: " + str(int(row[7] or 0)).rjust(2,' ') + "    Texture: " + str(row[3]) + "    Effer: " + str(row[5]) + "    Rock Fragments: " + str(int(row[4] or 0)))

##            pdfOut.drawString(20,lineOffset - 40,"LongitudeStart: " + str(row[2]))
##            pdfOut.drawString(20,lineOffset - 60,"LatitudeEnd: " + str(row[3]))
##            pdfOut.drawString(20,lineOffset - 80,"LongitudeEnd: " + str(row[4]))
##            pdfOut.drawString(20,lineOffset - 100,"Azimuth: " + str(row[5]))
##            pdfOut.drawString(20,lineOffset - 120,"Direction: " + row[6])
##            pdfOut.drawString(20,lineOffset - 140,"LineLengthAmount: " + str(row[7]))
##            pdfOut.drawString(20,lineOffset - 160,"SpacingIntervalAmount: " + str(row[8]))
##            pdfOut.drawString(20,lineOffset - 180,"SpacingType: " + row[9])

            recCount += 1

    arcpy.RemoveJoin_management("soilhorLayer")
    arcpy.Delete_management("soilhorLayer")
    # end page 3
    pdfOut.showPage()

#--Page4 Species List from Species Ind
    pdfOut.drawString(200,792,"Revist report for PlotID " + pk)
    lineOffset = 760
    fields = ["Species"]
    whereClause = "PrimaryKey = '" + pk + "'"
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

    pdfOut.drawString(20,lineOffset,"Species List: ")
    # have to worry about long strings here
    lineOffset = lineOffset-20
    for line in textwrap.wrap(speciesList, 81):
        pdfOut.drawString(30, lineOffset, str(line))
        lineOffset -= 20

    # end page 4
    pdfOut.showPage()

#---Page5 and on
    # Grad the images and add all of them.  Easier to use file path than URL
    photoPath = photosDir + "\\" + photoState + "\\" + photoKey


    # If the photo directory doesnt exist, create one

    if not os.path.exists(photoPath):
        fields = ['PrimaryKey', 'PlotID','ProjectName','SpeciesState']
        whereClause = "PrimaryKey = '" + pk + "'"

        with arcpy.da.SearchCursor(terraSDE, fields, whereClause) as cursor:
            for row in cursor:
                missing_photos.append(row[0])
                missing_ids.append(row[1])
                missing_project.append(row[2])
                missing_state.append(row[3])

        print("Photo path does not exist")
        pdfOut.showPage()
        ## Add a line here to create folder in \\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Data\Development\Terrestrial\ImageStaging
    else:
        photoLinks = os.listdir(photoPath)
        for photo in photoLinks:
            print("Photo " + photo)
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

df.to_csv(path_or_buf = outputFolder + '/' + 'missing_photos.csv',header = True, index = False) # copy this to \\blm.doi.net\dfs\loc\EGIS\ProjectsNational\AIM\Data\Development\Terrestrial\ImageStaging

print("All Done")
