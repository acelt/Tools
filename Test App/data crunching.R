 # setup
library(elevatr)
library(sf)
library(terra)
library(soilDB)

# test gdb
gdb <-  "C:\\Users\\alaurencetraynor\\Documents\\Tools\\CO Elevation\\elevation test\\elevation test.gdb"

# test poly
polyname <- "testpoly"
polypath <-  paste0(gdb,"/","polyname")

# import
poly <- sf::st_read(dsn = gdb,
                    layer = polyname)

plot(poly$Shape)

## get data
# get elevation raster for poly aoi
elevation_raster <- get_elev_raster(locations = poly,
                                    z = 14)
# get map unit keys and ecoclass data
mu <- mukey.wcs(aoi = poly, db = 'gssurgo', res = 30)

# need error check for empty soil survey

# soil maps - parent material and depth to bedrock/rock outcrop units

# maybe just use ssurgo?
# may want to do this state by state tpo speed things/start with an even smaller test area

# slope/prominance

# public land - to mask out private rocks

# locations of existing crags - use mtn project api - to train data

# prediction map - asses to type boulder/route and given a probability of success/calssify