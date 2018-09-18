# OpenXDF

Processing exported Polysmith PSG files in OpenXDF format.

## Description

This repository contains scripts that assist with batch processing [Polysmith](http://www.nihonkohden.de/products/neurology/eeg/polysomnography/polysmith.html?L=1) overnight sleep studies (PSG) from the sleep clinic.

These functions process decrpyted OpenXDF files -- this library contains functions which will ensure file deidentification, grab sleep tech comments, and save XDF files as JSONs to save space. Files are then loaded again and sleep staging/scoring information is scraped for each study.

### Notes

None yet

## Required Libraries:

pandas >= 0.18  
xmltodict  