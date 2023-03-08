#!/usr/bin/python

#Userscript - Begin cell1
import re
import subprocess
import numpy as np
import os
import sys
import argparse
import bokeh.plotting as bok
import platform
import xml.etree.ElementTree as etree
import platform
from bokeh.models import ColumnDataSource, HoverTool, CustomJS, Slider
#from bokeh.layouts import column, row, widgetbox

def recording_info(filename):
    recorded = os.path.basename(filename)[-14:]
    mntdir = os.path.dirname(filename)
    tree = etree.parse(mntdir + '/.octaves_xml')
    disk = tree.getroot()
    recordings = disk.findall('recording')
    for recording in recordings:
        if ( recorded == recording.find('recorded').text ) :
            break
    return recording, mntdir + "/cache/"

def get_tag(tag_name,filename):
    
    basename, file_type = os.path.splitext(filename)
    
    if (platform.machine() == 'armv7l'):
        config, cache_dir = recording_info(basename)
    else:
        tree = etree.parse(basename + ".xml")
        config = tree.getroot()
    if (tag_name == "num_channels") :
        tag_string = config.find("channels").text
    elif (tag_name == "num_samples") :
        fs = int(config.find("sample-rate").text)
        record_length = int(float(config.find("record_length").text))
        tag_string = "{}".format( fs * record_length)
    else :
        tag_string = config.find(tag_name).text
                    
    return tag_string

def get_octave_data(filename,channel):
    print("{} {}".format(filename,channel))
    return 
#Userscript - End cell1

def main(args):

    source_file = args.FILE
       
