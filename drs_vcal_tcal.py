#!/bin/env python

import os
import sys
import h5py
import ctypes 
import numpy as np
import matplotlib.pyplot as plt

#-----------------------------------------------------------------------

WD_N_CHANNELS = 18
WD_N_CELLS    = 1024

#-------------------------------------------------------------------------------
# Voltage Calibration Class
#-------------------------------------------------------------------------------

class vcal_class:

  class vcal_binary_data(ctypes.Structure):
      _fields_ = [
                   ('version_id',         ctypes.c_char * 4),
                   ('crc',                ctypes.c_int),
                   ('sampling_frequency', ctypes.c_short),
                   ('padding',            ctypes.c_short),
                   ('temperature',        ctypes.c_float),
                   ('wf_offset1',         ctypes.c_float * 1024 * 18),
                   ('wf_offset2',         ctypes.c_float * 1024 * 18),
                   ('wf_gain1',           ctypes.c_float * 1024 * 18),
                   ('wf_gain2',           ctypes.c_float * 1024 * 18),
                   ('drs_offset_range0',  ctypes.c_float * 16 ),
                   ('drs_offset_range1',  ctypes.c_float * 16 ),
                   ('drs_offset_range2',  ctypes.c_float * 16 ),
                   ('adc_offset_range0',  ctypes.c_float * 16 ),
                   ('adc_offset_range1',  ctypes.c_float * 16 ),
                   ('adc_offset_range2',  ctypes.c_float * 16 )
                 ]

  #-----------------------------------------------------------------------

  def __init__(self, filename=None):
    if filename == None:
      self.valid = False
    else:  
      self.valid = self.load(filename)


  def load(self, filename):    
    # check file size
    if (os.path.getsize(filename) != ctypes.sizeof(self.vcal_binary_data)):
      print("Voltage Cal: %s has wrong file size!"%filename)
      return False

    cbd = self.vcal_binary_data()

    with open(filename, 'rb') as file:
      file.readinto(cbd) 

    if (cbd.version_id != b"CAL2"):
      print("Voltage Cal: %s has wrong version!"%filename)
      return False

    self.version_id         = str(cbd.version_id)
    self.crc                = int(cbd.crc)
    self.sampling_frequency = float(cbd.sampling_frequency)
    self.temperature        = float(cbd.temperature)
    self.wf_offset1         = np.ctypeslib.as_array(cbd.wf_offset1       )
    self.wf_offset2         = np.ctypeslib.as_array(cbd.wf_offset2       )
    self.wf_gain1           = np.ctypeslib.as_array(cbd.wf_gain1         )
    self.wf_gain2           = np.ctypeslib.as_array(cbd.wf_gain2         )
    self.drs_offset_range0  = np.ctypeslib.as_array(cbd.drs_offset_range0)
    self.drs_offset_range1  = np.ctypeslib.as_array(cbd.drs_offset_range1)
    self.drs_offset_range2  = np.ctypeslib.as_array(cbd.drs_offset_range2)
    self.adc_offset_range0  = np.ctypeslib.as_array(cbd.adc_offset_range0)
    self.adc_offset_range1  = np.ctypeslib.as_array(cbd.adc_offset_range1)
    self.adc_offset_range2  = np.ctypeslib.as_array(cbd.adc_offset_range2)

    return True

  #-----------------------------------------------------------------------

  def dump(self):   
    print("Voltage Cal Version %-4s  CRC=0x%08x  Freq: %4d  Temperature %.2f deg. C"%(self.version_id, self.crc, self.sampling_frequency, self.temperature))

    for ch in range(WD_N_CHANNELS):
      for cell in range(1024):
        print("ch %2d - cell %4d :  offset1: %10.6f   offset2: %10.6f   gain1: %10.6f   gain2: %10.6f"%(ch, cell,  self.wf_offset1[ch][cell],  self.wf_offset2[ch][cell],  self.wf_gain1[ch][cell],  self.wf_gain2[ch][cell]))
      
    for ch in range(WD_N_CHANNELS-2):
      print ("ch %2d :  %.6f  %.6f  %.6f  %.6f  %.6f  %.6f"%(ch, self.drs_offset_range0[ch],  self.drs_offset_range1[ch],  self.drs_offset_range2[ch],  self.adc_offset_range0[ch],  self.adc_offset_range1[ch],  self.adc_offset_range2[ch]));

