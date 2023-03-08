#!/usr/bin/env python
import numpy as np
import os
import subprocess
import datetime
import time
import struct
import sys
import re
from bokeh.plotting import figure, curdoc, show
from bokeh.io import output_notebook
from bokeh.layouts import gridplot
import socket


def is_script():
    '''Tests whether the code is being executed within a script file'''
    try:
        os.path.basename(__file__) 
    except Exception as e:
        return False
    return True


def setup_plot():
    '''Reset the various x-labels and data points'''
    global o_plot
    #Clear the log lines
    for x in plot_extras['error_log']:
        x.data_source.data['text'] = ['']

    o_plot.title.text="Recording from Beaglebone Black Acquisition System"
    

# -----------------------------------------------------------------------
# update_data function
#------------------------------------------------------------------------
def update_data():
    
    global o_plot, plot_extras, num_drops, renew_plot

    #data = "[28 60 1466749370 1977509]"
    try:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    except Exception as e:
        return
    data = data.decode("utf-8") 
    #print(data)
    if ( len(data) >= 8) and (data[:8] == 'Finished'):
        o_plot.title.text = o_plot.title.text + ' Finished'
        renew_plot = True
        num_drops = 0
        return
    
    [i,num_grabs,timestamp,spare_time] = [int(k) for k in data[1:-1].split(' ')]
    
    if renew_plot:
        renew_plot = False
        print("Resetting graph")
        if is_script():
            curdoc().remove_periodic_callback(update_data)
        setup_plot()
        if is_script():
            curdoc().add_periodic_callback(update_data, UPDATE_TIME)
        return
    
    (plot_extras['RECORD_level']).data_source.data['x'] = [0, 0, float(i)/float(num_grabs), float(i)/float(num_grabs)]
    o_plot.title.text = datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M:%S %d/%m/%Y")
    cpu_percent = (1 - spare_time/1000000.)
    (plot_extras['CPU_percent']).data_source.data['text'] = ["{:0.2f}%".format(100*cpu_percent)]
    if (cpu_percent > 1):
        num_drops = num_drops + 1
        if (num_drops <= log_max_lines):
            tmp_str = "Dropped packet {} at {}".format(i,datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d%H%M%S"))
            plot_extras['error_log'].append(o_plot.text(0,1-num_drops*base_skip,text=[tmp_str],alpha=0.5))
    (plot_extras['CPU_level']).data_source.data['y'] = [0, cpu_percent, cpu_percent, 0]
    o_plot.xaxis.axis_label = "{}/{}    ({} dropped packets)".format(i,num_grabs,num_drops)

# -----------------------------------------------------------------------
# Initialize some various variables
#------------------------------------------------------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 5004
num_grabs = 1

#Create the UDP receiving UDP socket
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
UPDATE_TIME = 500 #Milliseconds between running update()
print("The plot will be updated every {} milliseconds".format(UPDATE_TIME))
sock.settimeout(float(UPDATE_TIME)/(4*1000)) #Set socket timeout to 1/4 of update interval
sock.bind((UDP_IP, UDP_PORT))

renew_plot = False

# create a new plot with a title and axis labels
o_plot = figure(
     x_range = [0, 1.2],
    y_range = [0, 1.3],
    width = 800,
    height = 200,    
    toolbar_location=None
)
o_plot.title.text="Recording from Beaglebone Black Acquisition System"
o_plot.title.text_font_size='12pt'
o_plot.xaxis.major_label_text_font_size = '0pt'  # Turn off tick labels
o_plot.xaxis.major_tick_line_color = None  # turn off major ticks
o_plot.yaxis.major_label_text_font_size = '0pt'  # Turn off tick labels
o_plot.yaxis.major_tick_line_color = None  # turn off major ticks
o_plot.xgrid.grid_line_color = None # turn off x grid
o_plot.ygrid.grid_line_color = None # turn off y grid
o_plot.xaxis[0].major_tick_line_color = None  # turn off major ticks
o_plot.xaxis[0].ticker.num_minor_ticks = 0  # turn off minor ticks
o_plot.yaxis[0].major_tick_line_color = None  # turn off major ticks
o_plot.yaxis[0].ticker.num_minor_ticks = 0
left_align = 1.1
box_width = 0.1
base_skip = 1./5
log_max_lines = 5
num_drops = 0
plot_extras = {}
plot_extras['CPU_percent'] = o_plot.text(left_align,1,text=['CPU%'])
plot_extras['error_log'] = []
plot_extras['RECORD_BOX'] = o_plot.patch(
    [0, 0, 1, 1], 
    [0, 1, 1, 0],
    alpha=0.1, line_width=4,color="black")
plot_extras['RECORD_level'] = o_plot.patch(
    [0, 0, 0, 0], 
    [0, 1, 1, 0],
    alpha=0.8, line_width=2,color="red")
plot_extras['CPU_BOX'] = o_plot.patch(
    [left_align, left_align, left_align+box_width, left_align+box_width], 
    [0, 1, 1,0],
    alpha=0.8, line_width=4,line_color="black")
plot_extras['CPU_level'] = o_plot.patch(
    [left_align, left_align, left_align+box_width, left_align+box_width], 
    [0,0,0,0],
    alpha=0.8, line_width=2,color="green")

setup_plot()

if is_script():
    curdoc().add_root(o_plot)
    curdoc().add_periodic_callback(update_data, UPDATE_TIME)
else:
    output_notebook()
    show(o_plot)
    #%run ./simulate_third_octaves.py -v -t 2 -i 0.0.0.0
    for q in range(8):
        update_data()
    show(o_plot)