# Description: 'MESH-basin-delineation'
#  
#  
# Configurable conditions.
# Required:
# Required packages.
import os
import numpy  as np
import pandas as pd 
import xarray as xs 

# File names.
input_drainage_file = 'C:/Users/DisherB/Documents/Watershed_Delin/Watershed_delineation/Code/Network topology/Input/Little_pic_river/drainage_out.csv'
output_file = 'C:/Users/DisherB/Documents/Watershed_Delin/Watershed_delineation/Code/Network topology/Output/Little_pic_river/MESH_drainage_database.nc'
 
err = 0

# Check if 'input_data' exists.
if (not os.path.exists(input_drainage_file)):
    print("ERROR: The input file cannot be found: %s" % input_drainage_file)
    err = 1
 
# Exit if errors were found.
if (err != 0): exit()

##########################################################################
#Import Data
d1 = pd.read_csv(input_drainage_file)

#Remove nan and replace with zero 
#temporary solution
d1['gradient'] = d1['gradient'].fillna(0)

# open as Xarray Dataset
ds = xs.Dataset.from_dataframe(d1)

#Count the number of outlets (where data is -1). Note: Currenly only one outlet is supported 
outlets = np.where(ds['next_order'].values == -1)[0]

# Checks.
err = 0
if (len(outlets) == 0):
    print("ERROR: No outlets found.")
    err = 1
 
# Exit if errors were found.
if (err != 0): exit()
##########################################################################
#Drop all other variables not needed inside.dbf
ds = ds[['cat', 'area', 's_order', 'next_order' , 'length', 'gradient', 'lat', 'lon']]

# apply minimum threshold for ChnlSlope
thres_min = 1e-6
ds['gradient'][ds['gradient'] < thres_min] = 1e-5

##########################################################################
#Replace outlets (-1) with 0
ds['next_order'][ds['next_order'] == -1] = 0

#re-indexing and re-ordering
#Create a subset of 'rank' and a dummy 'new_index' variable
Rank = ds['s_order'].values.copy()
Next = ds['next_order'].values.copy()
new_index = []

# Loop to re-rank values
for i in range(1, ds['s_order'].values.max()+1):
    for j in range(0, len(Rank)):
        if Rank[j] == i and not j in outlets:
            new_index.append(j)
            
# #re-add outlets at the end of the index 
new_index.extend(outlets)            

#de-increment Rank and Next       
now_next = 1
for i in range(1, ds['s_order'].values.max()+1):
        if i in ds['s_order'].values:
            ds['next_order'].values = np.where(ds['next_order'].values == i, now_next, ds['next_order'].values)
            ds['s_order'].values =  np.where(ds['s_order'].values == i, now_next, ds['s_order'].values)
            now_next += 1


# #re-order the variables based on the 'new_rank'
for m in ['cat','area','s_order', 'next_order' , 'length', 'gradient', 'lat', 'lon']:
     ds[m].values = ds[m].values[new_index]
#########################################################################
#Drainage variables 
# Set coordinates to latitude and longtitude
ds = ds.set_coords(['lon', 'lat'])

# Rename index variables to subbasin
ds = ds.rename({'index':'subbasin'})

# Rename variables in .dbf (must be consistent with what MESH is expecting)
for old, new in zip(['cat','area','s_order', 'next_order' , 'length', 'gradient'], ['ID','GridArea', 'Rank', 'Next', 'ChnlLength', 'ChnlSlope']):
    ds = ds.rename({old: new})
 
# Assign missing attributes for all variables  
ds['GridArea'].attrs['long_name'] = 'Grid area (GridArea)'
ds['GridArea'].attrs['units'] = 'm**2'
ds['GridArea'].attrs['grid_mapping'] = 'crs'
ds['GridArea'].attrs['coordinates'] = 'time lon lat'

ds['Rank'].attrs['long_name']    = 'Element ID (Rank)'
ds['Rank'].attrs['units']        = '1'
ds['Rank'].attrs['grid_mapping'] = 'crs'
ds['Rank'].attrs['coordinates']  = 'time lon lat'

ds['Next'].attrs['long_name']    = 'Element ID (Rank)'
ds['Next'].attrs['units']        = '1'
ds['Next'].attrs['grid_mapping'] = 'crs'
ds['Next'].attrs['coordinates']  = 'time lon lat'

ds['ChnlLength'].attrs['long_name'] = 'Channel length (ChnlLength)'
ds['ChnlLength'].attrs['units']     = 'm'
ds['ChnlLength'].attrs['grid_mapping'] = 'crs'
ds['ChnlLength'].attrs['coordinates']  = 'time lon lat'

ds['ChnlSlope'].attrs['long_name'] = 'Channel slope (ChnlSlope)'
ds['ChnlSlope'].attrs['units'] = 'm m**-1'
ds['ChnlSlope'].attrs['grid_mapping'] = 'crs'
ds['ChnlSlope'].attrs['coordinates']  = 'time lon lat'

