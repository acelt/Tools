statustrend.bcov.fcn <- function(nsites, nrepeats=1, site.var=0, year.var=0, siteyear.var=0, index.var=0, site.rho=1, year.rho=0) {

################################################################################
# Function:    modified form trend.se.fcn
# Programmer:  Tom Kincaid
# Date:        April 11, 2003; Modifed 3 Aug 2006 by B. Gitzen to output betahat.cov
# Description:
#   This function calculates the standard error for trend for a design.
#   Input:
#	  nsites = a matrix (dimensions: number of panels (rows) by number of years 
#         (columns)) containing the number of sites visited for each combination 
#         of panel and year
#	  nrepeats = either a single number or a matrix the same dimension as
#         nsites specifying the number of revisits to the sites in a panel for a
#         year, where a single number indicates a fixed number of revisits for
#         all years.  The default is 1.
#      site.var = the variance component estimate for site.  Tthe default is 0.
#      year.var = the variance component estimate for year.  The default is 0.
#      site.year.var = the variance component estimate for site by year 
#         interaction.  The default is 0.
#      index.var = the variance component estimate for index error.  The default 
#         is 0.
#	  site.rho = site correlation across years.  The default is 1.
#	  year.rho = year autocorrelation.  The default is 0.
#   Output:
#      The standard error for trend for a design. Modified 3 Aug 2006 by B. Gitzen to output betahat.cov.
################################################################################

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

# Calculate the number of sites in each panel

panel.nsites <- apply(nsites, 1, max)

# Create a diagonal matrix containing the inverse of the number of sites in each 
# panel

if(npanels > 1)
   dinv <- diag(1/panel.nsites)
else
   dinv <- 1/panel.nsites

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

# Create a diagonal matrix containing the inverse of the number of sites in each panel times the number of visits

dinv.index <- diag(as.vector(ifelse((nsites*nrepeats) > 0, 1/(nsites*nrepeats), 0)))

# Create the matrix for year-to-year correlation of a panel mean

rhomat <- matrix(0, nrow=nyears, ncol=nyears)
rhomat[1,] <- 0:(nyears-1)
for(i in 2:nyears) {
   rhomat[i,] <- c(rev(1:(i-1)), 0:(nyears-i))
}

# Create the matrix for year-to-year covariance of the response due to site variation

site.cov <- site.var*(site.rho ^ rhomat)

# Create the matrix for year-to-year covariance of the response due to year variation

year.cov <- year.var*(year.rho ^ rhomat)

# Create the matrix for year-to-year covariance of the response due to site-by-year variation

siteyear.cov <- siteyear.var*diag(nyears)

# Create the matrix for year-to-year covariance of the response due to index variation

index.cov <- index.var*diag(nyears)

# Create the design matrix for trend

xmat <- cbind(rep(1, npanels*nyears), rep(1:nyears, rep(npanels, nyears)))

# Create the covariance matrix for panel means across years

phi <- kronecker(site.cov,dinv) + kronecker(year.cov,matrix(1, nrow=npanels, ncol=npanels)) + kronecker(siteyear.cov,dinv) + kronecker(index.cov,diag(npanels))*dinv.index

# Reduce the dimensionality of xmat and phi to retain only those years in which a panel is 
# visited

indx <- as.vector(nsites) > 0
xmat <- xmat[indx,]
phi <- phi[indx, indx]

# Calculate the variance/covariance matrix for the intercept and trend estimates

temp.qr <- qr(phi)
if(temp.qr$rank < sum(indx))
   stop("\nThe covariance matrix is less than full rank.")
phi.inv <- solve(temp.qr)
betahat.cov <- solve(t(xmat) %*% phi.inv %*% xmat)
#return betahat.cov
betahat.cov

#old
# Return the standard error of the trend estimate

#sqrt(betahat.cov[2,2])

}
