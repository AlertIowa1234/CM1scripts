import sys,os
import argparse
import netCDF4
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units


def usage(name=None):
   return '''CM1toSHARPpy.py input-netCDF-file output-sounding-file [options] [--help]

Example:
  python3 CM1toSHARPpy.py cm1out.nc CM1SHARP.out -x 0 -y 0 -t 52 -u 12.4 -v 1.9 -windinterp 1
'''

#Define command line arguments
parser = argparse.ArgumentParser(description='Generate SHARPpy from CM1 data.', usage=usage())
parser.add_argument('inputfile', help='Input netCDF file', default='blank')
parser.add_argument('outputfile', help='Output sounding file name', default='CM1out.snd')
parser.add_argument('-x', help='x position to generate sounding data from dataset', type=float, default=0.)
parser.add_argument('-y', help='y position to generate sounding data from dataset', type=float, default=0.)
parser.add_argument('-t', help='time to generate sounding data from in dataset', type=float, default=0.)
parser.add_argument('-u', help='X movement speed of domain in m/s', type=float, default=0.)
parser.add_argument('-v', help='Y movement speed of domain in m/s', type=float, default=0.)
parser.add_argument('-windinterp', help='Use wind vectors interpolated to scalar points?', type=int, default=0)
args = parser.parse_args()
datafile = netCDF4.Dataset(args.inputfile, 'r')

#Define model data variables and other input variables.
PRS  = datafile.variables['prs'][args.t,:,args.y,args.x] / 100.00 * units.mbar
TIME = datafile.variables['time'][:]
TH   = datafile.variables['th'][args.t,:,args.y,args.x] * units.degK
QV   = datafile.variables['qv'][args.t,:,args.y,args.x] * units('g/kg')
TMPK = mpcalc.temperature_from_potential_temperature(PRS, TH)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Wind direction calculation currently uses non interpolated wind vectors interpolated to scalar points, use the flag -windinterp 1 to use the interpolated variables.
if args.windinterp == 0:
 U    = np.array(datafile.variables['u'][args.t,:,args.y,args.x]) + args.u
 V    = np.array(datafile.variables['v'][args.t,:,args.y,args.x]) + args.v
elif args.windinterp == 1:
 U    = np.array(datafile.variables['uinterp'][args.t,:,args.y,args.x]) + args.u
 V    = np.array(datafile.variables['vinterp'][args.t,:,args.y,args.x]) + args.v
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Define output variables.
#------------------------------------------------------------------------------------------
#Still have not found a way to use zf or zh from model data because of numpy giving errors.
HGHT = datafile.variables['z'][:] * 1000.00 * units.meters
#------------------------------------------------------------------------------------------
TMPC = TMPK.to('degC')
DWPC = mpcalc.dewpoint(mpcalc.vapor_pressure(PRS, QV))
WDIR = mpcalc.wind_direction(U, V)
WSPD = mpcalc.wind_speed(U, V) * 1.94384
# Write data to file.
file_header = """%TITLE%
Xaxis_{0}_Yaxis_{1}_Time_{2}   010101/0000

   LEVEL       HGHT       TEMP       DWPT       WDIR       WSPD
-------------------------------------------------------------------
%RAW%""".format(args.x, args.y, int(args.t))

np.savetxt(args.outputfile, np.c_[PRS,HGHT,TMPC,DWPC,WDIR,WSPD], fmt='%10.20f', header=file_header, footer='%END%', delimiter=', ', comments='',)
