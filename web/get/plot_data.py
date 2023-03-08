#!/usr/bin/python

#Userscript - Begin cell1
import re
import subprocess
import numpy as np
import os
import soundfile
import sys
import argparse
import bokeh.plotting as bok
import platform
import xml.etree.ElementTree as etree
from numpy.lib.stride_tricks import as_strided
import platform

def int24_to_int32(f_input,f_output):
    '''Convert a binary file containing signed 24-bit integers to signed 32-bit integers'''

    with open(f_input,'rb') as f_in:
        with open(f_output,'wb') as f_out:
            bytes = f_in.read(3)
            while bytes:
                f_out.write(bytes)
                b = bytearray(bytes)
                if (b[2]&128 == 0): #The sign bit is zero, so extend with zeros
                    f_out.write(b'\x00')
                else: # The sign bit is one, so extend with ones
                    f_out.write(b'\xff') 
                bytes = f_in.read(3)


def recording_info(filename):
    recorded = os.path.basename(filename)[-14:]
    raw_disk = os.path.dirname(filename)
    fat32_disk = raw_disk[:-1] + '1'
    with open("/proc/mounts",'r') as file:
        for line in file:
            if fat32_disk in line:
                mntdir = line.split(" ")[1]
    tree = etree.parse(mntdir + '/.recordings_xml')
    disk = tree.getroot()
    recordings = disk.findall('recording')
    for recording in recordings:
        if ( recorded == recording.find('recorded').text ) :
            break
    return recording, raw_disk, mntdir + "/cache/"

def get_tag(tag_name,filename):
    
    basename, file_type = os.path.splitext(filename)
    
    if (file_type == ".flac") :
        if (tag_name == "sample-rate") :
            tag_string = subprocess.check_output(["metaflac", "--show-sample-rate",filename])
        elif (tag_name == "bps") :
            tag_string = subprocess.check_output(["metaflac", "--show-bps",filename])
        elif (tag_name == "num_channels") :
            tag_string = subprocess.check_output(["metaflac", "--show-channels",filename])
        elif (tag_name == "num_samples") :
            tag_string = subprocess.check_output(["metaflac", "--show-total-samples",filename])
        else :
            tag_string = subprocess.check_output(["metaflac", ("--show-tag=" + tag_name) ,filename]).decode("utf-8")
            if tag_string :
                tag_string = tag_string.split("=")[1]
    elif (file_type == ".bin") :
        tree = etree.parse(basename + ".xml")
        config = tree.getroot()
        if (tag_name == "num_channels") :
            tag_string = config.findall("channels")[0].text
        elif (tag_name == "num_samples") :
            fs = int(config.findall("sample-rate")[0].text)
            record_length = int(float(config.findall("record_length")[0].text))
            tag_string = "{}".format( fs * record_length)
        else :
            tag_string = config.findall(tag_name)[0].text
    
    else :
        config, raw_disk, cache_dir = recording_info(filename)
        if (tag_name == "num_channels") :
            tag_string = config.findall("channels")[0].text
        elif (tag_name == "num_samples") :
            fs = int(config.findall("sample-rate")[0].text)
            record_length = int(float(config.findall("record_length")[0].text))
            tag_string = "{}".format( fs * record_length)
        else :
            tag_string = config.find(tag_name).text
                
    return tag_string
#Userscript - End cell1

def main(args):

    source_file = args.FILE
       
