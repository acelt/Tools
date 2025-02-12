#### S. L. Garman's modification (2008) of T. Kincaid's power.status.fcn.  
### This is a modified version of power.status.fcn.R.   Instead of having defaults in the function call, the inputs are explicitly
### listed in this top section.  The function, statustrend.bcov.fcn.R, is a separate R script and called within to derive SE of trend and
### estimates used to derive the SE of status.  In this version, this R script serves as the 'MAIN' of the power code - first copy & paste
### statustrend.bcov.fcn.R into the R console, then modify the inputs here and copy & paste this script to the R console to execute.

### Added the ability to output power and SE of status at the very end of power.status.fcn.R - to faciliate further processing
##  and graphing of results.


indicator="Test Indicator"                                                                     
ind.mean=1.00     		## When using ln-transformed observations to derive site, year, and residual variance, set this to 1                                                                             
trend=  1.0000000		## This is the % trend-slope to detect.  Internally it is converted to fractional trend-slope (i.e., trend/100)
site.var=         .258         	## site, year, and residual variance are the biggies - best to use ln-transformed data to derive these.                                                               
year.var=          0.008                                                                       
siteyear.var=0.0 		## This is variance due to re-measuring the same site(s) across multiple years; else use the default                                                                              
index.var=        .109                                                                         
site.rho=1			## Use the default unless you have detailed information in support of site-to-site correlation                                                                                     
year.rho=0.0  			## Use the default unless you have detailed information in support of year-to-year autocorrelation                                                                                 		
alfa=0.2      			## Type I error                                                                                 
plot.ind=TRUE                   ## Makes pretty-picture power curves, but sometimes doesn't work?????                                                               
                                                                                               
## nsites is the design matrix.  Each row is a panel.  Each entry within a row is the year a panel is monitored, starting at yr 1.
## E.g., Here we have 50 plots in panel 1 which is monitored in yr 1, and every 5 yrs aftwerwards over a 20-yr period.
##       There are 50 plots in panels 2-5, where panel2 is first monitored in yr 2, panel 3 in yr 3, etc.. and
##       all panels are remeasured every 5 yrs.
                                                                                               
nsites <- matrix(c(50,0,0,0,0,50,0,0,0,0,50,0,0,0,0,50,0,0,0,0,                                
0,50,0,0,0,0,50,0,0,0,0,50,0,0,0,0,50,0,0,0,                                                   
0,0,50,0,0,0,0,50,0,0,0,0,50,0,0,0,0,50,0,0,                                                   
0,0,0,50,0,0,0,0,50,0,0,0,0,50,0,0,0,0,50,0,                                                   
0,0,0,0,50,0,0,0,0,50,0,0,0,0,50,0,0,0,0,50), nrow= 5, ncol=  20, byrow=TRUE)                  

#################################################################################################################################
#################################################################################################################################
## power.status.fcn code starts here.
                                                                                               
nrepeats=1                                                                                     
                                                                                               
# Calculate additional required values                                                         
                                                                                               
   nind <- length(indicator)                                                                   
   trend <- trend/100                                                                          
   trend.mean <- trend*ind.mean                                                                
                                                                                               
# Ensure that nsites is a matrix                                                               
                                                                                               
   if(length(nsites) == 1)                                                                     
      stop("\nThe input value for nsites must be a matrix.")                                   
   if(!is.matrix(nsites))                                                                      
      nsites <- as.matrix(nsites)                                                              
                                                                                               
#  Calculate the number of panels and the number of years for nsites                           
                                                                                               
   npanels <- nrow(nsites)                                                                     
   nyears <- ncol(nsites)                                                                      
                                                                                               
# Ensure for a design with a single panel that nsites has one row                              
                                                                                               
   if(nyears == 1) {                                                                           
      nsites <- t(nsites)                                                                      
      nyears <- npanels                                                                        
      npanels <- 1                                                                             
   }                                                                                           
                                                                                               
# As necessary, create nrepeats                                                                
                                                                                               
   if(length(nrepeats) == 1) {                                                                 
      temp <- nrepeats                                                                         
      nrepeats <- matrix(0, nrow=npanels, ncol=nyears)                                         
      nrepeats[nsites > 0] <- temp                                                             
   }                                                                                           
                                                                                               
# Ensure that nrepeats is a matrix                                                             
                                                                                               
   if(!is.matrix(nrepeats))                                                                    
      nrepeats <- as.matrix(nrepeats)                                                          
                                                                                               
#  Calculate the number of panels and the number of years for nrepeats                         
                                                                                               
   npanels.nr <- nrow(nrepeats)                                                                
   nyears.nr <- ncol(nrepeats)                                                                 
                                                                                               
