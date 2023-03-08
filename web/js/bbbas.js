
/*global $, jQuery, document */
$.ajaxSetup({cache: false});

function doLoad() {
    "use strict";
	
	js_updateTime();

	js_run_code('list_recordings','recordings');
	
	js_run_code('list_octaves','octaves');
    
	js_check_server();

	js_run_code("refresh_config","configuration");
    
}

/**
\brief Initialize all jQuery functions etc.

*/
$(document).ready(function () {
	"use strict";
	
	if ($("#Poweroff").length) {
		doLoad();
	}
});

function js_check_server() {
    "use strict"
    var keepAliveTimeout = 1000 * 1;
    var mode = $('#mode').html();
    $.ajax(
    {
        type: 'GET',
        url: 'test.html',
        success: function(data)
        {
            if (mode == 'refresh_ready') {
                js_run_code('list_recordings','recordings');
                js_run_code('list_octaves','octaves');
                $('#mode').html("mode");
            }
            //Server is up and running, so device is not recording.
            //Show Record buttons and hide bokeh plots
            $('#record_div').show();
            $('#octave_plot').hide();
            $('#record_progress').hide();
            setTimeout(function()
            {
                js_check_server();
            }, keepAliveTimeout);
        },
        error: function(XMLHttpRequest, textStatus, errorThrown)
        {
            if (mode != 'refresh_ready') {
                //Server is not running, so device is probably recording.
                //Hide Record buttons and show bokeh plots
                $('#record_div').hide();
                if (mode == 'record_button') {
                    //We are recording voltages
                    $('#record_progress').show();
                } else if (mode == 'octaves_button')  {
                    //We are recording octaves
                    $('#octave_plot').show();
                } else {
                    //I don't know which mode we are in, show both plots
                    $('#record_progress').show();
                    $('#octave_plot').show();
                }
                $('#mode').html("refresh_ready");
            }             
            setTimeout(function(){ js_check_server(); }, keepAliveTimeout);
        }
    });    
}

function js_updateTime() {
    "use strict";
    js_run_code('get_status','status');	
	setTimeout(js_updateTime, 60 * 1000);
}

