# Monitor
Python script to monitor websites

## Setting up a workspace
To monitor a bunch of sites one needs to create a workspace, a folder henceforth denoted `workspace`. All cached data is stored in `workspace`. Within `workspace` one needs to create a folder named "inputFolder" containing two plain text files:

1. A file named "urlFile" containing a list of urls to monitor: A single url on ech line. 
E.g. the content of `urlFile` might look something like
```
https://github.com
https://www.worldometers.info    
```
if these were the sites one wishes to monitor.
2. A file named "keyFile". This file should contain a list of keywords to look for on the sites: A single word on each line. The case of the words doen't matter. E.g. the content of `keyFile` might look something like
```
application
job
news
```
if these are the words one would like to look for in the sites.

## Montoring
Once a proper workspace has been setup, run 
```
python monitor.py <path to workspace>
```
to cache the needed data. When ever one would like to compare the current sites with the cached sited the same command is run. This also results in the cached data being updated.

## Dependencies
To install all dependencies: 
```
pip install requirements.txt
```