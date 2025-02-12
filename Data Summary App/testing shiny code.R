library(arcgis)
library(arcgisbinding)
library(tidyverse)
library(DT)

arc.check_product()

data <- arc.open("https://gis.blm.doi.net/arcgis/rest/services/vegetation/BLM_Natl_AIM_TerrADatAndLMF/MapServer/0")

State <- "WY"

FO <-  "Casper"

Date_start <- "2024-01-01"
Date_end <- "2024-12-31"

  # where clause to select state
  clause <- paste0("State = '",State, "'")
  
  # Grab data from AGOL and tidy up a bit
  data1 <- arc.select(data, where_clause = clause) |> 
    mutate(DateVisited = format(as.Date(DateVisited), "%Y-%m-%d")) |> 
    filter(DateVisited > Date_start & DateVisited < Date_end,
           State == State,
           grepl(FO, ProjectName)|grepl(FO, PlotID)) |> 
    select(PlotID,
           DateVisited,
           BareSoilCover,
           TotalFoliarCover,
           SoilStability_All,
           AH_PerenForbCover,
           AH_PerenGrassCover,
           AH_AnnGrassCover,
           AH_SagebrushCover,
           Hgt_Herbaceous_Avg,
           Hgt_Sagebrush_Avg,
           SagebrushShape_All_Predominant,
           Spp_Sagebrush,
           ProjectName,
           PhotoLink,
           EcologicalSiteId) |> 
    rename("Plot ID"= "PlotID",
           "Date Visited"= "DateVisited",
           "Bare Soil Cover (%)"="BareSoilCover",
           "Total Foliar Cover (%)" = "TotalFoliarCover",
           "Soil Stability"= "SoilStability_All",
           "Any Hit Perennial Forb Cover (%)"= "AH_PerenForbCover",
           "Any Hit Perennial Grass Cover (%)" = "AH_PerenGrassCover",
           "Any Hit Annual Grass Cover (%)"= "AH_AnnGrassCover",
           "Any Hit Sagebrush Cover (%)"= "AH_SagebrushCover",
           "Average Herbaceous Height (cm)" = "Hgt_Herbaceous_Avg",
           "Average Sagebrush Height (cm)" = "Hgt_Sagebrush_Avg",
           "Sagebrush Shape"= "SagebrushShape_All_Predominant",
           "Species of Sagebrush"="Spp_Sagebrush",
           "Project Name"= "ProjectName",
           "Photo Link"="PhotoLink",
           "Ecological Site Id"="EcologicalSiteId") |> 
    mutate(`Sagebrush Shape` = gsub("C","Columnar", `Sagebrush Shape`),
           `Sagebrush Shape` = gsub("S","Spreading", `Sagebrush Shape`)) |> 
    mutate(across(`Bare Soil Cover (%)`:`Average Sagebrush Height (cm)`, round))

  data1 <- data1 |> 
    select(-c(`Date Visited`,`Sagebrush Shape`, `Species of Sagebrush`, `Project Name`, `Photo Link`)) |> 
    pivot_longer(cols = `Bare Soil Cover (%)`:`Average Sagebrush Height (cm)`, names_to = "Indicator", values_to = "Value")
  
  ggplot(data1, aes(x = Indicator, y = Value, fill = `Ecological Site Id`)) +
    geom_boxplot()  +
    facet_wrap(.~Indicator)
  