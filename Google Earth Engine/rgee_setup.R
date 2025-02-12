#install.packages("rgee")

library(rgee)
ee_install(py_env = "rgee") # It is just necessary once!

rgee::ee_clean_pyenv()
rgee::ee_install_set_pyenv(py_path = "C:\\Program Files\\ArcGIS\\Pro\\bin\\Python\\envs\\arcgispro-py3")

ee_Initialize(user = 'alaurencetraynor@gcp.usgs.gov')
