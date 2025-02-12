library(jsonlite)
library(tidyverse)
library(arcgis)
library(arcgisbinding)
arc.check_product()
library(leaflet)
library(leaflet.extras)

# pull in map of MLRAs
# mlra_url <-  "https://services.arcgis.com/SXbDpmb7xQkk44JV/arcgis/rest/services/Major_Land_Resource_Areas/FeatureServer/0"
# mlra_fc <- arc_open(mlra_url)
# mlra_df <- arc_select(mlra_fc)

### Script to pull out reference sheet infor from EDIT using MLRA ###
 
# Specify the Major Land Resource Area
# make this into a funciton so we can loop through
grab_referencesheets <- function(mlra, out_path = wd()){
  
  base.url <- paste0("https://edit.jornada.nmsu.edu/services")
  
  # get list of all ESDs in the MLRA
  # try to catch the 404 error when the MLRA doesnt exisit in EDIT
  classlist <- jsonlite::fromJSON(paste0(base.url, "/downloads/esd/", mlra, "/class-list.json"))
  
  ecoclasses <- as.data.frame(classlist$ecoclasses)
  
  esd.url <- paste0(base.url, "/descriptions/esd/", mlra)
  
  # Make a list of all the data frames for the ecoclasses IDs
  doc.url.list <- lapply(X = ecoclasses$id, FUN = function(X) {
    jsonlite::fromJSON(paste0(esd.url, "/", X, "/reference-sheet.json"))
  })
  
  ref_sheet_list <- list()
  
  # We can coerce this to a data.frame
  for(i in 1:length(doc.url.list)){
    ref_sheet_list[[i]] <- as.data.frame(doc.url.list[[i]][["referenceSheet"]][["narratives"]])
    ref_sheet_list[[i]]$littercover <- doc.url.list[[i]][["referenceSheet"]][["litterCover"]]
    ref_sheet_list[[i]]$littercover <- doc.url.list[[3]][["referenceSheet"]][["litterDepth"]]
    ref_sheet_list[[i]]$compositionMetric <-doc.url.list[[i]][["referenceSheet"]][["compositionMetric"]]
  }
  
  final_data <- do.call(rbind, ref_sheet_list)
  
  # add the ESD to this
  final_data$EcologicalSite <- ecoclasses$id
  
  # we may want to add some of the metadata items to this table to?
  # litter cover composition metric and litter depth are separate and should be included
  # perhaps the author/approver too?
  
  # Then write it to a flat csv file
  write.csv(final_data, paste0(out_path, mlra, "_final_data.csv"))
  
}

# relevant mlras for norcal include 023x, 021x,026x maybe a lil of 027x
mlra <- "023X"
out_path <- "\\\\blm.doi.net\\dfs\\nr\\users\\alaurencetraynor\\My Documents\\Analysis\\Tools\\EDIT API\\"

grab_referencesheets(mlra = mlra,
                     out_path = out_path)

# for(i in unique(mlra_df$MLRARSYM)){
#   grab_referencesheets(mlra = i, out_path = out_path)
# }