function js_shutdown() {
    "use strict";
	$("<div title='Shut down?'>Are you sure you want to poweroff?</div>").dialog({
		resizable: false,
		height:'auto',
		width:'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Shutdown": function() {
				js_run_code('shutdown','debug');
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_clear_cache() {
    "use strict";
	$("<div title='Clear Cache?'>Are you sure you want to clear the cache of plots?</div>").dialog({
		resizable: false,
		height:'auto',
		width:'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Clear Cache": function() {
				js_run_code('clear_cache','debug');
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_restart_jupyter() {
    "use strict";
	$("<div title='Restart Jupyter?'>Are you sure you want to restart the jupyter kernel?</div>").dialog({
		resizable: false,
		height:'auto',
		width:'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Restart": function() {
				js_run_code('restart_jupyter','debug');
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_format_sd() {
    "use strict";
	$("<div title='Format the SD card?'>Are you sure you want to format the SD card? ALL RECORDED DATA WILL BE LOST!!!</div>").dialog({
		resizable: false,
		height:'auto',
		width:'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Format": function() {
				js_run_code('format_sd','debug');
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_update_config(obj) {
    "use strict";
    var i;
	var num_channels = parseInt($("#num_channels option:selected").text());
	var arg_array = ["update_config","debug",
		"filename",$("#filename").val(),
		'record_length',$("#record_length").val(),
		'sample_rate',$("#sample_rate option:selected").text(),
		'num_channels',$("#num_channels option:selected").text(),
		'description',$("#description").val(),
		'shift',$("#shift_channels").prop("checked"),
        'fft_size',$("#fft_size").val(),
        'mode',$("#mode").html(),
		];
	for (i = 1; i <= num_channels; i += 1) {
		arg_array.push( "channel_" + i, check_str($("#channel_" + i).val()));
	}
	js_run_code.apply(null, arg_array);
}

function js_restore_config(obj) {
    "use strict";
	$("<div title='Restore defaults?'>Restore filename, channel descriptions, etc to default values?</div>").dialog({
		resizable: false,
		height:300,
		width:500,
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Yes": function() {
				js_run_code("restore_config","configuration");
				$(this).dialog('destroy').remove();
			},
			"No": function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_save_config(obj) {
    "use strict";
    js_update_config(obj);
    var num_configs = $('#config_xmls option').size() - 1; 
    var saved_configs;
    if ( num_configs ) {
		saved_configs = $( "<select id='saved_configs' name='saved_configs' size='" + num_configs + "'></select>" );
		saved_configs.change(function() {
			$("#xml_filename").val($("#saved_configs").find("option").filter(":selected").text());
		});
		$("#config_xmls > option").each(function() {
			if (this.text) {
				saved_configs.append("<option>"+ this.text.substr(0,this.text.lastIndexOf(".")) + "</option>");
			}
		});
	}
	var dialog_box = $("<div title='Save configuration as ...'></div>");
	dialog_box.append(saved_configs);
	dialog_box.append("<br/><input id='xml_filename' type='text' title='Enter a filename for the XML file' style='width:200px;' value='" + $("#filename").val() + "' />.xml");
	dialog_box.dialog({
		height:'auto',
		width:'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			OK: function() {
				js_run_code("save_config","configuration","xml_file",$('#xml_filename').val());
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_record(obj) {
    "use strict";
    var mode = $(obj).attr('id');
    $("#mode").html(mode);
    js_update_config(obj);
    js_run_code('start_stop','debug');
}

function js_change_channels(obj) {
    "use strict";
    var max_channels = 8;
    var num_channels = parseInt($("#num_channels option:selected").text());
    var channel_box, i;
    for (i = 1; i <= num_channels; i += 1) {
		//Create the channel boxes if they don't exist
		if (! $("#channel_" + i).length) {
			$( "<tr><td>Channel " + i + "</td> \
						<td><textarea id='channel_" + i + "' title='Short description of the data being recorded on channel' rows='3' cols='50' style='resize:none;' maxlength='65536'>Channel " + i + "</textarea></td></tr>" ).insertAfter($("#description_table").find("tr").last());
		}
	}
    for (i = num_channels+1; i <= max_channels; i += 1) {
		//Delete the channel boxes if they do exist
		if ($("#channel_" + i).length) $("#channel_" + i).parents("tr").remove();
    }
}

function js_load_config(obj) {
    "use strict";
 	js_run_code("load_config","configuration","xml_file",$('#config_xmls').find("option").filter(':selected').text());
}

function js_delete_config(obj) {
    "use strict";
	js_run_code("delete_config","configuration","xml_file",$('#config_xmls').find("option").filter(':selected').text());
}

function js_toggle(obj,element_id) {
    "use strict";
    if ( $('#' + element_id).hasClass('hide') ) {
		$(obj).html($(obj).html().replace(/Show/,'Hide'));
		$(obj).val($(obj).val().replace(/Show/,'Hide'));
		$('#' + element_id).removeClass('hide');
	} else {
		$(obj).html($(obj).html().replace(/Hide/,'Show'));
		$(obj).val($(obj).val().replace(/Hide/,'Show'));
		$('#' + element_id).addClass('hide');
	}
}

function js_toggle_next(obj) {
    "use strict";
    if ( $(obj).next().hasClass('hide') ) {
		$(obj).html($(obj).html().replace(/Show/,'Hide'));
		$(obj).next().removeClass('hide');
	} else {
		$(obj).html($(obj).html().replace(/Hide/,'Show'));
		$(obj).next().addClass('hide');
	}
}

function js_delete_file(obj) {
    "use strict";
    var rows_to_delete, filenames, file;
    var table_id = $(obj).closest(".table_div").find("table").attr('id');
    var t = $('#' + table_id).DataTable();
    
    //Get the selected rows, except for the 'select_all' table header row
    rows_to_delete = $('#' + table_id).find('input:checked').closest('td').closest('tr');
    
    //Create an array of filenames to delete
    filenames = $(rows_to_delete).find(".filename").map(function(){return $(this).attr("title");}).get();
    if ( filenames.length == 0 ) return;
    else if ( filenames.length == 1) file = "this file";
    else file = "these files";
    
	$("<div title='Delete?'>Are you sure you want to delete " + file + "?<p>" + filenames.join(",<br/>") + "</p></div>").dialog({
		width: 'auto',
		height: 'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Delete": function() {
				t.rows(rows_to_delete).remove().draw();
				js_run_code("delete_file","debug","table_id",table_id,"file_list",filenames.join());
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_delete_SD(obj) {
    "use strict";
        
	$("<div title='Clear SD card?'>Are you sure you want to delete ALL recordings from this SD card?</p></div>").dialog({
		width: 'auto',
		height: 'auto',
		modal: true,
		close: function () { $(this).dialog('destroy').remove(); },
		buttons: {
			"Delete": function() {
				js_run_code("delete_SD","debug");
				js_run_code('list_recordings','recordings');
                js_run_code('list_octaves','octaves');
				$(this).dialog('destroy').remove();
			},
			Cancel: function() {
				$(this).dialog('destroy').remove();
			}
		}
    });
}

function js_duplicate_settings(obj) {
    "use strict";
    var table_id = $(obj).closest(".table_div").find("table").attr('id');
    
    //Get the first selected row, except for the 'select_all' table header row
    var selected_row = $('#' + table_id).find('input:checked').closest('td').closest('tr').first();
    if (! selected_row.length ) return;
	var recorded = $(selected_row).find(".recorded").text();
	js_run_code("duplicate_settings","configuration","table_id",table_id,"recorded",recorded);
}

function js_edit(obj) {
    "use strict";
	var i;
    var table_id = $(obj).closest(".table_div").find("table").attr('id');
    var div_id = $(obj).closest(".table_div").attr('id');
    //Get the first selected row, except for the 'select_all' table header row
    var selected_row = $('#' + table_id).find('input:checked').closest('td').closest('tr').first();
    if (! selected_row.length ) return;

	var filename = $(selected_row).find(".filename").attr("title");
	//Strip the timestamp
	var filename = filename.replace(/_\d+\..*$/, "");
	var recorded = $(selected_row).find(".recorded").text();
	var description = $(selected_row).find(".description").text();
	var num_channels = parseInt($(selected_row).find(".num_channels").text());
	var edit_box_str = "<div id='edit_box'><span>Flac filename: </span> \
				<input name='filename' class='filename' type='text' title='Name of the file'  style='width:200px;' value='" +
				filename + "' /> \
			<table> \
				<tr><td>Description</td> \
				<td><textarea class='description' title='Short description of the data' rows='2' cols='50' style='resize:none;' maxlength='65536'>" + description + "</textarea></td> \
				</tr>";
	for (i = 1; i <= num_channels; i += 1) {
		edit_box_str += "<tr><td>Channel " + i + "</td> \
					<td><textarea class='channel_" + i + "' title='Short description of the data being recorded on channel' rows='2' cols='50' style='resize:none;' maxlength='65536'>" + $(selected_row).find(".channel_" + i).text() +"</textarea></td></tr>";
	}
	edit_box_str += "</table></div>";
			
   $(edit_box_str).clone().dialog(
        { 
        resizable: true,
        height: 500,
        width: 800, 
        title: "Edit the metadata of " + filename,
        open: function() {
			$(this).find(".description").focus(); $(".description").select();  
			},
        close: function () { $(this).dialog('destroy').remove(); },
        modal: true,
        draggable: true,
        buttons: {
            "OK": function() {
				//For simplicity, I am just getting rid of any quotes in the comment
				var arg_array = ["edit_tags",div_id,
                    "table_id",table_id,
					"recorded",recorded,
					'new_filename',check_str($(this).find(".filename").val()),
					'description',check_str($(this).find(".description").val()),
					];
				for (i = 1; i <= num_channels; i += 1) {
					arg_array.push( "channel_" + i, check_str($(this).find(".channel_" + i).val()));
				}
				js_run_code.apply(null, arg_array);
                $(this).dialog('destroy').remove();
				
            },
            Cancel: function() {
                $(this).dialog('destroy').remove();
            }
        }
    });
}

function js_analyze(obj) {
    "use strict";

     var table_id = $(obj).closest(".table_div").find("table").attr('id');

   //Get the selected rows, except for the 'select_all' table header row
    var selected_rows = $('#' + table_id).find('input:checked').closest('td').closest('tr');
    if (! selected_rows.length ) return;
	
	var filenames = $(selected_rows).find(".filename").map(function(){return $(this).attr("title");}).get();
    
    if (table_id == "recording_table") {
        $.each(filenames, function( index, value ) {
            //alert(value);
            window.open("/analyze.php?file=/dev/mmcblk0p2/" + value);
        });
    } else {
        $.each(filenames, function( index, value ) {
            //alert(value);
            window.open("/analyze.php?file=/mnt/externalSD/" + value);
        });        
    }
}

function check_str(str) {
	//TODO: For simplicity, I am just getting rid of any quotes in the comment
	return str.replace(/['\"]/g, "");
}

function js_run_code() {
    "use strict";
    //The first argument is the (cmd) case statement to be used in run_code
    //The second argument is id of the html element to be updated
    //Subsequent argument pairs define key,value pairs to be passed to run_code
        
    var cmd = arguments[0],
        element_id = arguments[1],
        load_str = "get/run_code.php?cmd=" + cmd + "&",
        i;
    for (i = 2; i < arguments.length; i += 2) {
        load_str += arguments[i] + "=" + encodeURIComponent(arguments[i + 1]) + "&";
    }

    jQuery.get(load_str, function (data) { $('#' + element_id).html(data); });
}



