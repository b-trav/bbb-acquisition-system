<?php
include('../includes/globals.php');

$cmd=str_check($_GET["cmd"]);
$specials = [];

function refresh_config($SD_dir) {
	$current_config = $SD_dir.'/.current_config_xml';
	$default_config = '../default_config.xml';
	$contents = file_get_contents('../templates/configuration.html');
	if (!file_exists($current_config)) copy($default_config,$current_config);
	$config = simplexml_load_file($current_config);
	$saved_configs = '';
	foreach (glob($SD_dir."/*.xml") as $file) {
		$saved_configs .= "<option>".basename($file)."</option>";		
	}
	$num_channels = $config->channels;
	$contents = str_replace("<option>$num_channels</option>","<option selected='selected'>$num_channels</option>",$contents);
	$attr = $config->channels->attributes();
	if (isset($attr['shift'])) $shift="checked='checked'";
	else $shift = "";
	$sample_rate = $config->{'sample-rate'};
    $fft_size = $config->fft_size;
	$contents = str_replace("<option>$sample_rate</option>","<option selected='selected'>$sample_rate</option>",$contents);
	$channels_str = "";
	for ($i = 1; $i <= $num_channels; $i++) {
		$channels_str .= "
			<tr><td>Channel $i</td>
			<td><textarea id='channel_$i' title='Short description of the data being recorded on channel $i' rows='3' cols='50' style='resize:none;' maxlength='65536'>".$config->{"channel_$i"}."</textarea></td>
				</tr>";
	}
	$specials = array(
		'FILENAME' => $config->filename,
		'RECORD_LENGTH' => $config->record_length,
		'DESCRIPTION' => $config->description,
		'CHANNELS' => $channels_str,
		'CONFIGS' => $saved_configs,
		'SHIFT' => $shift,
		'FFT_SIZE' => $fft_size,
				);
	foreach ($specials as $key => $value) $contents = str_replace("{".$key."}",$value,$contents);
	echo $contents;
}

function list_recordings($SD_dir) {
	setlocale(LC_TIME, "");
	$contents = file_get_contents('../templates/list_recordings.html');
	$file_list_str = '';
	if ( file_exists("$SD_dir/.recordings_xml") ) {
		$disk= simplexml_load_file("$SD_dir/.recordings_xml");
		$num_recordings = count($disk->recording);
		for($rr = 0; $rr < $num_recordings; $rr++) {
			$recording = $disk->recording[$rr];
			$filename = $recording->filename;
			$recorded = $recording->recorded;
            $mem_start = (float) $recording->mem_start;
            $drops_str = "mem_start :                        ".number_format($mem_start)."&#013;";
			$sample_rate = $recording->{'sample-rate'};
			$bit_rate = $recording->bps;
			$num_channels = intval($recording->channels);
            if ( isset($recording->recorded['drops']) ) {
                $drops = explode(",",$recording->recorded['drops']);
                foreach ($drops as $drop) {
                    $tmp_str = explode(":",$drop);
                    $drops_str .= sprintf("%04d : %s : %s &#013;",
                        intval($tmp_str[0]),
                        date("M d H:i:s",$tmp_str[1]),
                        number_format($mem_start+intval($tmp_str[0])*$num_channels*intval($sample_rate)*(intval($bit_rate)/8)));
                }
                $row_class = "class='drops'";
            } else {
                $row_class = "";
            }
			$date_modified = "<span class='hide recorded'>$recorded</span><br/>".strftime('%H:%M:%S %x', strtotime($recorded));
			$file_size = number_format(floatval($recording->mem_size)/(1024*1024));
			$record_length = $recording->record_length;
			$range = '['.$recording->min.",".$recording->max."]";
			$description = $recording->description;
			$channel = array();
			for ($i = 1; $i <= $num_channels; $i++) {
				$channel[] = $recording->{"channel_$i"};
			}
			$file_list_str .= "<tr $row_class>
					<td><input type='checkbox' /></td>
					<td>
						<a class='filename' href=\"${filename}_${recorded}.flac\" title='${filename}_${recorded}.flac' download>$filename</a>
						<a class='small' href=\"${filename}_${recorded}.bin\" title='${filename}_${recorded}.bin' download>(binary)</a>
						<a class='small' href=\"${filename}_${recorded}.xml\" title='${filename}_${recorded}.xml' download>(metadata)</a>
					</td>
					<td>$date_modified</td>
					<td>$file_size</td>
					<td class='length'><span class='hide'>$record_length<br/></span><span title='$drops_str' >".gmdate("H:i:s", intval($record_length))."</span></td>
					<td class='num_channels'>$num_channels</td>
					<td>$sample_rate</td>
					<td>
						<div class='description' onclick='js_toggle_next(this);'>$description</div>
						<div class='channels hide'>";
			foreach ($channel as $i=>$ch) {
				$k = $i +1;
				if (empty($ch)) 
					$file_list_str .= "
							<div class='hide'><span>Channel $k:</span><span class='channel_$k'>$ch</span></div>";
				else
					$file_list_str .= "
							<div><span>Channel $k:</span><span class='channel_$k'>$ch</span></div>";
			}
			$file_list_str .= "
						</div>
					</td>
				</tr>";
		}
	} 
	$specials = array(
		'FILE_LIST' => $file_list_str,
				);
	foreach ($specials as $key => $value) $contents = str_replace("{".$key."}",$value,$contents);
	echo $contents;
}

