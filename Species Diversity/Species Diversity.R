### Calculating Species richness by functional group ###

# Setup
library(tidyverse)

# will need to install this package via github
# devtools::install_github('Landscape-Data-Commons/terradactyl')
library(terradactyl)

# I'm going to import the data with arcgisbinding since im accessing the .sde but could use sf::st_read() if just reading from a .gdb
library(arcgisbinding)
arc.check_product()
library(RODBC)

### Parameters
sde_path <- "\\\\blm.doi.net\\dfs\\loc\\EGIS\\ProjectsNational\\AIM\\AIMDataTools\\SDE\\AIMTerrestrialPub.sde"
  
# Define groups (could be from tblStateSpecies or elsewhere)
tblstatespecies_path <- paste0(sde_path, "/ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.tblStateSpecies")

# we could get species inventory data from either tblSpecRichDetail or just from the TerrestrialSpecies layer 
# the latter will be easier since it includes both AIM and LMF
species_indicator_path <- paste0(sde_path, "/ilmocAIMTerrestrialPub.ilmocAIMPubDBO.TerrestrialSpecies")

### read in
# state species list with all grouping info
# dont need this now since were grouping by functional group/duration which is already in the species indicator table
#tblstatespecies <- arcgisbinding::arc.open(path = tblstatespecies_path)

# using arcgisbinding for this just in case I want to merge back to species indicators and write it back to a feature clss for further spatial analysis
# species presence and cover
species_indicator <- arcgisbinding::arc.open(path = species_indicator_path)

# Filter this down to the plots of interest and convert to data frames
clause = "State = 'NM'"
species_indicator <- arcgisbinding::arc.select(species_indicator, where_clause = clause)

#tblstatespecies <- arcgisbinding::arc.select(tblstatespecies)

# join the species inventory tall data and species data
# species_inventory <-  merge(x = species_indicator,
#                                  y = tblstatespecies,
#                                  all.x = TRUE,
#                                  all.y = FALSE,
#                                  by.x = c("SpeciesState", "Species"),
#                                  by.y = c('SpeciesState', "SpeciesCode"))

# calculate number of annual and perennial species
# summarise by plot and the combo of duration and growth habitat sub group
plot_summary <- species_indicator %>% 
  group_by(PrimaryKey, GrowthHabitSub, Duration) %>%  # just grouping by growth habit and duration not noxious here
  summarise(richness = n()) %>% 
  pivot_wider(id_cols = PrimaryKey, names_from = c(GrowthHabitSub, Duration), values_from = richness) %>% # pivoting just to sum
  #mutate(Total = rowSums(across(Forb_Perennial:NA_NA),na.rm = T)) %>% # removing this total for now
  pivot_longer(cols = 2:12, names_to = "indicator",values_to = "richness") %>% 
  ungroup()
# may want to check spatial info for revisits in here...

# if we need Any Hit cover from these same groups we'll need to calculate that from the LPI raw data
# Im pulling in just the tabular data from the SQL database because its faster 
conn <- RODBC::odbcConnect(dsn = "AIMPub", rows_at_time = 1)

tblLPIDetail <- RODBC::sqlQuery(conn, 'SELECT * FROM ILMOCAIMPUBDBO.tblLPIDetail;')
tblLPIHeader <- RODBC::sqlQuery(conn, 'SELECT * FROM ILMOCAIMPUBDBO.tblLPIHeader;')
PINTERCEPT <-  RODBC::sqlQuery(conn, 'SELECT * FROM ILMOCAIMPUBDBO.PINTERCEPT;')
terradat <- RODBC::sqlQuery(conn, 'SELECT * FROM ILMOCAIMPUBDBO.TerrestrialIndicators;')

# subset
tblLPIDetail <- tblLPIDetail[tblLPIDetail$PrimaryKey %in% plot_summary$PrimaryKey,]
tblLPIHeader <- tblLPIHeader[tblLPIHeader$PrimaryKey %in% plot_summary$PrimaryKey,]
PINTERCEPT <- PINTERCEPT[PINTERCEPT$PrimaryKey %in% plot_summary$PrimaryKey,]
terradat <- terradat[terradat$PrimaryKey %in% plot_summary$PrimaryKey,]

