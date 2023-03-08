<?php
include('includes/globals.php');

$file = str_check($_GET["file"]);
$path_parts = pathinfo($file);
$dir = $path_parts['dirname'];
$file_base = $path_parts['filename'];
$ext = $path_parts['extension'];

if ($ext == "flac") {
    if ( ! file_exists("$SD_dir/cache/$file_base.html") )
        $debug = exec("get/plot_data.py $dir/$file_base");
    $contents = file_get_contents("$SD_dir/cache/$file_base.html");
} elseif ($ext == "octaves") {
    if ( ! file_exists("$SD_dir/cache/$file_base.html") )
        $debug = exec("get/plot_octaves.py $dir/$file_base.$ext");
    $contents = file_get_contents("$SD_dir/cache/$file_base.html");
}

$specials = array(
     'JUPYTER' => $_SERVER['SERVER_NAME'],
    );

include('includes/process_html.php');

echo $contents;

?>