#Userscript - Begin cell2

    if not ( os.path.isfile(source_file) or recording_info(source_file) ):
        print("I need a valid file!")
        sys.exit(1)

    data_file, file_type = os.path.splitext(os.path.basename(source_file))
    
    description = get_tag("description",source_file)
    fs = int(get_tag("sample-rate" ,source_file))

    #Some global variables
    if (platform.machine() == 'armv7l'):
        MAX_FFT_SIZE = np.power(2,12) #(2,15) #Running on the beaglebone, so we have limited RAM
    else:
        MAX_FFT_SIZE = fs      
    MAX_T_SIZE = np.power(2,12) #(2,15)    
    START_TIME = 0 # The time of the first sample to grab (in seconds)
    NUM_SAMPLES = max(MAX_FFT_SIZE,MAX_T_SIZE) #The number of samples to grab
    
    START = int(START_TIME * fs)
    precision = int(get_tag("bps" ,source_file))
    num_channels = int(get_tag("num_channels" ,source_file))
    total_num_samples = int(get_tag("num_samples" ,source_file))
    v_max = float(re.sub(r'[^\d-]+', '', get_tag("max",source_file)))
    v_min = float(re.sub(r'[^\d-]+', '', get_tag("min",source_file)))

    cache_dir = os.path.join(os.path.dirname(source_file),'cache/')
    if (file_type == ".flac") :
        voltage, samplerate = soundfile.read(source_file,start=START,stop=(START+NUM_SAMPLES))
    else :
        if (file_type == ".bin") :
            raw_file = source_file
            mem_start = "0"
            mem_size = os.path.getsize(source_file)
        else :
            recording, raw_file, cache_dir = recording_info(source_file)
            mem_start = recording.find("mem_start").text
            mem_size = recording.find("mem_size").text

        with open(raw_file, 'r') as f:
            f.seek(int(mem_start)+START*num_channels*precision/8)
            rawbytes = f.read(NUM_SAMPLES*num_channels*precision/8)
        with open("/dev/shm/mmap.bin",'w') as f:
            f.write(rawbytes)
        int24_to_int32("/dev/shm/mmap.bin","/dev/shm/mmap32.bin")
        v = np.fromfile("/dev/shm/mmap32.bin",dtype='int32') # Load the 32-bit binary data from file
        v = v.reshape((len(v)//num_channels,num_channels))
        voltage = v.astype(float)/np.power(2,23)
    
    voltage *= v_max
    num_samples = voltage.shape[0]
    for qq in range(num_channels):
        print("On channel {} voltages range from {} V to {} V.".format(qq+1,np.min(voltage[:,qq]),np.max(voltage[:,qq])))
        print("On channel {} the power is {}.".format(qq+1,np.sum(voltage[:,qq]**2)/num_samples))
    
    #Reduce the data if there are too many points
    Nt = min(num_samples,MAX_T_SIZE) # Number of time points to plot
    Nf = min(num_samples,MAX_FFT_SIZE) # Number of frequency domain points to plot

    delta_t = 1/float(fs)
    delta_f = 1/(float(Nf) * delta_t)
    freq = np.linspace(delta_f,Nf/2*delta_f,Nf/2)
    
    times = np.linspace(START*delta_t,(START+Nt)*delta_t,Nt,False)

    centre_frequency = 1000*np.power(2,(-18.)/3)                                 
    f_c = [centre_frequency]
    upper_limit = centre_frequency*np.power(2,1./6)
    f_e = [int(centre_frequency/np.power(2,1./6)/delta_f), int(upper_limit/delta_f)]
    while upper_limit < fs/2 :
        centre_frequency *= np.power(2,1./3)
        upper_limit = centre_frequency*np.power(2,1./6)
        f_c.append(centre_frequency)
        f_e.append(int(upper_limit/delta_f))

    #Get rid of the last entries
    f_c.pop()
    f_e.pop()
    octaves = np.zeros([len(f_c)])    
    o_x = np.roll(np.repeat(np.arange(len(f_c)+1),4),-2)
    o_x[-2:] = len(f_c)
    
    plot_width=976
    plot_height=500
    
    # create time domain plot
    time_plot = bok.figure(
        width=plot_width, 
        height=plot_height,
        title=data_file + file_type,
        x_axis_label="Time (seconds)", 
        y_axis_label="Voltage"
    )

    #Create an info box
    info_plot = bok.figure(
        width = plot_width,
        height = 300,
        y_range=[0, 1], x_range=[0,1],
        title=data_file + file_type,
        toolbar_location=None,
        tools=['reset'],
    )
    info_box = ["Description    : {}".format(description),
                "Sample Rate    : {} samples per second".format(fs),
                "Precision      : {} bit".format(precision),
                "No. of Samples : {}".format(total_num_samples),
                "Length         : {} seconds".format(total_num_samples/fs),
                ]
    for idx, line in enumerate(info_box):
        info_plot.text(0, 0.9-idx*0.1, text=[line], text_font_size="10pt") #,text_color="firebrick", text_align="center")
    info_plot.xaxis.visible=False
    info_plot.yaxis.visible=False
    info_plot.xgrid.grid_line_color = None
    info_plot.ygrid.grid_line_color = None
    
    # create frequency domain plot
    freq_plot = bok.figure(
        width=plot_width, 
        height=plot_height,
        title=u"Frequency Spectra for {}, \u0394f = {:.2f} Hz".format(data_file,delta_f),
        x_axis_label="Frequency (Hz)", 
        y_axis_label="dBV"
    )

    lower_limit = -150
    # create 1/3 octave plot
    o_plot = bok.figure(
        width=plot_width, 
        height=plot_height,
        y_range = [-150, 10],
        title=u"1/3 Octaves for {}, \u0394f = {:.2f} Hz".format(data_file,delta_f),
        x_axis_label="Bands", 
        y_axis_label="Power in band (dB)"
    )
    [o_plot.text(idx+0.9,lower_limit+1,text=[int(k)],angle=np.pi/2,text_font_size="9pt") for idx, k in enumerate(f_c)]
    
    colors = ['red','blue','green','magenta','cyan','yellow','black','orange']
    channel = []
    for x in range(num_channels):
        channel.append({})
        channel_tag = get_tag("channel_{}".format(x+1),source_file)
        if channel_tag:
            channel[x]['num'] = x + 1
            channel[x]['tag'] = "Ch {}".format(x+1)
            channel[x]['label'] = "Ch {} : ".format(x+1) + channel_tag
            channel[x]['voltage'] = voltage[:,x]
            
            #Time domain plots
            time_plot.line( times , channel[x]['voltage'][0:Nt], 
                           legend=channel[x]['tag'],
                           color=colors[x]
                          )

            #Info box
            info_plot.line(1,1, legend=channel[x]['label'], color=colors[x])
            
            #Frequency domain plots
            #Fourier transform the data
            window_function = np.hanning(Nf)
            #window_function = np.ones([Nf])
            windowed_data = np.multiply( channel[x]['voltage'][0:Nf] , window_function ) 
            print("On channel {} the windowed power in the input is {}.".format(x+1,np.sum(windowed_data**2)/Nf))
            F = np.fft.fft(windowed_data)/Nf
            print("On channel {} the power of all frequencies is {}.".format(x+1,np.sum(np.real(F*np.conjugate(F)))))
            F = F[1:int(Nf/2)+1]
            P = np.real(F*np.conjugate(F))
            print("On channel {} the max frequency power is {} V at {} Hz.".format(x+1,np.max(P),freq[np.argmax(P)]))
            print("On channel {} the power of all frequencies is {}.".format(x+1,np.sum(2*P)))
            freq_plot.line( freq, 10*np.log10(P), 
                           legend=channel[x]['tag'],
                           color=colors[x]
                          )
            for idx, c_f in enumerate(f_c) :
                freq_plot.line(c_f*np.ones(2),np.array([-130,-2*idx]),color='blue')
                lb = (1-0.232/2)*c_f
                ub = (1+0.232/2)*c_f
                freq_plot.line(np.array([lb,lb,ub,ub]),np.array([-130,-2*idx,-2*idx,-130]),color='green')
            
            #1/3 Octave plot
            for idx, c_f in enumerate(f_c) :
                octave_power = np.sum(P[f_e[idx]:f_e[idx+1]],0)/(0.232*c_f)
                octave_power = 10*np.log10(np.max([octave_power,1e-15]))
                octaves[idx] = octave_power
            print("On channel {} the max 1/3 octave band level is {} at {} Hz.".format(x+1,np.max(octaves),f_c[np.argmax(octaves)]))
            o_y = 0.*o_x.astype('float64') + lower_limit
            for idx, octave_power in enumerate(octaves) :
                o_y[idx*4+1] = octave_power
                o_y[idx*4+2] = octave_power
            o_plot.line(o_x,o_y,legend=channel[x]['tag'],color=colors[x])
            
    info_plot.legend.location = "bottom_center"        
    p = bok.vplot(time_plot, info_plot, freq_plot, o_plot)
#Userscript - End cell2     
    
    if not os.path.isdir(cache_dir):
        os.mkdir(cache_dir)
    html_file = os.path.join(cache_dir,data_file + ".html")
    jupyter_file = os.path.join(cache_dir,data_file + ".ipynb")

    ref_str = "<p>Click <a href='SDcard/cache/"
    ref_str = ref_str + data_file + ".ipynb' download>here</a> to analyse this data using "
    ref_str = ref_str + "<a href='http://www.scipy.org' target='_blank'>SciPy</a> in a "
    ref_str = ref_str + "<a href='http://www.jupyter.org' target='_blank'>Jupyter Notebook</a>.</p>"

    bok.output_file(html_file, title=data_file, autosave=False, mode='cdn')
    bok.save(p)
    with open(html_file, "r") as sources:
        filedata = sources.read()
    filedata = filedata.replace('</body>', ref_str + '</body>')
    #Uncomment the next two lines to use local resources
    #filedata = filedata.replace('href="https://cdn.pydata.org/bokeh/release/', 'href="stylesheets/')
    #filedata = filedata.replace('src="https://cdn.pydata.org/bokeh/release/', 'src="js/')   
    with open(html_file, "w") as sources:
        sources.write(filedata)
            
        
    with open(__file__, "r") as f:
        script_str = f.readlines()
    
    current_cell = 0
    cell1 = []
    cell2 = []
    cell2.append(("source_file = \"" + data_file + ".flac" + "\"\n").replace('\\','\\\\').replace('\n','\\n').replace('"', '\\"'))
    cell2.append(("bok.output_notebook()\n").replace('\\','\\\\').replace('\n','\\n').replace('"', '\\"'))
    for line in script_str:
        if line.startswith("#Userscript - Begin cell1"):
            current_cell = 1
            continue
        if line.startswith("#Userscript - Begin cell2"):
            current_cell = 2
            continue
        if line.startswith("#Userscript - End"):
            current_cell = 0            
        if current_cell == 1:
            cell1.append(line.replace('\\','\\\\').replace('\n','\\n').replace('"', '\\"'))
        if current_cell == 2:
            cell2.append(line[4:].replace('\\','\\\\').replace('\n','\\n').replace('"', '\\"'))
    cell2.append("bok.show(p)".replace('\\','\\\\').replace('\n','\\n').replace('"', '\\"'))
    
    juypter_str = '''{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [\n    "''' + '",\n    "'.join(cell1) + '''"\n   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {
    "collapsed": true
   },
   "outputs": [],
   "source": [\n    "''' + '",\n    "'.join(cell2) + '''"\n   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 2",
   "language": "python",
   "name": "python2"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 2
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython2",
   "version": "2.7.6"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 0
}
'''
    
    with open(jupyter_file, "w") as f:
        f.write(juypter_str)
    
if __name__ == '__main__':
    
    help_text = '''
    This script takes a data file as input, and produces some plots using the first set of points.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument('-v', '--verbose', help="Show some additional info, useful for debugging.",action="store_true")
    parser.add_argument("FILE", help="a flac or binary file contained on the SD card attached to the BBB.")
    args = parser.parse_args()  
    if args.FILE is None :
        parser.print_help()
        print("You need to supply a valid data file.")
        sys.exit(1)
    main(args)