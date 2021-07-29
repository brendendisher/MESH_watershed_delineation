from grass.script import core as gcore
#install required GRASS modules
#gcore.run_command('g.extension', extension = 'r.stream.segment')
#gcore.run_command('g.extension', extension = 'r.stream.basins')
#Define input and output data 
input_DEM =r'C:\Users\DisherB\Documents\Watershed_Delin\Merit_Hydro\n50w120_elv.tif'
input_WSC =r'C:\Users\DisherB\Documents\Watershed_Delin\WSC_Basins.gdb'
output_db = r'C:\Users\DisherB\Documents\Watershed_Delin\Python-Dev\drainage_out.csv'
#Required arguments 
WSC_basin = 'EC_05BB001_1' #Water Survey Canada (WSC) Basin ID 
coords = '-115.5717,51.17222' # Coordinates of the outlet
threshold = '5000' #Minimum flow accumulation for streams 
# Import Raster
DEM_in = 'DEM_in'
gcore.run_command('r.in.gdal', input = input_DEM, output = DEM_in, overwrite = True)
#Import geodatabase
Basin_in ='Basin_in' 
gcore.run_command('v.import',layer = WSC_basin, input = input_WSC, output = Basin_in, overwrite = True)
#buffer basin
basin_buffered = 'basin_buffered'
gcore.run_command('v.buffer', input = Basin_in, distance = '0.05', minordistance = '0.05', output = basin_buffered, overwrite = True)
#update mask 
#add if mask true, then remove
#gcore.run_command('r.mask', vect=basin_buffered, overwrite = True)
#generate flow accumulation and direction 
flow_dir = 'flow_dir'
flow_acc = 'flow_acc'
gcore.run_command('r.watershed', elevation = DEM_in, accumulation = flow_acc, drainage = flow_dir, flags = 's', overwrite = True)
#generate watershed outline
watershed_outline ='watershed_outline'
gcore.run_command('r.water.outlet', input = flow_dir, output = watershed_outline, coordinates = coords, overwrite = True)
#update mask 
gcore.run_command('r.mask', rast='Watershed_outline', overwrite = True)
#Generate stream network
stream_raster = 'stream_raster'
gcore.run_command('r.stream.extract', elevation = DEM_in, accumulation = flow_acc, threshold = threshold, stream_raster = stream_raster, direction = flow_dir, overwrite = True)
#generate stream topology 
stream_segments = 'stream_segments'
stream_sector = 'stream_sector'
gcore.run_command('r.stream.segment', stream_rast = stream_raster, elevation = DEM_in, direction = flow_dir, segments = stream_segments, sectors = stream_sector, overwrite = True)
#Generate subbasins
watershed_subbasins ='watershed_subbasins'
gcore.run_command('r.stream.basins', direction = flow_dir, stream_rast = stream_raster, basins = watershed_subbasins, overwrite = True)
#Clean data 
watershed_subbasins_cleaned = 'watershed_subbasins_cleaned'
gcore.run_command('r.neighbors', input = watershed_subbasins, output = watershed_subbasins_cleaned, method = 'mode', overwrite = True)
#Convert to vector 
subbasins_vector = 'subbasins_vector'
gcore.run_command('r.to.vect', input = watershed_subbasins_cleaned, output = subbasins_vector, type ='area', flags = 'v', overwrite = True)
#Join datasets 
gcore.run_command('v.db.join', map = subbasins_vector, column='cat', other_table =stream_segments, other_column = 's_order', overwrite = True)
#add new columns for area, lat and lon
gcore.run_command('v.db.addcolumn', map = subbasins_vector, columns = "area double precision")
gcore.run_command('v.db.addcolumn', map = subbasins_vector, columns = "lat double precision")
gcore.run_command('v.db.addcolumn', map = subbasins_vector, columns = "lon double precision")
#generate values for new columns 
gcore.run_command('v.to.db', map = subbasins_vector, option = 'area', columns = 'area')
gcore.run_command('v.to.db', map = subbasins_vector, option = 'coor', columns = 'lon,lat')
#Export attribute table 
gcore.run_command('db.out.ogr', input = subbasins_vector, output = output_db, overwrite = True)
