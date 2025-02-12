
# Setup packages
library(tidyverse)
library(RODBC)

# Create parameters 
tar_ee <- 0.03
tar_sd <- 0.05
tar_ci <- 0.1
cl <- 0.8
est_p <- 0.3

# Inverse normal cumulative distribution 
a <-  qnorm((cl+1)/2)

# Number of intercepts required for each parameter
# For any cover value
intercepts_ee_any <- 0.5/pi/tar_ee^2
intercepts_sd_any <- 0.25/tar_sd^2
intercepts_ci_any <- a^2/tar_ci^2

# For Estimate cover value parameter
intercepts_ee_p <- 2*est_p*(1-est_p)/pi/tar_ee^2
intercepts_sd_p <- est_p*(1-est_p)/tar_sd^2
intercepts_ci_p <- intercepts_ci_any*4*est_p*(1-est_p)

# Make this into a function

drezner <- function(tar_ee, tar_sd, tar_ci, cl, est_p, output_table){
  
  # Inverse normal cumulative distribution 
  a <-  qnorm((cl+1)/2)
  
   # Number of intercepts required for each parameter
  # For any cover value
  intercepts_ee_any <- 0.5/pi/tar_ee^2
  intercepts_sd_any <- 0.25/tar_sd^2
  intercepts_ci_any <- a^2/tar_ci^2
  
  any_vars <- c(intercepts_ee_any,intercepts_sd_any,intercepts_ci_any)
  
  # For Estimate cover value parameter
  if(!is.na(est_p) & length(est_p)>0){
    intercepts_ee_p <- 2*est_p*(1-est_p)/pi/tar_ee^2
    intercepts_sd_p <- est_p*(1-est_p)/tar_sd^2
    intercepts_ci_p <- intercepts_ci_any*4*est_p*(1-est_p)
  } else{
    intercepts_ee_p <- NA
    intercepts_sd_p <- NA
    intercepts_ci_p <- NA
  }
  
  p_vars <- c(intercepts_ee_p,intercepts_sd_p,intercepts_ci_p)
  
  # build results table
  colnames <- c("Number of Intercepts Required for Estimated Cover:", "Number of Intercepts Required for Any Cover")
  rownames <- c("Target Expected Error", "Target Standard Deviation", "Target Confidence Level")
  
  output <- data.frame(cbind(p_vars,any_vars), row.names = rownames)  
  colnames(output) <- colnames
  
  output[1,1] <- intercepts_ee_p
  output[2,1] <- intercepts_sd_p
  output[3,1] <- intercepts_ci_p
  output[1,2] <- intercepts_ee_any
  output[2,2] <- intercepts_sd_any
  output[3,2] <- intercepts_ci_any
  
  output_alt <- c(ee = intercepts_ee_p, sd = intercepts_sd_p,ci = intercepts_ci_p)
  
  if(output_table == TRUE){
    return(output)
  } else{
    return(output_alt)
  }
  
  
}

drezner(tar_ee = 0.03,
        tar_sd = 0.05,
        tar_ci = 0.1,
        cl = 0.8212332,
        est_p = 0.434234,
        output_table = FALSE)

# Lets in some species ind data to test
con_name <- "AIMPub"
conn <- RODBC::odbcConnect(dsn = con_name, rows_at_time = 1)

# load terrestrial species
ter_species <- RODBC::sqlQuery(conn, 'SELECT * FROM ilmocAIMTerrestrialPub.ILMOCAIMPUBDBO.TerrestrialSpecies;')

# Subset to state
state <-  "CO"

# Filter rows to state
state_species <- ter_species[ter_species$SpeciesState == state,]

# run it per plot per species and report parameters and results
# build an empty list and fill
list <- list()
state_species <- state_species[state_species$AH_SpeciesCover > 0 & !is.na(state_species$AH_SpeciesCover) & state_species$Species != "NULL" ,]

results <- lapply(X = split(state_species, state_species[["PrimaryKey"]]),      
       FUN = function(state_species){
        for(i in unique(state_species[["Species"]])){
          species_cover <-  state_species$AH_SpeciesCover[state_species$Species == i][1]/100
         
          list[[i]] <- drezner(tar_ee = 0.03,
                               tar_sd = 0.05,
                               tar_ci = 0.1,
                               cl = 0.95,
                               est_p = species_cover,
                               output_table = FALSE)
        }
        return(list)
      })

results_df <- do.call("rbind", results)
results_df <- do.call("rbind", results_df)
results_df_filled <- plyr::rbind.fill(results_df)

# calc some summary stats
#Intercepts for expected error
mean(results_df_filled[,1])
sd(results_df_filled[,1])

# for standard deviaiton
mean(results_df_filled[,2])
sd(results_df_filled[,2])

# for 80% confidence intervals
mean(results_df_filled[,3])
sd(results_df_filled[,3])

write.csv(results_df_filled, "C:\\Users\\alaurencetraynor\\Documents\\drezner_95.csv")
