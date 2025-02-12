library(httr2)
library(tidyverse)
library(nhdplusTools)
library(sf)
library(spData)
library(mapview)

# --------------------------------------------------------------------------------------------------------
# ------------------------- Define parameters for Climate Engine API -------------------------------------

# Define root url for Climate Engine API
root_url <- 'https://api.climateengine.org/'

# Define key
# Temporary key set up for testing
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzk0MjYzOCwianRpIjoiODE0YjQwYzEtMWQ4ZS00YjBlLWExNDAtYzk1ZjVhZGZlZmI1IiwibmJmIjoxNzMzOTQyNjM4LCJ0eXBlIjoiYWNjZXNzIiwic3ViIjoidUZXM0VmMUxhWmI5U0VhUnRPdzVNUzI2UjBTMiIsImV4cCI6MTczNjUzNDYzOCwicm9sZXMiOiJ1c2VyIiwidXNlcl9pZCI6InVGVzNFZjFMYVpiOVNFYVJ0T3c1TVMyNlIwUzIifQ.x8b-wfCmX906kuwm04iMbYyQhOLazYxxaUQnIgQPFVk'

# --------------------------------------------------------------------------------------------------------
# ---------------------- Confirm authentication for Climate Engine API -----------------------------------

# Define endpoint
endpoint = '/home/key_expiration'

# Run simple endpoint to get key expiration and print result
test <- request(base_url = paste0(root_url, endpoint)) |>
  req_headers(Authorization = key) |>
  req_perform()
print(resp_raw(test))
rm(test, endpoint)

# --------------------------------------------------------------------------------------------------------
# ----------------------- Get HUC10 AOI and parse coordinates as string ----------------------------------

# Get HUC10s for Colorado
data(us_states)
aoi <- us_states |>
  filter(NAME == 'Colorado')
aoi_hucs <- get_huc(aoi, type = 'huc10')

# Get a single HUC ID
aoi_huc_id <- aoi_hucs$huc10[10]

# Subset a single HUC10 and visualize location
huc <- aoi_hucs |> filter(huc10 == aoi_huc_id)

# Simplify the geometry 
# NOTE: This is only temporarily necessary because of a technical issue we are working on
huc <- huc |>
  st_simplify(preserveTopology = TRUE, dTolerance = 10)
mapview(huc)

# Function to convert a single geometry to the desired character string format
convert_sf_geometry_to_string <- function(sf_object) {
  
  # Parse geometry
  geometry <- st_geometry(sf_object)[[1]]
  
  # Extract coordinates as a matrix
  coords <- st_coordinates(geometry)
  
  # Format each coordinate pair as a string
  coords_list <- apply(coords, 1, function(row) {
    sprintf("[%f,%f]", row[1], row[2])  # Format each coordinate pair as [longitude,latitude]
  })
  
  # Combine into a single string representing the polygon
  sprintf("[[%s]]", paste(coords_list, collapse = ","))
}

# Apply the function to parse coordinates string
coords_string <- convert_sf_geometry_to_string(huc)[[1]]
rm(convert_sf_geometry_to_string)

# --------------------------------------------------------------------------------------------------------
# ---------------- Make reports/site_characterization request to Climate Engine API ----------------------

# Climate Engine endpoint for the reports
endpoint <- '/custom/reports/site_characterization' 

# Generate list of parameters for API request
params = list(
  user_email = 'eric.jensen@dri.edu', # Standard email address
  site_name = huc$name |> unlist(), # Pass HUC name as site_name; limit 35 characters
  site_type = 'HUC10 Watershed', # Limit 50 characters
  site_description = 'Report for Watershed Condition Assessment', # Limit 50 characters
  mask_ownership = 'BLM', # Select one from ['None', 'BIA', 'BLM', 'DOD', 'FWS', 'NPS', 'USFS']
  mask_landcover = 'True', # Boolean
  coordinates = coords_string # Formatted coordinate string, documentation here: https://support.climateengine.org/article/152-formatting-coordinates-for-api-requests?preview=67044393eb6616597e5673a2
  # geometry_type = 'Polygon' # User needs to pass geometry_type as either "Polygon" or "MultiPolygon"
)

# Pass request to return HTML as a character string
response <- request(base_url = paste0(root_url, endpoint)) |>
  req_url_query(query = !!!params) |>
  req_headers(Authorization = key) |>
  # req_method("POST")|>
  req_perform() |>
  resp_body_json()
print(response)