lpi_tall <- terradactyl::gather_lpi(source = "AIM",
                        tblLPIDetail = tblLPIDetail,
                        tblLPIHeader = tblLPIHeader)

# merge species attributes
species_lut <- species_indicator %>% 
  select(Species, GrowthHabitSub, Duration) %>% 
  mutate(HabitDuration = paste(GrowthHabitSub, Duration, sep = "_")) %>% 
  unique()

lpi_tall_join <- merge(x = lpi_tall,
                       y = species_lut[,c("Species","HabitDuration")],
                       by.x = "code",
                       by.y = "Species",
                       all.x = T,
                       all.y = F)

lpi_cover_aim <- terradactyl::pct_cover(lpi_tall = lpi_tall_join,
                                        tall = T,
                                        hit = "any",
                                        by_line = F,
                                        HabitDuration)
  
# repeat for lmf
lpi_tall_lmf <- terradactyl::gather_lpi(source = "LMF",
                                    PINTERCEPT = PINTERCEPT)

# merge species attributes
lpi_tall_lmf_join <- merge(x = lpi_tall_lmf,
                       y = species_lut[,c("Species","HabitDuration")],
                       by.x = "code",
                       by.y = "Species")

lpi_cover_lmf <- terradactyl::pct_cover(lpi_tall = lpi_tall_lmf_join,
                                        tall = T, # output will be tall/long
                                        hit = "any",
                                        by_line = F,
                                        HabitDuration)

# bind aim and lmf
lpi_cover_aimlmf <- bind_rows(lpi_cover_aim,lpi_cover_lmf)

# revert indicators back to lower case
lpi_cover_aimlmf$indicator <- tolower(lpi_cover_aimlmf$indicator)

# merge to species richness info
# make that formatting the same first
plot_summary$indicator <- tolower(plot_summary$indicator)



cover_richness <-  merge(x = lpi_cover_aimlmf,
                         y = plot_summary,
                         by = c("PrimaryKey","indicator"),
                         all = TRUE) # TO 

# should also grab total foliar cover from terradat
cover_richness <- merge(x = cover_richness,
                        y = terradat[,c("PrimaryKey","TotalFoliarCover")],
                        by = "PrimaryKey")

# heres a function for calculating diversity!
calc_diversity <- function(data, method = "shannons"){
  if(method == "shannons"){
    diversity_summary <- data %>% 
      group_by(PrimaryKey) %>% 
      filter(percent>0) %>% 
      mutate(proportion = percent/TotalFoliarCover,
             logp = log(proportion),
             plogp = proportion * logp) %>% 
      summarise(shannons = -sum(plogp, na.rm = T),
                richness = sum(richness),
                evenness = shannons/log(richness)) %>% 
      ungroup()
  }
  if(method == "simpsons"){
    diversity_summary <- data %>% 
      group_by(PrimaryKey) %>% 
      filter(percent>0) %>% 
      mutate(nn1 = percent *(percent-1),
             NN1 = TotalFoliarCover*(TotalFoliarCover-1),
             nn1NN1= nn1/NN1) %>% 
      summarise(Simpsons = sum(nn1NN1),
                S1 = 1-sum(nn1NN1),
                richness = sum(richness)) %>% 
      ungroup()
    
  }
  return(diversity_summary)
  
  }

diversity_summary <- calc_diversity(data = cover_richness,
                                    method = "shannons")

# join this back to species indicators to get the spacial info and write to gdb
# this will be joined to primarykey so will be duplicated across different species

# this can exclude the spatial info without converting to sf

species_indicator <- arcgisbinding::arc.data2sf(species_indicator)

species_indicator_join <- sp::merge(x = species_indicator,
                                y = diversity_summary,
                                by = "PrimaryKey",
                                all.x = T,
                                all.y = F)

# write
arc.write(path = "C:\\Users\\alaurencetraynor\\Documents\\Tools\\Species Diversity\\Species Diversity.gdb\\species_diversity_NM",
          data = species_indicator_join)
  