#-----------------------------------------------------------------------

  def calibrate(self, data, trigger_cell, channel):
    # cell-by-cell offset calibration
    data -= np.roll(self.wf_offset1[channel], -trigger_cell)
    
    # start-to-end offset calibration
    data -= self.wf_offset2[channel]

    # gain calibration
    msk_gtz = data > 0  # create boolean mask vector for selection 
    data[ msk_gtz] /= np.roll(self.wf_gain1[channel], -trigger_cell)[ msk_gtz]
    data[~msk_gtz] /= np.roll(self.wf_gain2[channel], -trigger_cell)[~msk_gtz]

    return data

  #  # range calibration
  #  
  #  dc_ofs = 0;
  #  
  #  if   (abs(dc_ofs - 0.45) < 0.001):
  #    ofs = self.drs_offset_range0[channel]
  #  elif (abs(dc_ofs)        < 0.001):
  #    ofs = self.drs_offset_range1[channel]
  #  elif (abs(dc_ofs + 0.45) < 0.001):
  #    ofs = self.drs_offset_range2[channel]
  #  else:
  #    ofs = 0
  #
  #  d -= ofs
  #
  #  return d


#-------------------------------------------------------------------------------
# Timing Calibration Class
#-------------------------------------------------------------------------------

class tcal_class:
  
  class tcal_binary_data(ctypes.Structure):
      _fields_ = [
                   ('version_id',         ctypes.c_char * 4),
                   ('crc',                ctypes.c_int),
                   ('sampling_frequency', ctypes.c_float),
                   ('temperature',        ctypes.c_float),
                   ('dt',                 ctypes.c_float * 1024 * 18),
                   ('period',             ctypes.c_float * 1024 * 18),
                   ('offset',             ctypes.c_float * 18 )
                 ]

  #-----------------------------------------------------------------------

  def __init__(self, filename=None):
    if filename == None:
      self.valid = False
    else:  
      self.valid = self.load(filename)

  def load(self, filename):   
    # check file size
    if (os.path.getsize(filename) != ctypes.sizeof(self.tcal_binary_data)):
      print("Timing Cal: %s has wrong file size!"%filename)
      return False

    cbd = self.tcal_binary_data()

    with open(filename, 'rb') as file:
      file.readinto(cbd) 

    if (cbd.version_id != b"CAL2"):
      print("Timing Cal: %s has wrong version!"%filename)
      return False

    self.version_id         = str(cbd.version_id)
    self.crc                = int(cbd.crc)
    self.sampling_frequency = float(cbd.sampling_frequency)
    self.temperature        = float(cbd.temperature)
    self.dt                 = np.ctypeslib.as_array(cbd.dt    )
    self.period             = np.ctypeslib.as_array(cbd.period)
    self.offset             = np.ctypeslib.as_array(cbd.offset)

    #bulid integrated time vector
    # variant 1 : iterations
    #   self.t = np.zeros([WD_N_CHANNELS, 2047], dtype='float32')
    #   for ch in range(WD_N_CHANNELS):
    #     for i in range(1,2047):
    #        self.t[ch][i] = self.t[ch][i-1] + self.dt[ch][(i-1)%1024]

    # variant 2 : with numpy functions instead of iterations:
    dt_zero_pad_tile = np.pad(np.tile(self.dt, 2)[:,:-2],[(0,0),(1,0)], mode='constant') 
    self.t = np.cumsum(dt_zero_pad_tile, axis=1)

    return True

  #-----------------------------------------------------------------------

  def dump(self):   
    print("Timing Cal Version %-4s  CRC=0x%08x  Freq: %.0f  Temperature %.2f deg. C"%(self.version_id, self.crc, self.sampling_frequency, self.temperature))

    for ch in range(WD_N_CHANNELS):
      for cell in range(1024):
        print("ch %2d - cell %4d :  dt: %10.6f ns  period: %10.6f ns"%(ch, cell,  self.dt[ch][cell] * 1e9,  self.period[ch][cell] * 1e9))
      
    for ch in range(WD_N_CHANNELS):
      print ("ch %2d :  offset: %10.6f ns"%(ch, self.offset[ch] * 1e9));


