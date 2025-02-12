#-------------------------------------------------------------------------------
# Name:        Revist Report for Terra with Species List.py
# Purpose:
#   Using ReportLab and PIL to create a PDF Plot Revisit report for each PrimaryKey given
#   in a txt file
#
# Author:      dbrowning, alaurencetraynor
#
# Created:     7/8/2020
# Modified:    10/30/2024
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
outputFolder = r"T:\ProjectsNational\AIM\Data\Development\Reports\Revisit\CO 2024\CO_AIMt_2024_revisits\CRFO"
pkFile = r"T:\ProjectsNational\AIM\Data\Development\Reports\Revisit\CO 2024\CO_AIMt_2024_revisits\CO_CRVFO_2024_revisits.txt"

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
        raise ValueError("Unsupported image orientation '%s'."
                         % ORIENTATIONS[orientation])

    if image_width > image_height:
        page_width, page_height = page_height, page_width  # flip width/height
        draw_width, draw_height = draw_height, draw_width
        canvas.setPageSize((page_width, page_height))

    canvas.drawImage(path, 0, 0, width=draw_width, height=draw_height,
                     preserveAspectRatio=True)

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


    # adding one more join to pull in elevation
    arcpy.AddJoin_management("terraLayer", "PrimaryKey", gpsSDE, "PrimaryKey")

    fields = [terraFC + '.PrimaryKey', terraFC + '.PlotID', terraFC + '.Latitude_NAD83', terraFC + '.Longitude_NAD83', terraFC + ".State", plotsFC + ".SLOPE_PERCENT", \
            plotsFC + ".SLOPE_ASPECT", terraFC + ".EcologicalSiteId", plotsFC + ".COMPONENT_NAME", plotsFC + ".PSU", plotsFC + ".POINT", plotsFC + ".SURVEY", plotsFC + ".STATE", plotsFC + ".COUNTY", gpsFC + ".ELEVATION"]
    whereClause = terraFC + ".PrimaryKey = '" + pk + "'"



    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor("terraLayer", fields, whereClause) as cursor:
        for row in cursor:
            # Adding a check for wierd characters in plot ID (e.g. "/")
            # import re
            # re.sub("/", "_", row[1])
            # it doesnt quite work yet

            # Start the PDF
            pdfOut = canvas.Canvas(outputFolder + "\\" + "Revisit Report for " + row[1] + ".pdf")
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
                print(pk + ' has erroneous EcolSite')
                pdfOut.drawString(20,lineOffset-180,"EcolSite: <NULL>")
            else:
                pdfOut.drawString(20,lineOffset-180,"EcolSite: " + row[7])
            pdfOut.drawString(20,lineOffset-200,"Soil: " + str(row[8]))

    # end page 1
    pdfOut.showPage()

#----Page2
    # Just get PrimaryKey records
    whereClause = "PrimaryKey = '" + pk + "'"
    arcpy.MakeTableView_management(soilhorSDE, "soilhorLayer", whereClause)

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

    #---Page5
    # Indicators for review here
    pdfOut.drawString(200,792,"Standard 1: Terradat Indicators for PlotID " + plotID)

        # adding additional indicators here requested by MK for reference review
    fields = ['AH_NonNoxPerenGrassCover', 'AH_NonNoxAnnGrassCover', 'AH_NonNoxShrubCover'\
            , 'AH_NonNoxSubShrubCover', 'AH_NoxPerenGrassCover', 'AH_NoxAnnGrassCover', 'AH_TallPerenGrassCover',  'AH_ShortPerenGrassCover', 'AH_SagebrushCover', 'AH_NonSagebrushShrubCover'\
            , 'Spp_Sagebrush', 'Spp_TallPerenGrass', 'Spp_ShortPerenGrass', 'Spp_Nox']

    whereClause = "PrimaryKey = '" + pk + "'"

    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor(terraSDE, fields, whereClause) as cursor:
        for row in cursor:

            lineOffset = 760
            pdfOut.drawString(20,lineOffset,"Non-Noxious Perennial Grass Cover: " + str(row[0]))
            pdfOut.drawString(20,lineOffset-20,"Non-Noxious Annual Grass Cover: " + str(row[1]))
            pdfOut.drawString(20,lineOffset-40,"Non-Noxious Shrub Cover: " + str(row[2]))
            pdfOut.drawString(20,lineOffset-60,"Non-Noxious Sub-Shrub Cover: " + str(row[3]))
            pdfOut.drawString(20,lineOffset-80,"Noxious Perennial Grass Cover: " + str(int(row[4])))
            pdfOut.drawString(20,lineOffset-100,"Noxious Annual Grass Cover: " + str(row[5]))
            pdfOut.drawString(20,lineOffset-120,"Tall Perennial Grass Cover: " + str(row[6]))
            pdfOut.drawString(20,lineOffset-140,"Short Perennial Grass Cover: " + str(row[7]))
            pdfOut.drawString(20,lineOffset-160,"Sagebrush Cover: " + str(row[8]))
            pdfOut.drawString(20,lineOffset-180,"Non-Sagebrush Shrub Cover: " + str(row[9]))
            pdfOut.drawString(20,lineOffset-200,"Sagebrush Species: " + str(row[10]))
            pdfOut.drawString(20,lineOffset-220,"Tall Perennial Grass Species: "+ str(row[11]))
            pdfOut.drawString(20,lineOffset-240,"Short Perennial Grass Species: "+ str(row[12]))
            pdfOut.drawString(20,lineOffset-260,"Noxious Species: "+ str(row[13]))

    # end page 5
    pdfOut.showPage()

    #---Page6
    # Indicators for review here
    pdfOut.drawString(200,792,"Standard 3 and 5: Terradat Indicators for PlotID " + plotID)

    fields = ['AH_NonNoxPerenForbCover', 'AH_NonNoxAnnForbCover', 'AH_NoxPerenForbCover'\
            , 'AH_NoxAnnForbCover', 'AH_PreferredForbCover', 'Spp_PreferredForb']
    whereClause = "PrimaryKey = '" + pk + "'"

    # Print the Summary Info on Page 1
    with arcpy.da.SearchCursor(terraSDE, fields, whereClause) as cursor:
        for row in cursor:

            lineOffset = 760
            pdfOut.drawString(20,lineOffset,"Non-Noxious Perennial Forb Cover: " + str(row[0]))
            pdfOut.drawString(20,lineOffset-20,"Non-Noxious Annual Forb Cover: " + str(row[1]))
            pdfOut.drawString(20,lineOffset-40,"Noxious Perennial Forb Cover: " + str(row[2]))
            pdfOut.drawString(20,lineOffset-60,"Noxious Annual Forb: " + str(row[3]))
            pdfOut.drawString(20,lineOffset-80,"Preferred Forb Cover: " + str(int(row[4])))
            pdfOut.drawString(20,lineOffset-100,"Preferred Forb Species: " + str(row[5]))

    arcpy.RemoveJoin_management("terraLayer")
    arcpy.Delete_management("terraLayer")

    # end page 6
    pdfOut.showPage()

#---Page7 and on
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
        pdfOut.showPage()
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
df.to_csv(path_or_buf = outputFolder + '/' + 'missing_photos_lmf.csv',header = False, index = False)

print("All Done")
