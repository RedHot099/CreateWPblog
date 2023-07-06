<?php
$zip = new ZipArchive;
$res = $zip->open('wp.zip');
if ($res === TRUE) {
  $zip->extractTo('./');
  $zip->close();
  echo 'wypakowało się!';
} else {
  echo 'coś poszło nie tak!';
}
?>