# #-------------------------------------------------------------------------------
# # main
# #-------------------------------------------------------------------------------
#
# # voltage calibration data
# vcal = vcal_class('comb002-5120.vcal')
# if not vcal.valid: sys.exit(-1)
# #vcal.dump()
#
#
# # timing calibration data
# tcal = tcal_class('comb002-5120.tcal')
# if not tcal.valid: sys.exit(-1)
# #tcal.dump()
#
#
# # waveform data from hdf5
#
# filename = 'diode_02.h5'
# channel = 14
#
# h5f = h5py.File(filename)
#
# drs_data = (np.array(h5f['SF-DIGITIZER-01:Lnk9Ch%d-DATA/data'%channel]).astype(np.float32) - 0x800) / 4096.0
# drs_tc   =           h5f['SF-DIGITIZER-01:Lnk9Ch%d-DRS_TC/data'%channel]
#
#
# num_events = min(np.shape(drs_data)[0] ,len(drs_tc))
# num_samples = np.shape(drs_data)[1]
#
#
# #-------------------------------------------------------------------------------
# # plot some waveforms
#
# num_plot = min(20, num_events)
#
# fig0=plt.figure(0)
# # plt.xlim([0,num_samples-1])
# plt.grid(True)
# plt.xlabel('time [ns]')
# plt.ylabel('voltage [V]')
# plt.title('Plot of first %d events from %s'%(num_plot, filename))
#
#
# per_min = 0.
# per_max = 0.
#
# for event in range(num_plot):
#   d_uncal     = drs_data[event]
#   trigger_cell = int(drs_tc[event])
#
#   # note: without np.copy the original data would be modified!
#   d_calib = vcal.calibrate(np.copy(d_uncal), trigger_cell, channel)
#
#   t = 1e9 * (tcal.t[channel][trigger_cell:trigger_cell+1024] - tcal.t[channel][trigger_cell])
#
#   plt.plot(t,d_uncal, marker='.')
#   plt.plot(t,d_calib, marker='.')
#
#   #-------------------------------------------------------------------------------
#   # check integration difference with timing calibration
#   # use fixes area for this example, should be be waveform dependent for real measurements!
#
#   int_cell_start =   80
#   int_cell_end   =  250
#   dc_ofs         = -0.4
#
#   dt = np.roll(tcal.dt[channel], -trigger_cell)
#
#   int_no_tcal   = np.sum((d_calib[int_cell_start : int_cell_end+1] - dc_ofs)) / 5120e6
#   int_with_tcal = np.sum((d_calib[int_cell_start : int_cell_end+1] - dc_ofs) * dt[int_cell_start : int_cell_end+1])
#
#   percent = (int_no_tcal-int_with_tcal)/int_no_tcal * 100
#
#   print ("event : %3d   int_no_tcal: %15.6e    int_no_tcal: %15.6e   diff:  %15.6e  (%5.2f %%)"%(event, int_no_tcal, int_with_tcal, int_no_tcal-int_with_tcal, percent))
#
#   per_min = min(per_min, percent)
#   per_max = max(per_max, percent)
#
# print ("percent min: %5.2f %%    percent max: %5.2f %%"%(per_min ,per_max))
#
#
#
#
# #-------------------------------------------------------------------------------
# # Calculating average
#
# fig1=plt.figure(1)
# plt.xlim([0,num_samples-1])
# plt.grid(True)
# plt.xlabel('samples')
# plt.ylabel('voltage [V]')
# plt.title('Average of %d events from %s'%(num_events, filename))
#
# avg = np.zeros(num_samples, dtype=float)
# avg_cal = np.zeros(num_samples, dtype=float)
#
#
# for event in range(num_events):
#   d_uncal     = drs_data[event]
#   tigger_cell = drs_tc[event]
#
#   # note: without np.copy the original data would be modified!
#   d_calib = vcal.calibrate(np.copy(d_uncal), tigger_cell, channel)
#   avg     += d_uncal
#   avg_cal += d_calib
#
# avg     /= num_events
# avg_cal /= num_events
#
# plt.plot(avg, label='uncalibrated')
# plt.plot(avg_cal, label='calibrated')
# plt.legend()
#
# #-------------------------------------------------------------------------------
#
#
# fig0.tight_layout()
# fig1.tight_layout()
# plt.show()
#
# #-------------------------------------------------------------------------------
#
