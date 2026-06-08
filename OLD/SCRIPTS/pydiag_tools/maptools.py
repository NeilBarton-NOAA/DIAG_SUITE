################################################################################
# Neil P. Barton
# (c) Neil P. Barton, 2014-02-26 Wed 01:42 AM UTC
################################################################################
# These Modules Provide default maps based on basemap and matplotlib
################################################################################
from matplotlib.pylab import show
####################################
def index_lon_lat_dat(lon, lat, dat):
   from numpy import argsort, array, squeeze, zeros
   from numpy.ma import masked_where
   lon = lonE2W(lon)
   lon2, lat2, dat2 = zeros(dat.shape) - 9999.0, zeros(dat.shape) - 9999.0, zeros(dat.shape) - 9999.0
   is_mask = False
   if hasattr(dat, 'mask'):
      if (dat.mask.size > 1):
        is_mask = True
   if is_mask:
      mask = dat.mask
      mask2 = zeros(dat.shape) - 9999.0
   for i in range(dat.shape[0]):
      index = argsort(lon[i])
      lon2[i] = lon[i, index]  
      lat2[i] = lat[i, index]
      dat2[i] = dat[i, index]
      if is_mask:
         mask2[i] = mask[i, index]
   if is_mask:
      dat2 = masked_where(mask2 == True, dat2)
   return lon2, lat2, dat2

####################################
def lonE2W(longitude):
    """
    converts longitude degrees that are West equal negative values into East values that are all positive
    INPUTS
        longitude: with negative west
    OUTPUTS
        longitude: with negative west as positive east components
    DEPENDENCIES
       numpy
    """
    from numpy import abs, array
    longitude = array(longitude)
    if (longitude.size == 0):
        if longitude > 180:
            longitude = longitude - 360.0
    else:
        longitude[longitude > 180.0] = (longitude[longitude > 180.0] - 360.0)
    return longitude

####################################
def lonW2E(longitude):
    """
    converts longitude degrees that are West equal negative values into East values that are all positive
    INPUT
        longitude: longitude defined positive from east
    OUTPUT
        longitude: longitude defined with west lons as negative
    DEPENDENCIES
        numpy
    """
    from numpy import array
    longitude = array(longitude)
    if (longitude.size == 1):
        if longitude < 0:
            longitude = longitude + 360.0
    else:
        longitude[longitude < 0] = longitude[longitude < 0] + 360
    return longitude


