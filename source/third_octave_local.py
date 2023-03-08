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
    global o_plot, freq_bin, bar_graph
    [num_channels,sample_rate,fft_size,lower_limit,upper_limit] = current_settings
    
    #Calculate the bands that we are using
    # f_c is a list of the centre frequency
    # The 19th centre frequency is defined to be 1000 Hz
    centre_frequency = 1000*np.power(2,(-18.)/3)                                 
    f_c = [int(round(centre_frequency))]
    upper_frequency = centre_frequency*np.power(2,1./6)
    while upper_frequency < sample_rate/2 :
        centre_frequency *= np.power(2,1./3)
        upper_frequency = centre_frequency*np.power(2,1./6)
        f_c.append(int(round(centre_frequency)))
    f_c.pop() #Get rid of the last entries
        
    #Set the x-labels and bar graphs
    for x in freq_bin[:len(f_c)]:
        x.glyph.text_color = 'black'
    for x in freq_bin[len(f_c):]:
        x.glyph.text_color = None
    for x in range(8):
        bar_graph[x].data_source.data["y"] = np.zeros(4*len(f_c)) + lower_limit
    #Clear the log lines
    for x in plot_extras['error_log']:
        x.data_source.data['text'] = ['']

    o_plot.xaxis.axis_label = u'1/3 Octave Bands ({} SPS, {} points, \u0394f = {:.2f} Hz)'.format(
        sample_rate,
        fft_size,
        float(sample_rate)/float(fft_size)
    )
    o_plot.title.text="1/3 Octaves"
    o_plot.x_range.start = 0
    o_plot.x_range.end = len(f_c) + 4 #Add space for the legend
    o_plot.y_range.start = lower_limit
    o_plot.y_range.end = upper_limit
    