#Userscript - Begin cell2

    if (platform.machine() != 'armv7l') and not os.path.isfile(source_file) :
        print("I need a valid file!")
        sys.exit(1)

    data_file, file_type = os.path.splitext(os.path.basename(source_file))
    data_dir = os.path.dirname(source_file)
    cache_dir = os.path.join(data_dir,'cache/')
        
    description = get_tag("description",source_file)
    fs = int(get_tag("sample-rate" ,source_file))
    fft_size = int(get_tag("fft_size",source_file))
    delta_f = float(fs)/float(fft_size)
    num_channels = int(get_tag("channels",source_file))
    record_length = int(get_tag("record_length",source_file))
    f_c = np.fromstring(get_tag("centre_frequencies",source_file)[1:-1],sep=',')
    num_bands = len(f_c)
    
    lower_limit = -150
    num_lines = sum(1 for line in open(source_file))
    i = np.zeros([num_lines])
    timestamp = np.zeros([num_lines])
    fft_time = np.zeros([num_lines])
    octaves = np.zeros([num_lines,num_channels,num_bands])
    o_x = np.roll(np.repeat(np.arange(num_bands+1),4),-2)
    o_x[-2:] = num_bands
    o_y = np.zeros([num_lines,num_channels,len(o_x)]) + lower_limit

    with open(source_file,'r') as f:
        for idx, s in enumerate(f):
            i[idx] = int(s[1:s.find(',')])
            s = s[s.find(',')+1:]
            timestamp[idx] = int(s[:s.find(',')])
            s = s[s.find(',')+1:]
            fft_time[idx] = int(s[:s.find(']')])
            for x in range(num_channels):
                octave = [float(q) for q in s[s.find('[[')+2:s.find(']]')].split()]
                s = s[s.find(']]')+2:]
                octaves[idx,x,:] = np.array(octave)
                for idx2, octave_power in enumerate(np.array(octave)) :
                    o_y[idx,x,idx2*4+1] = octave_power
                    o_y[idx,x,idx2*4+2] = octave_power
    
    plot_width=976
    plot_height=500
 
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
                "FFT Size       : {}".format(fft_size),
                "Length         : {} seconds".format(record_length),
                ]
    for idx, line in enumerate(info_box):
        info_plot.text(0, 0.9-idx*0.1, text=[line], text_font_size="10pt") #,text_color="firebrick", text_align="center")
    info_plot.xaxis.visible=False
    info_plot.yaxis.visible=False
    info_plot.xgrid.grid_line_color = None
    info_plot.ygrid.grid_line_color = None

    special_channel = num_channels - 1
    
    colors = ['red','blue','green','magenta','cyan','yellow','black','orange']
    rect_source = ColumnDataSource(data=dict(h1=[0], h2=[2], color=['red'], colors=colors))
    bar_source = ColumnDataSource(data=dict(x=[o_x], y=[o_y[0,special_channel,:]]))
    octave_values = ColumnDataSource(data=dict(o_y=o_y,octaves=octaves,last_channel=[special_channel]))
        
    # create image plot
    image_plot = bok.figure(
        width=plot_width, 
        height=plot_height,
        x_range=[0, num_bands],
        y_range=[0, num_lines],
        title=u"{}, \u0394f = {:.2f} Hz".format(data_file,delta_f),
        x_axis_label="1/3 Octave Bands", 
        y_axis_label="FFT snapshot"
    )
    im = image_plot.image(image=[octaves[:,special_channel,:]], x=[0], y=[0], dw=[num_bands], dh=[num_lines], palette="Spectral11")
    
    #print(octave_values.data)
    #print(im.data_source.data)
    
    callback = CustomJS(args=dict(rect_source=rect_source, bar_source=bar_source, octave_values=octave_values, image_source=im.data_source), code="""
    var rect_data = rect_source.get('data');
    h1 = rect_data['h1'];
    h2 = rect_data['h2'];
    var current_timestep = time_slider.get('value');
    h1[0] = 2*current_timestep;
    h2[0] = 2*current_timestep + 2;
    
    var current_channel = channel_slider.get('value') - 1;
    
    var octave_data = octave_values.get('data');
    o_y = octave_data['o_y'];
    octaves = octave_data['octaves'];
    lc = octave_data['last_channel'];
    var last_channel = lc[0];
   
    var bar_data = bar_source.get('data');
    y = bar_data['y'];
    for (x = 0; x < y.length; x++){
        y[x] = o_y[current_timestep][current_channel][x];
    }
    
    if (last_channel != current_channel) 
    {
        var image_data = image_source.get('data');
        lc[0] = current_channel;
        image = image_data['image'];
        for (x = 0; x < octaves.length; x++ ){
            for (k = 0; k < octaves[0][0].length; k++){
                image[0][x][k] = octaves[x][current_channel][k];
            }
        }
    }
             
    bar_source.trigger('change');
    rect_source.trigger('change');
    image_source.trigger('change');
    """)
    
    time_slider = Slider(title="Time", start=0, end=num_lines-1, value=0, step=1, callback=callback)
    callback.args['time_slider'] = time_slider
    channel_slider = Slider(title="Channel", start=1, end=num_channels, value=num_channels, step=1, callback=callback)
    callback.args['channel_slider'] = channel_slider

    image_plot.rect(0, 0, width=2*num_bands, height='h1', fill_color=None, source=rect_source)
    image_plot.rect(0, 0, width=2*num_bands, height='h2', fill_color=None, source=rect_source)
        
    # create 1/3 octave plot
    o_plot = bok.figure(
        width=plot_width, 
        height=plot_height,
        y_range = [-150, 10],
        title=data_file,
        x_axis_label=u"1/3 Octave bands, \u0394f = {:.2f} Hz".format(delta_f), 
        y_axis_label="Power in band (dB)",
    )
    [o_plot.text(idx+0.9,lower_limit+1,text=[int(k)],angle=np.pi/2,text_font_size="9pt") for idx, k in enumerate(f_c)]
    
    for x in range(num_channels):
        channel_tag = get_tag("channel_{}".format(x+1),source_file)
        if channel_tag:            
            info_plot.line(1,1, legend="Ch {} : {}".format(x+1,channel_tag), color=colors[x]) #Info box
            
    o_plot.line(o_x,o_y[0,special_channel,:], color=colors[x], source=bar_source) #1/3 Octave plot
            
    info_plot.legend.location = "bottom_center"        
    p = bok.vplot(info_plot, channel_slider, image_plot, time_slider, o_plot)
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
    cell2.append(("source_file = \"" + data_file + ".octaves" + "\"\n").replace('\\','\\\\').replace('\n','\\n').replace('"', '\\"'))
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
    This script takes a **data file as input, and produces some plots of third octaves.
    '''
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=help_text)
    parser.add_argument('-v', '--verbose', help="Show some additional info, useful for debugging.",action="store_true")
    parser.add_argument("FILE", help="an .octaves file.")
    args = parser.parse_args()  
    if args.FILE is None :
        parser.print_help()
        print("You need to supply a valid data file.")
        sys.exit(1)
    main(args)