#Add 'axis' and missing attributes for the 'lat' variable.
ds['lat'].attrs['standard_name'] = 'latitude'
ds['lat'].attrs['units'] = 'degrees_north'
ds['lat'].attrs['axis'] = 'Y'
 
# Add 'axis' and missing attributes for the 'lon' variable.
ds['lon'].attrs['standard_name'] = 'longitude'
ds['lon'].attrs['units'] = 'degrees_east'
ds['lon'].attrs['axis'] = 'X'

# Add or overwrite 'grid_mapping' for each variable (except axes).
for v in ds.variables:
    if (ds[v].attrs.get('axis') is None):
        ds[v].attrs['grid_mapping'] = 'crs'

# Projection Information
if (ds.variables.get('crs') is None):
    ds['crs'] = ([], np.int32(1))
    ds['crs'].attrs.update(grid_mapping_name = 'latitude_longitude', longitude_of_prime_meridian = 0.0, semi_major_axis = 6378137.0, inverse_flattening = 298.257223563)

# Import 'date' from 'datetime'.
from datetime import date
 
# Add a 'time' axis with static values set to today (in this case, time is not actually treated as a dimension).
ds['time'] = (['subbasin'], np.zeros(len(ds['Rank'])))
ds['time'].attrs.update(standard_name = 'time', units = ('days since %s 00:00:00' % date.today().strftime('%Y-%m-%d')), axis = 'T')
 

# Set the 'coords' of the dataset to the new axes.
ds = ds.set_coords(['time','lon', 'lat'])

# Add (or overwrite) the 'featureType' to identify the 'point' dataset.
ds.attrs['featureType'] = 'point'

# Save the new dataset to file.
ds.to_netcdf(output_file)

##########################################################################
#assigning CLASS landcover data
input_drainage_file_LC = 'C:/Users/DisherB/Documents/Watershed_Delin/Watershed_delineation/Code/Landcover/Input/CLASS/Little_pic_river/drainage_LC_out.csv'
output_CLASS_file = 'C:/Users/DisherB/Documents/Watershed_Delin/Watershed_delineation/Code/Landcover/Output/CLASS/Little_pic_river/MESH_drainage_database.nc'
#import data as pandas array
l1 = pd.read_csv(input_drainage_file_LC)

#aggregate data - group by subbasin ID (a_cat) and Landcover ID (b_value), maintain the sub-basin area and sum landcover area
ls_agg = l1.groupby(['a_cat', 'b_value'], as_index = False).agg({'a_area':'first', 'area': 'sum'})

#get unique landcover ID values
LC_unique = ls_agg['b_value'].unique()                                                                 
a_cat_unique= ls_agg['a_cat'].unique()  

#Calculate relative area of each landcover 
ls_agg['rel_area'] = (ls_agg['area']/ls_agg['a_area'])

new_CLASS = np.zeros((len(ds['ID']), len(LC_unique)))
LC_unique = LC_unique.tolist()

# re-order and wrangle  he data into the correct array shape. 
for i , r in ls_agg.iterrows(): 
    count = 0 
    for x in a_cat_unique:    
        if x == r['a_cat']:
            new_CLASS[new_index.index(count), LC_unique.index(r['b_value'])] = r['rel_area'] 
        count += 1

#Create dummy array for extra CLASS gru - Required to run MESH
dummy_array = np.zeros((len(ds['ID']),1))
new_CLASS = np.append(new_CLASS, dummy_array, axis = 1)

# Add atttributes to 'GRU' variables 
ds['GRU'] = (['subbasin', 'gru'], new_CLASS) 
#ds['GRU'].attrs = (np.array(range(1, len(Reordered_Rank) + 1), dtype = 'int32')) 
ds['GRU'].attrs['long_name'] ='Fraction of land cover (GRU)'
ds['GRU'].attrs['units'] ='1'
ds['GRU'].attrs['grid_mapping'] = 'crs'
ds['GRU'].attrs['coordinates']  = 'time lon lat'

# Save the new dataset to file.
ds.to_netcdf(output_CLASS_file)

##########################################################################
output_SVS_file = 'C:/Users/DisherB/Documents/Watershed_Delin/Watershed_delineation/Code/Landcover/Output/SVS/Litte_pic_river/MESH_drainage_database.nc'

#assigning lancover to each gru in SVS
new_SVS = np.zeros((len(ds['ID']), 2))
new_SVS[:, 0] = 1.0

# Add atttributes to 'GRU' variables 
ds['GRU'] = (['subbasin', 'gru'], new_SVS) 
ds['GRU'].attrs = (np.array([0], dtype = 'int32'))
ds['GRU'].attrs['long_name'] ='Fraction of land cover (GRU)'
ds['GRU'].attrs['units'] ='1'
ds['GRU'].attrs['grid_mapping'] = 'crs'
ds['GRU'].attrs['coordinates']  = 'time lon lat'

#Save the new dataset to file.
ds.to_netcdf(output_SVS_file)
##########################################################################
### Print of script message.
print('\nProcessing has completed.')