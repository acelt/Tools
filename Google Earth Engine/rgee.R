install.packages("rgee")
library(remotes)
library(rgee)
install_github("r-spatial/rgee")
rgee::ee_install()


ee_check() # Check non-R dependencies

rgee::ee_install_set_pyenv(
  py_path = "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python", # Change it for your own Python PATH
  py_env = "rgee" # Change it for your own Python ENV
)

# 1. Initialize the Python Environment
ee_Initialize()