function list_octaves($SD_dir) {
	setlocale(LC_TIME, "");
	$contents = file_get_contents('../templates/list_octaves.html');
	$file_list_str = '';
	if ( file_exists("$SD_dir/.octaves_xml") ) {
		$disk= simplexml_load_file("$SD_dir/.octaves_xml");
		$num_recordings = count($disk->recording);
		for($rr = 0; $rr < $num_recordings; $rr++) {
			$recording = $disk->recording[$rr];
			$filename = $recording->filename;
			$recorded = $recording->recorded;
            $drops_str = "";
            if ( isset($recording->recorded['drops']) ) {
                $drops = explode(",",$recording->recorded['drops']);
                foreach ($drops as $drop) {
                    $tmp_str = explode(":",$drop);
                    $drops_str .= $tmp_str[0]." : ".date("M d H:i:s",$tmp_str[1])."&#013;";
                }
                $row_class = "class='drops'";
            } else {
                $row_class = "";
            }
			$date_modified = "<span class='hide recorded'>$recorded</span><br/>".strftime('%H:%M:%S %x', strtotime($recorded));
			$file_size =  round(filesize("$SD_dir/${filename}_${recorded}.octaves")/1024);
			$sample_rate = $recording->{'sample-rate'};
			$fft_size = $recording->fft_size;
			$bit_rate = $recording->bps;
			$record_length = $recording->record_length;
			$range = '['.$recording->min.",".$recording->max."]";
			$description = $recording->description;
			$num_channels = intval($recording->channels);
			$channel = array();
			for ($i = 1; $i <= $num_channels; $i++) {
				$channel[] = $recording->{"channel_$i"};
			}
			$file_list_str .= "<tr $row_class>
					<td><input type='checkbox' /></td>
					<td>
						<a class='filename' href=\"SDcard/${filename}_${recorded}.octaves\" title='${filename}_${recorded}.octaves' download>$filename</a>
						<a class='small' href=\"${filename}_${recorded}.xml\" title='${filename}_${recorded}.xml' download>(metadata)</a>
					</td>
					<td>$date_modified</td>
					<td>$file_size</td>
					<td class='length'><span class='hide'>$record_length<br/></span><span title='$drops_str' >".gmdate("H:i:s", intval($record_length))."</span></td>
					<td class='num_channels'>$num_channels</td>
					<td>$sample_rate</td>
					<td>$fft_size</td>
					<td>
						<div class='description' onclick='js_toggle_next(this);'>$description</div>
						<div class='channels hide'>";
			foreach ($channel as $i=>$ch) {
				$k = $i +1;
				if (empty($ch)) 
					$file_list_str .= "
							<div class='hide'><span>Channel $k:</span><span class='channel_$k'>$ch</span></div>";
				else
					$file_list_str .= "
							<div><span>Channel $k:</span><span class='channel_$k'>$ch</span></div>";
			}
			$file_list_str .= "
						</div>
					</td>
				</tr>";
		}
	} 
	$specials = array(
		'FILE_LIST' => $file_list_str,
				);
	foreach ($specials as $key => $value) $contents = str_replace("{".$key."}",$value,$contents);
	echo $contents;
}

