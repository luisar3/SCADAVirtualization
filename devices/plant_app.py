# -*- coding: utf-8 -*-
"""
Created on Fri Jul 16 14:02:33 2021

@author: Luis Rodriguez
@email: Luis.Rodriguez[at]rams.colostate.edu
@company: Colorado State University
"""

import csv
from time import sleep
from datetime import datetime as dt
from pprint import pprint
from labjack import ljm

import sys

# ----- globals

time_series = {}
signal_data = {}

# ----- helpers

def get_current_time():
    raw_time = dt.now()
    current_time = raw_time.strftime("%H:%M:%S")
    return current_time

def create_filetag():
    t = dt.now().time()
    seconds = (t.hour*60 + t.minute)*60 + t.second
    return "{0}_{1}".format(dt.now().date(), seconds)

def write(handle, pin="TDAC0", v=2.0):
    return ljm.eWriteName(handle, pin, v)

def quick_write(pin="TDAC0", v=2.0):
    temp_handle = ljm.openS("T7", "USB", "ANY")
    return write(temp_handle, pin, v)

def read_analog(handle, pin="AIN0"):
    return ljm.eReadName(handle,pin)

def status_print(t, pot_value, s1_value, s2_value, err):
    print("\n"*4)
    print("---- {0} ----".format(get_current_time())
              + "\n[{0}] Potentiometer value: {1}".format(t, pot_value)
              + "\n\t > Signal 1: -/+ 1  (TDAC0) = [{0}]".format(s1_value)
              + "\n\t > Signal 2: offset (TDAC1) = [{0}]".format(s2_value)
              + "\n err: {0}".format(err))

def pins_state_print(handle, T):
    X = []
    for i in T:
        X.append(read_analog(handle, i))
    return X


# ----- main loop

def main():
    T7_id = "ANY"
    T7_handle = ljm.openS("T7", "USB", T7_id)
    T7_pins = ["TDAC0", "TDAC1"]
    
    signal1_v = 0
    signal2_offset = 0
    
    try:
        while True:
            for e in range (1000):
                # Alternate +/- 1 from base signal
                if e % 10 == 0 and e != 0:
                    if signal1_v > signal2_offset:
                        signal1_v = 0
                    else:
                        signal1_v = 1
    
                # Change offset to 2
                # > if pot is connected, this value will not matter
                if e % 100 == 0 and e != 0:
                    if signal2_offset > 0:
                        signal2_offset = 0
                    else:
                        pot_input = read_analog(T7_handle)
                        if pot_input < 1.0:
                            signal2_offset = 2
                        else:
                            signal2_offset = int(pot_input)
                
                w_error_s1 = write(T7_handle, T7_pins[0], signal1_v)
                _ = write(T7_handle, T7_pins[1], signal2_offset)
                
                pot_ain = read_analog(T7_handle)
                
                # Print the registers for LJ and see if PLC replies
                status_print(e, pot_ain, signal1_v, signal2_offset, w_error_s1)
                
                time_series[get_current_time()] = (signal1_v, signal2_offset)
                
                sleep(1)
                
    except KeyboardInterrupt:
        print("Service terminated.")
    
    # process/output time series data into CSV
    print(time_series)

def double_signal():
    # T7_id = "ANY"
    T7_handle = ljm.openS("T7", "USB", "ANY")
    T7_pins = ["TDAC0", "TDAC1"]
    T7_ain_pins = ["AIN0", "AIN1"]
    
    # reset pins
    write(T7_handle, T7_pins[0], 0)
    write(T7_handle, T7_pins[1], 0)
    
    bool1 = False
    bool2 = False
    
    print("Pins reset to 0v")
    sleep(3)
    
    try:
        for e in range(3000):
            # fix signal 1
            if bool1:
                write(T7_handle, T7_pins[0], 1)
            else:
                write(T7_handle, T7_pins[0], 0)
            bool1 = not bool1
    
            
            # fix signal 2
            if e % 10 == 0:
                if bool2:
                    write(T7_handle, T7_pins[1], 1)
                else:
                    write(T7_handle, T7_pins[1], 0)
                bool2 = not bool2
                
            # print states
            print("\n t:{0} > Pin states:".format(e))
            pins = pins_state_print(T7_handle, T7_ain_pins)
            print(pins)
            
            signal_data[e] = {"sequenceNum": e, "timestamp":get_current_time(),
                             T7_ain_pins[0]: pins[0], T7_ain_pins[1]: pins[1]}
            sleep(0.1)
    
    except KeyboardInterrupt:
        print("Done. Data being saved.\n")
    
    
    columns = signal_data[0].keys()
    try:
        with open("plant_data_{0}.csv".format(create_filetag()), "w") as csvfile:
            print("Writing to {0}...".format(csvfile.name))
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            for d in signal_data:
                writer.writerow(signal_data[d])
    except IOError as err:
        print("I/O error in CSV writing! ***\n\t{0}".format(err))
    
    print("Data saved.")
    

if __name__ == '__main__':
    
    # Plant app
    # main()
    # double_signal()
    quick_write()
    quick_write(pin="TDAC1")
    sleep(2)
    quick_write(v=0)
    quick_write(pin="TDAC1", v=0)
    
    
    print("Done.")
    

    
    