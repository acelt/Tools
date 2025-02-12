library(arcgis)
library(arcgisbinding)
library(tidyverse)
library(shiny)
library(DT)

ui <- fluidPage(
  selectInput(inputId = "State",
              label = "Pick a State",
              choices = c("AZ", "CA", "CO", "Other")),
  selectInput(inputId = "FO",
                label = "Pick a Field Office",
                choices = c("Casper", "Buffalo")),
  dataTableOutput(outputId = "data")
)

server <- function(input, output, sesison){
  arc.check_product()
  
  data <- arc.open("https://gis.blm.doi.net/arcgis/rest/services/vegetation/BLM_Natl_AIM_TerrADatAndLMF/MapServer/0")
  
  data_df <- arc.select(data)
  
  data_cafo <- data_df |> 
    mutate(year = format(as.POSIXct(DateVisited), "%Y")) |> 
    filter(year == 2024,
           State == input$State,
           grepl(input$FO, ProjectName)|grepl(input$FO, PlotID)) |> 
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
           EcologicalSiteId)
  
  write.csv(data_cafo, "\\\\blm.doi.net\\dfs\\nr\\users\\alaurencetraynor\\My Documents\\Analysis\\WY\\Casper FO\\indicators.csv", row.names = FALSE)
  
  species_data <- arc.open("https://gis.blm.doi.net/arcgis/rest/services/vegetation/BLM_Natl_AIM_TerrADatAndLMF/MapServer/1")
  
  species_data_df <- arc.select(species_data, where_clause = "SpeciesState = 'WY'") |> 
    filter(PlotID %in% data_cafo$PlotID)
  
  species_data_final <- species_data_df |> 
    mutate(CommonName = NA) |> 
    select(PlotID,
           Species,
           CommonName,
           AH_SpeciesCover,
           Hgt_Species_Avg,
           AH_SpeciesCover_n,
           Hgt_Species_Avg_n,
           GrowthHabit,
           GrowthHabitSub,
           Duration,
           Noxious,
           SG_Group)
  
  write.csv(species_data_final, "\\\\blm.doi.net\\dfs\\nr\\users\\alaurencetraynor\\My Documents\\Analysis\\WY\\Casper FO\\speciesindicators.csv", row.names = FALSE)
  
}

shinyApp(ui = ui, server = server)