switch ($cmd) {
	case 'shutdown':
		exec("sudo bbbas_powerdown.py");
		echo "Goodbye";
		break;

	case 'get_status':
		setlocale(LC_TIME, "");
		unset($output);
		exec("check_voltage.py 2>/dev/null",$output);
		echo strftime('<span class="label">Date:</span><span class="data">%x</span><span class="label">Time:</span><span class="data">%H:%M</span>');
		if (! empty($output) ) echo "<span class='label'>Voltage:</span><span class='data'>${output[0]}</span>";
		if ( ! file_exists("/dev/mmcblk1p1") ) {
			echo "<span class='error'>ERROR: There is no SD card inserted. Please insert a blank/valid SD card and re-boot.</span>";
		} elseif ( ! file_exists("/dev/mmcblk0p2") ) {
			echo '<span class="error">ERROR: The SD card is not correctly formatted. Click here to format SD card, and re-boot:</span><input type="submit" value="Format SD card" title="Format SD card (data may be lost!)" onclick="js_format_sd();" />';
		} else {
			unset($output);
			if ( file_exists("$SD_dir/.mem_start") )
				exec("echo $(( $((`sudo /sbin/blockdev --getsize64 /dev/mmcblk0p2` - `cat /mnt/externalSD/.mem_start` )) / 1048576 ))",$output);
			else
				exec("echo $((`sudo /sbin/blockdev --getsize64 /dev/mmcblk0p2` / 1048576 ))",$output);
			printf("<span class='label'>SD card available memory:</span><span class='data'>%s MB</span>",$output[0]);
		}
        echo "<span class='label'>Your IP:</span><span id='client_ip' class='data'>".$_SERVER['REMOTE_ADDR']."</span>";
        echo "<span class='label'>Device IP:</span><span id='device_ip' class='data'>".$_SERVER['SERVER_ADDR']."</span>";
		break;

	case 'format_sd':
		exec("sudo ../../source/format_sd_card.sh",$output);
		break;
		
	case 'start_stop':
		$PIN = 31; //Corresponds to p9.13 (UART4_TXD) gpio0[31] corresponds to gpio31
		exec("echo 1 > /sys/class/gpio/gpio$PIN/value;sleep 1;echo 0 > /sys/class/gpio/gpio$PIN/value");
		echo "Starting Recording ...";
		break;
								
	case 'refresh_config':
		refresh_config($SD_dir);
		break;

	case 'duplicate_settings':
        $table_id=str_check($_GET["table_id"]);
        if ($table_id == "recording_table") $recordings_xml = "$SD_dir/.recordings_xml"; 
        else $recordings_xml = "$SD_dir/.octaves_xml"; 
		$recorded = str_check($_GET["recorded"]);
		$disk= simplexml_load_file($recordings_xml);
		$num_recordings = count($disk->recording);
		for($rr = 0; $rr < $num_recordings; $rr++) {
			$recording = $disk->recording[$rr];
			if ($recording->recorded == $recorded) {
				$config = new SimpleXMLElement("<config></config>");
				$config->addChild('filename', $recording->filename);
				$config->addChild('record_length', $recording->record_length);
				$config->addChild('sample-rate', $recording->{'sample-rate'});
				$config->addChild('fft_size', $recording->fft_size);
				$config->addChild('channels', $recording->channels);
				$config->addChild('description', $recording->description);
				$num_channels=intval($recording->channels);
				for ($i = 1; $i <= $num_channels; $i++) {
					$config->addChild("channel_$i", $recording->{"channel_$i"});
				}
				$config->asXml($current_config);
				break;
			}
		}
		refresh_config($SD_dir);
		break;
		
		
	case 'update_config':
		//TODO: Check that the filename is valid
		//TODO: Check that record_length is an integer
		//TODO: Check that all entries are valid for xml input
		
		//Create xml from scratch
		$config = new SimpleXMLElement("<config></config>");
		$config->addChild('filename', str_check($_GET["filename"]));
		$config->addChild('record_length', str_check($_GET["record_length"]));
		$config->addChild('sample-rate', str_check($_GET["sample_rate"]));
		$config->addChild('fft_size', str_check($_GET["fft_size"]));
		$config->addChild('channels', str_check($_GET["num_channels"]));
		if ( str_check($_GET["shift"]) == 'true') $config->channels->addAttribute('shift','shift');
		$config->addChild('description', str_check($_GET["description"]));
		$num_channels=intval(str_check($_GET["num_channels"]));
		for ($i = 1; $i <= $num_channels; $i++) {
			$config->addChild("channel_$i", str_check($_GET["channel_$i"]));
		}
		$config->asXml($current_config);
        //Store the client ip address to a file
        file_put_contents("$SD_dir/.client_ip",$_SERVER['REMOTE_ADDR']);
        if (str_check($_GET["mode"]) == 'octaves_button') file_put_contents("/tmp/octaves",$_SERVER['REMOTE_ADDR']);
		break;

	case 'restore_config':
		$default_config = '../default_config.xml';
		unlink($current_config);
		copy($default_config,$current_config);
		refresh_config($SD_dir);
		break;
				
	case 'save_config':
		$xml_file=str_check($_GET["xml_file"]);
		copy($current_config,$SD_dir.'/'.$xml_file.'.xml');
		refresh_config($SD_dir);
		break;
				
	case 'load_config':
		$xml_file=str_check($_GET["xml_file"]);
		copy($SD_dir.'/'.$xml_file,$current_config);
		refresh_config($SD_dir);
		break;
				
	case 'delete_config':
		$xml_file=str_check($_GET["xml_file"]);
		unlink($SD_dir.'/'.$xml_file);
		refresh_config($SD_dir);
		break;
				
	case 'list_recordings':
		list_recordings($SD_dir);	
		break;

	case 'list_octaves':
		list_octaves($SD_dir);	
		break;

	case "delete_file":
        $table_id=str_check($_GET["table_id"]);
        if ($table_id == "recording_table") $recordings_xml = "$SD_dir/.recordings_xml"; 
        else $recordings_xml = "$SD_dir/.octaves_xml"; 
		$file_list=str_check($_GET["file_list"]);
		if ( file_exists($recordings_xml) ) {
			$disk= simplexml_load_file($recordings_xml);
			foreach (explode(",",$file_list) as $file) {
                if ($table_id == "octave_table") unlink("$SD_dir/$file");
				$file = pathinfo($file, PATHINFO_FILENAME);
				$timestamp = substr($file,strrpos($file,"_")+1);
				foreach ($disk->recording as $key=>$item) {
					if ($item->recorded == $timestamp) {
						unset($item[0]);
						break;
					}
				}
			}
			$disk->asXml($recordings_xml);
		}
		break;

	case "delete_SD":
		if ( file_exists("$SD_dir/.mem_start") ) unlink("$SD_dir/.mem_start");
		if ( file_exists("$SD_dir/.recordings_xml") ) unlink("$SD_dir/.recordings_xml");
		if ( file_exists("$SD_dir/.octaves_xml") ) unlink("$SD_dir/.octaves_xml");
        foreach(glob("$SD_dir/*.octaves") as $f) {
            unlink($f);
        }
		break;

	case "clear_cache":
		exec("rm -rf $SD_dir/cache");
		echo "";
		break;

	case "restart_jupyter":
		exec("kill $(pgrep jupyter);cd /home/debian;jupyter notebook &");
		echo "";
		break;

	case "edit_tags":
        $table_id=str_check($_GET["table_id"]);
        if ($table_id == "recording_table") $recordings_xml = "$SD_dir/.recordings_xml"; 
        else $recordings_xml = "$SD_dir/.octaves_xml"; 
		$recorded = str_check($_GET["recorded"]);
		$disk= simplexml_load_file($recordings_xml);
		$num_recordings = count($disk->recording);
		for($rr = 0; $rr < $num_recordings; $rr++) {
			$recording = $disk->recording[$rr];
			if ($recording->recorded == $recorded) {
                $old_filename = (string)$recording->filename;
				$recording->filename = str_check($_GET["new_filename"]);
				$recording->description = str_check($_GET["description"]);
				$num_channels = $recording->channels;
				for ($i = 1; $i <= $num_channels; $i++) $recording->{"channel_$i"} = str_check($_GET["channel_$i"]);
				break;
			}
		}
		$disk->asXml($recordings_xml);
        if ($table_id == "recording_table") list_recordings($SD_dir);
        else {
            rename("$SD_dir/${old_filename}_$recorded.octaves","$SD_dir/".str_check($_GET["new_filename"])."_$recorded.octaves");
            list_octaves($SD_dir);
        }
		break;

	case 'binary_file':
	case 'flac_file':
	case 'xml_file':
		set_time_limit(60*60*24);
		$filename = str_check($_GET["filename"]);
		$recorded = substr($filename,-14);
        $found = false;
		$disk= simplexml_load_file("$SD_dir/.recordings_xml");
		$num_recordings = count($disk->recording);
		for($rr = 0; $rr < $num_recordings; $rr++) {
			$recording = $disk->recording[$rr];
			if ($recording->recorded == $recorded) {
				$mem_start = $recording->mem_start;
				$mem_size = $recording->mem_size; 
				$sample_rate = $recording->{'sample-rate'};
				$recorded = $recording->recorded;
				$description = $recording->description;
				$min = $recording->min;
				$max = $recording->max;
				$num_channels = $recording->channels;
				$precision = $recording->bps;
				$channel_str = "";
				for ($i = 1; $i <= $num_channels; $i++) {
					$channel_str .= "-T channel_$i=\"".$recording->{"channel_$i"}."\" ";
				}
                $found = true;
				break;
			}
		}
        if (!$found) {
            $disk= simplexml_load_file("$SD_dir/.octaves_xml");
            $num_recordings = count($disk->recording);
            for($rr = 0; $rr < $num_recordings; $rr++) {
                $recording = $disk->recording[$rr];
                if ($recording->recorded == $recorded) {
                    $sample_rate = $recording->{'sample-rate'};
                    $fft_size = $recording->fft_size; 
                    $recorded = $recording->recorded;
                    $description = $recording->description;
                    $min = $recording->min;
                    $max = $recording->max;
                    $num_channels = $recording->channels;
                    $channel_str = "";
                    for ($i = 1; $i <= $num_channels; $i++) {
                        $channel_str .= "-T channel_$i=\"".$recording->{"channel_$i"}."\" ";
                    }
                    break;
                }
            }            
        }
		if ( $cmd == 'xml_file' ) {
			echo $recording->asXml();
			break;
		}
		// Set up the download system...
		header('Content-Description: File Transfer');
		header('Content-Type: audio');
		header('Content-Transfer-Encoding: binary');
		header('Expires: 0');
		header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
		header('Pragma: public');
		if ( $cmd == 'binary_file' ) {
			header("Content-Length: $mem_size");
			passthru("get_binary /dev/mmcblk0p2 $mem_start $mem_size $sample_rate");
		} elseif ( $cmd == 'flac_file' ) {
			$flac_cmd = "get_binary /dev/mmcblk0p2 $mem_start $mem_size $sample_rate|";
			$flac_cmd .= "flac -c -T recorded=\"$recorded\" -T min=\"$min\" -T max=\"$max\" -T description=\"$description\" $channel_str --channels=$num_channels --bps=$precision --sign=signed --endian=little --lax --sample-rate=$sample_rate --input-size=$mem_size -";
			passthru($flac_cmd);
		} 		
		break;	
}

?>