# Ensure for a design with a single panel that nrepeats has one row                            
                                                                                               
   if(nyears.nr == 1) {                                                                        
      nrepeats <- t(nrepeats)                                                                  
      nyears.nr <- npanels.nr                                                                  
      npanels.nr <- 1                                                                          
   }                                                                                           
                                                                                               
# Ensure that nsites and nrepeats have the same dimensions                                     
                                                                                               
   if(npanels != npanels.nr)                                                                   
      stop("\nThe input values for nsites and nrepeats must have the same number of rows")     
   if(nyears != nyears.nr)                                                                     
      stop("\nThe input values for nsites and nrepeats must have the same number of columns")  
                                                                                               
# Create the array for output power values                                                     
 	#modified pout <- array(0, c(nyears-1,nind))                                                 
   pout <- array(0, c(nyears-1,nind*2)) #modified to allow nind additional columns of status SE
                                                                                               
# modified Calculate power values                                                              
# Calculate power and status values                                                            
   for(j in 1:nind) {                                                                          
      for(i in 2:nyears) {                                                                     
         #modified indexse <- trend.se.fcn(nsites=nsites[,1:i], nrepeats=nrepeats[,1:i],       
           # site.var=site.var[j], year.var=year.var[j],                                       
           # siteyear.var=siteyear.var[j], index.var=index.var[j],                             
           # site.rho=site.rho, year.rho=year.rho)                                             
        #Now calculate betahat.cov here                                                        
	betahat.cov <- statustrend.bcov.fcn(nsites=nsites[,1:i], nrepeats=nrepeats[,1:i],             
            site.var=site.var[j], year.var=year.var[j],                                        
            siteyear.var=siteyear.var[j], index.var=index.var[j],                              
            site.rho=site.rho, year.rho=year.rho)                                              
	#Power                                                                                        
	indexse<-sqrt(betahat.cov[2,2])                                                               
                                                                                               
        # comment out afterwards                                                               
	#pout[i-1,j+nind] <-sqrt(betahat.cov[2,2])                                                    
                                                                                               
	pout[i-1,j]  <- (pnorm(qnorm(alfa/2) - (trend.mean[j]/indexse))) +                            
            (1 - pnorm(qnorm(1-(alfa/2)) - (trend.mean[j]/indexse)) )                          
        	                                                                                      
	#Status                                                                                       
	Co<-matrix(c(1,i,0,1),nrow=2,byrow=T)                                                         
	pout[i-1,j+nind]  <- sqrt((Co%*%betahat.cov%*%t(Co))[1,1])                                    
                                                                                               
                                                                                               
                                                                                               
      }                                                                                        
   }                                                                                           
                                                                                               
# Begin the section to produce the power plot                                                  
                                                                                               
   if(plot.ind) {                                                                              
                                                                                               
# Set up the plot of power curves                                                              
                                                                                               
      par(mar=c(3.1,4.1,0.1,0.1), oma=c(0,0.1,2.1,0.1), xpd=T)                                 
      ltype <- c(1, 3:6, 8)                                                                    
                                                                                               
      plot(seq(0,nyears,length=11), seq(0,1,length=11), ylim=c(0,1),                           
         xlim=c(0,nyears), ylab="", xlab="", type="n", axes=F)                                 
                                                                                               
      axis(side=1, line=-0.75, at=seq(0, nyears, by=5), labels=seq(0, nyears,                  
         by=5), adj=0.5, font=3, cex=1)                                                        
      axis(side=2, line=-0.5, at=seq(0, 1, by=0.2), labels=c("0%", "20%", "40%",               
         "60%", "80%", "100%"), adj=0.85, font=3, cex=1)                                       
      mtext(outer=F, side=1, line=1.8, text="Number of Years", cex=1.5, font=3)                
      mtext(outer=F, side=2, line=2.5, text="Power for Trend Detection",                       
         cex=1.5, font=3)                                                                      
                                                                                               
#  Plot the power values                                                                       
                                                                                               
   for(j in 1:nind) {                                                                          
      lines(2:nyears, pout[,j], lty=ltype[j], lwd=3)                                           
   }                                                                                           
                                                                                               
# Create the legend for the plot                                                               
                                                                                               
   #legend(0, 1, as.character(indicator), lty=ltype[1:nind], lwd=3)                            
                                                                                               
# Create the title for the plot                                                                
                                                                                               
                                                                                               
# End the section for the power plot                                                           
                                                                                               
   }                                                                                           
                                                                                               
# Output the data frame of power values                                                        
                                                                                               
   pout <- data.frame(Year=2:nyears, pout)                                                     
   names(pout)[-1] <- indicator                                                                
   pout                                                                                        
   write.table(pout,"shsh",row.names=F,col.names=F,quote=F)                                    
