power.status.fcn <- function(indicator="Test Indicator", ind.mean=1, trend=2, nsites=matrix(rep(50, 20), nrow=1, ncol=20), nrepeats=1, site.var=1, year.var=0.001, siteyear.var=0.1, index.var=0.5, site.rho=1, year.rho=0, alfa=0.05, plot.ind=TRUE) {

################################################################################
# Function:   power.fcn
# Programmer: Tom Kincaid
# Date:       January 19, 2005; modified 3 Aug 2006 B Gitzen to output SE of status
# Description:
#   This function calculates power for trend detection for a set of indicators, 
#   where the model includes variance component for sites, years, and the 
#   interaction of sites and years.  Default values for the function calculate 
#   power to detect a trend of 2% per year for an indicator named "Test 
#   Indicator" that has a mean value equal to 1, site variance equal to 1, year 
#   variance equal to 0.001, site-by-year variance equal to 0.1, and residual 
#   (index) variance equal to 0.5.  The default design uses a single panel of 50 
#   sites that are visited once each year for 20 years.  By default, a plot of 
#   power for trend detection is produced.
#   Input:
#      indicator = a vector of indicator names, where the maximum number of 
#         indicators is six.  The default is "Test Indicator".
#      ind.mean = a vector of indicator means, where a value of one is used for 
#         log transformed indicators.  The default is 1.
#      trend = the trend expressed as percent per year.  The default is 2%.
#      nsites = a matrix (dimensions: number of panels (rows) by number of years 
#         (columns)) containing the number of sites visited for each combination 
#         of panel and year.  The default is a single panel containing 50 sites 
#         that are visited for 20 years.
#	  nrepeats = either a single number or a matrix the same dimension as
#         nsites specifying the number of revisits to the sites in a panel for a
#         year, where a single number indicates a fixed number of revisits for
#         all years.  The default is 1.
#      site.var = a vector of variance component estimates for site.  The
#         default is 1.
#      year.var = a vector of variance component estimates for year.  The
#         default is 0.001.
#      site.year.var = a vector of variance component estimates for site by year 
#         interaction.  The default is 0.01.
#      index.var = a vector of variance component estimates for index (residual) 
#         error.  The default is 0.5.
#	  site.rho = site correlation across years.  The default is 1.
#	  year.rho = year autocorrelation.  The default is 0.
#      alfa = the alpha, Type I error, level.  The default is 0.05.
#      plot.ind = option to produce a plot of power values, where TRUE = produce
#         the plot and FALSE =  do not produce the plot.  The default is TRUE.
#   Output:
#      The function returns a data frame of power values for trend detection.
#      Optionally, a plot of power values can be produced.
################################################################################

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
   pout <- array(0, c(nyears-1,nind*2)) #modified to allow nind additional columns of status SEs

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

######################################################################
# Modification by Garman.  Output data frame of power values for further processing & graphing.

   pout <- data.frame(Year=2:nyears, pout)
   names(pout)[-1] <- indicator
   pout
   write.table("shsh",pout,row.names=F,column.names=F,quote=F)
}
