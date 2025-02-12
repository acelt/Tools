library(shiny)
library(bslib)

ui <- page_fluid(
  navset_card_underline(
  
  nav_panel("Start Here",
            
            #State dropdown
            selectInput(inputId = "State",
                        label = "Pick a State",
                        choices = c("", "AZ", "CA", "CO","ID", "MT","NM","NV","OR","UT","WY")),
              
            # Field office drop down
            uiOutput("FOlist"),
              
            dateRangeInput(inputId = "Date",
                            label = "Choose a Date Range",
                            start = "2011-01-01",
                            end   = "2024-12-31")),
  nav_panel("Map",
            ),
  
  nav_panel("Indicator Data",
            
            #Output table
            DT::dataTableOutput(outputId = "table1")),          
  
  nav_panel("Species Data",
            
            #Output table
            DT::dataTableOutput(outputId = "table2")),

  nav_panel("Figures",
            plotOutput(outputId = "Indicator_plots"))
  
)
)

server <- function(input, output, session){
  library(arcgis)
  library(arcgisbinding)
  library(tidyverse)
  library(DT)

  output$FOlist <- renderUI({
    if(input$State == "AZ") {
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Arizona Strip", "Hassayampa", "Kingman", "Lake Havasu","Safford","Yuma", "Lower Sonoran","Tuscon"))
    } else if(input$State == "WY"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Casper", "Buffalo", "Cody","Newcastle","Rawlins","Rock Springs","Pinedale","Lander","Kemmerer"))
    } else if(input$State == "CA"){
      selectInput("FO", "Choose a Field Office:",
          choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    } else if(input$State == "CO"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    } else if(input$State == "ID"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    } else if(input$State == "MT"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    } else if(input$State == "NV"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    }else if(input$State == "NM"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    } else if(input$State == "OR"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    } else if(input$State == "UT"){
      selectInput("FO", "Choose a Field Office:",
                  choices = c("Applegate", "Eagle Lake", "Barstow","El Centro", "Needles","Palm Springs","Ridgecrest","Bakersfield", "Bishop","Central Coast", "Mother Lode","Ukiah", "Arcada","Redding"))
    }
  
  })
  
  arc.check_product()
  
  data <- arc.open("https://gis.blm.doi.net/arcgis/rest/services/vegetation/BLM_Natl_AIM_TerrADatAndLMF/MapServer/0")
 
  data1 <- reactive({
    
    # where clause to select state
    clause <- paste0("State = '",input$State, "'")
    
    # Grab data from AGOL and tidy up a bit
    arc.select(data, where_clause = clause) |> 
      mutate(DateVisited = format(as.Date(DateVisited), "%Y-%m-%d")) |> 
      filter(DateVisited > input$Date[1] & DateVisited < input$Date[2],
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
      
  })
  
  output$table1 <- DT::renderDataTable({
    data1()
    })
  
  # Reactive expression to get selected PlotIDs
  selectedPlotIDs <- reactive({
    
    # Get the PlotIDs from the first table
    data1()$`Plot ID`
  })
  
  plot_data <- reactive({
    #ensure data1 exists first
    req(data1())
    data1() |> 
      select(-c(`Date Visited`,`Sagebrush Shape`, `Species of Sagebrush`, `Project Name`, `Photo Link`)) |> 
      pivot_longer(cols = `Bare Soil Cover (%)`:`Average Sagebrush Height (cm)`, names_to = "Indicator", values_to = "Value") |> 
      ggplot(aes(x = `Ecological Site Id`, y = Value, fill = `Ecological Site Id`)) +
      theme_bw(base_size = 14)+
      geom_boxplot() +
      facet_wrap(.~Indicator, scales = "free")+
      theme(axis.text.x = element_blank())
  })
  
  # Make a figure
  output$Indicator_plots <- renderPlot({
    plot_data()
  })
  
  species_data <- arc.open("https://gis.blm.doi.net/arcgis/rest/services/vegetation/BLM_Natl_AIM_TerrADatAndLMF/MapServer/1")
  
  data2 <- reactive({
    
    #where clause
    clause2 <- paste0("SpeciesState = '",input$State, "'")
    
    arc.select(species_data, where_clause = clause2) |> 
    filter(PlotID %in% selectedPlotIDs()) |> 
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
           SG_Group) |> 
      mutate(across(c(AH_SpeciesCover, Hgt_Species_Avg), round))
  })
  
  output$table2 <- DT::renderDataTable({
    data2()
  } )
  
  session$onSessionEnded(function() { stopApp()})
}

shinyApp(ui = ui, server = server)

#shiny examples
#runExample("03_reactivity")