# -----------------------------------------------------------------------
# update_data function
#------------------------------------------------------------------------
def update_data():
    
    global o_plot, plot_extras, freq_bin, bar_graph, current_settings, num_drops, renew_plot

    try:
        #data = "[10,10,2,97656,97656,1467101236,511193][[-57.78 -58.08 -54.32 -55.58 -54.75 -54.16 -52.80 -50.99 -41.15 -22.91 -26.31 -36.03 -23.01 -24.23 -19.97 -21.01 -20.47 -27.40 -27.84 -29.99 -34.20 -40.18 -36.31 -38.94 -45.53 -61.65 -60.90 -63.65 -71.60 -82.21 -82.31 -82.15 -82.19 -82.08 -82.14 -100.00 ]][[-57.92 -57.93 -53.97 -55.42 -54.70 -54.23 -52.88 -50.94 -41.16 -22.92 -26.32 -36.03 -23.01 -24.23 -19.98 -21.01 -20.48 -27.40 -27.85 -30.00 -34.21 -40.18 -36.32 -38.94 -45.53 -61.66 -60.88 -63.65 -71.72 -82.31 -82.56 -82.39 -82.48 -82.56 -82.55 -100.00 ]]"
        #data = "[20,20,2,130208,130208,1467100678,735364][[-42.79 -39.06 -42.83 -37.66 -30.61 -31.49 -24.59 -7.45 -27.28 -28.47 -24.32 -21.51 -37.32 -35.76 -38.21 -41.53 -37.64 -37.49 -37.99 -35.35 -36.83 -40.99 -38.81 -41.44 -45.02 -47.20 -48.81 -51.72 -56.62 -59.33 -77.77 -83.68 -83.85 -83.97 -83.81 -83.84 -100.00 ]][[-39.84 -38.91 -42.65 -39.68 -27.26 -32.12 -23.27 -6.31 -25.30 -28.53 -23.26 -22.15 -35.57 -33.53 -37.48 -42.67 -37.37 -38.33 -41.43 -36.08 -37.49 -41.50 -39.86 -41.97 -45.44 -47.35 -49.05 -52.94 -57.43 -61.82 -78.18 -84.17 -84.16 -84.13 -84.23 -84.22 -100.00 ]]"
        data, addr = sock.recvfrom(1400) # buffer size is 1400 bytes
    except Exception as e:
        return
    data = data.decode("utf-8") 
    #print(current_settings)
    #print(data)
    if ( len(data) >= 8) and (data[:8] == 'Finished'):
        o_plot.title.text = o_plot.title.text + ' Finished'
        renew_plot = True
        num_drops = 0
        return
    
    [header,values] = data.split(']',1)
    [i,num_grabs,num_channels,sample_rate,fft_size,timestamp,fft_time] = [int(k) for k in header[1:].split(',')]
    
    if renew_plot or current_settings[:3] != [num_channels,sample_rate,fft_size] :
        renew_plot = False
        print("Resetting graph")
        current_settings[:3] = [num_channels,sample_rate,fft_size]
        if is_script():
            curdoc().remove_periodic_callback(update_data)
        UPDATE_TIME = int(float(fft_size)/float(sample_rate)*1000)/2 #Milliseconds between running update() (half the actual rate)
        print("The plot will be updated every {} milliseconds".format(UPDATE_TIME))
        sock.settimeout(float(UPDATE_TIME)/(4*1000)) #Set socket timeout to 1/4 of update interval
        setup_plot()
        if is_script():
            curdoc().add_periodic_callback(update_data, UPDATE_TIME)
        return
    
    for x in range(num_channels):
        octave = [float(q) for q in values[values.find('[[')+2:values.find(' ]]')].split()]
        values = values[values.find(']]')+2:]
        o_y = 0.*o_x.astype('float64') + lower_limit
        for idx, octave_power in enumerate(octave) :
            o_y[idx*4+1] = octave_power
            o_y[idx*4+2] = octave_power
        bar_graph[x].data_source.data["y"] = 1.*o_y

    (plot_extras['grab_number']).data_source.data['text'] = ["{}/{}".format(i,num_grabs)]
    (plot_extras['date']).data_source.data['text'] = [datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y")]
    (plot_extras['time']).data_source.data['text'] = [datetime.datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")]
    cpu_percent = (fft_time/1000000.)/(float(fft_size)/float(sample_rate))
    (plot_extras['CPU_percent']).data_source.data['text'] = ["{:0.2f}%".format(100.*cpu_percent)]
    if (cpu_percent > 1) and (num_drops < log_max_lines):
        num_drops = num_drops + 1
        tmp_str = "Dropped packet {} at {}".format(i,datetime.datetime.fromtimestamp(timestamp).strftime("%Y%m%d%H%M%S"))
        plot_extras['error_log'].append(o_plot.text(1,upper_limit+num_drops*base_skip,text=[tmp_str],alpha=0.2))
    (plot_extras['CPU_level']).data_source.data['y'] = [box_base, box_base+cpu_percent*box_height, box_base+cpu_percent*box_height,box_base]

# -----------------------------------------------------------------------
# Initialize some various variables
#------------------------------------------------------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
num_grabs = 1
sample_rate = 130208
fft_size = 130208
num_channels = 2
N = sample_rate
f_c = [16.0, 20.0, 25.0, 31.0, 39.0, 50.0, 63.0, 79.0, 99.0, 125.0, 157.0, 198.0, 250.0, 315.0, 397.0, 
       500.0, 630.0, 794.0, 1000.0, 1260.0, 1587.0, 2000.0, 2520.0, 3175.0, 4000.0, 5040.0, 6350.0, 8000.0, 10079.0, 
       12699.0, 16000.0, 20159.0, 25398.0, 32000,40317,50797]

#Create the UDP receiving UDP socket
sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
UPDATE_TIME = int(float(fft_size)/float(sample_rate)*1000)/2 #Milliseconds between running update()
print("The plot will be updated every {} milliseconds".format(UPDATE_TIME))
sock.settimeout(float(UPDATE_TIME)/(4*1000)) #Set socket timeout to 1/4 of update interval
sock.bind((UDP_IP, UDP_PORT))

upper_limit = 10
lower_limit = -150
renew_plot = False

# create a new plot with a title and axis labels
o_plot = figure(
    y_axis_label='Power in band (dB)',
    #x_range = [0, 38],
    width = 1200,
    height = 600,    
    toolbar_location=None
)
o_plot.title.text = "1/3 Octaves"
o_plot.title.text_font_size='12pt'
o_plot.xaxis.major_label_text_font_size = '0pt'  # Turn off tick labels
o_plot.xaxis.major_tick_line_color = None  # turn off major ticks
o_x = np.roll(np.repeat(np.arange(len(f_c)+1),4),-2)
o_x[-2:] = len(f_c)
freq_bin = [o_plot.text(idx+0.9,lower_limit+1,text=[k],angle=np.pi/2,text_font_size="9pt") for idx, k in enumerate(f_c)]
colors = ['red','blue','green','magenta','cyan','yellow','black','orange']
bar_graph = [o_plot.line(o_x,0*o_x.astype('float64') + lower_limit,color=colors[x], legend="Channel {}".format(x+1)) for x in range(8)]
left_align = len(f_c) + 0.5
base_height = (upper_limit+lower_limit)/2 + 5
base_skip = -(upper_limit-lower_limit)/20
box_base = base_skip*8.2+base_height
box_height = -5*base_skip
log_max_lines = 15
num_drops = 0
plot_extras = {}
plot_extras['grab_number'] = o_plot.text(left_align,base_height,text=['x/x'])
plot_extras['date'] = o_plot.text(left_align,base_height+base_skip,text=['Date'])
plot_extras['time'] = o_plot.text(left_align,base_height+2*base_skip,text=['Time'])
plot_extras['CPU_percent'] = o_plot.text(left_align,base_height+3*base_skip,text=['CPU%'])
plot_extras['error_log'] = []
plot_extras['CPU_BOX'] = o_plot.patch(
    [left_align, left_align, left_align+3, left_align+3], 
    [box_base, box_base+box_height, box_base+box_height,box_base],
    alpha=0.8, line_width=4,line_color="black")
plot_extras['CPU_level'] = o_plot.patch(
    [left_align, left_align, left_align+3, left_align+3], 
    [box_base,box_base,box_base,box_base],
    alpha=0.8, line_width=2,color="green")

current_settings = [num_channels,sample_rate,fft_size,lower_limit,upper_limit]
setup_plot()

if is_script():
    curdoc().add_root(o_plot)
    curdoc().add_periodic_callback(update_data, UPDATE_TIME)
else:
    output_notebook()
    show(o_plot)
    #%run ./simulate_third_octaves.py -v -t 2 -i 0.0.0.0
    for q in range(5):
        update_data()
    show(o_plot)