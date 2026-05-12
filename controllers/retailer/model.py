from controllers.retailer.sainsburys.model import SainsburysActual, SainsburysForecast
from controllers.retailer.tesco.model import TescoActual, TescoForecast

# we define these here so we have type hints in our code
RetailerForecast = TescoForecast | SainsburysForecast
RetailerActual = TescoActual | SainsburysActual
