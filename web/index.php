<?php

$specials = array( 
    'LAST_MODIFIED' => date("d F Y.",filemtime('templates/base.html')),
    'TITLE' => 'BBB Acquisition System',
    );

$contents = file_get_contents('templates/header.html');
$contents .= file_get_contents('templates/base.html');
$contents .= file_get_contents('templates/footer.html');

include('includes/process_html.php');

echo $contents;

?>
