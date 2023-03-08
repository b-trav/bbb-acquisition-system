<?php

$version = exec('git describe --tags');
$machine = exec('uname -a');
$machine .= "<br/>".exec('lsb_release -d | grep Description');
if (! isset($debug)) $debug = '';

// Load global variables
$specials = array_merge($specials,array(
	'YEAR' => date("Y",time()),
	'PAGE_NAME' => str_replace(".php","",pathinfo($_SERVER['SCRIPT_NAME'],PATHINFO_BASENAME)),
	'VERSION' => $version,
	'MACHINE' => $machine,
	'DEBUG' => $debug,
	'GITHUB_URL' => "http://github.com/bbb-acquisition-system",
            ));

//Replace all the special variables in the HTML document
foreach ($specials as $key => $value) {
    $contents = str_replace("{".$key."}",$value,$contents);
}

//Get rid of any special variables which haven't been replaced
$contents = preg_replace('/{[_\w]+}/','',$contents);
//Remove any html comments
$contents = preg_replace('/<!---.*?--->/s','',$contents);

?>
