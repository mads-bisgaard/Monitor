import os
from bs4 import BeautifulSoup
import requests
import pandas as pd
import argparse
import shutil


def cleanUrl(url):
    """
    Cleans a url to make it more human readable
    """
    newUrl = ''
    https = 'https://'
    http = 'http://'
    if url.startswith(https):
        newUrl = url[len(https):]
    if url.startswith(http):
        newUrl = url[len(http) :]
    return newUrl[: newUrl.find('/')]

def getFolders(projectFolder):
    """
    Get expected subfolders of main project folder
    """
    f = lambda file: os.path.abspath(os.path.join(projectFolder, file))
    return f('inputFolder'), f('cacheFolder')

def getInputFolderContent(inputFolder):
    f = lambda file: os.path.abspath(os.path.join(inputFolder, file))
    content = {}
    names = ['urlFile', 'keyFile']
    for elm in names:
        content[elm] = f(elm)
    return content

def getCacheFolderContent(cacheFolder):
    """
    Returns a dict with the files which must be in the cache folder and checks that the data is present.
    """
    f = lambda file: os.path.abspath(os.path.join(cacheFolder, file))
    content = {}
    content['keywordCount'] = f('keywordCount.csv')
    content['siteCaches'] = f('siteCaches')
    return content

def inputFolderIsValid(inputFolder):
    """
    Checks if the input folder is valid.

        :arg inputFolder:       Absolute path to input folder
    """
    isValid = True
    if not os.path.isdir(inputFolder):
        isValid = False
    content = getInputFolderContent(inputFolder)
    for key in content:
        if not os.path.isfile(content[key]):
            isValid = False
    return isValid

def cacheFolderIsValid(cacheFolder):
    """
    Checks if the input folder is valid.

        :arg inputFolder:       Absolute path to input folder
    """
    isValid = True
    if not os.path.isdir(cacheFolder):
        isValid = False
    content = getCacheFolderContent(cacheFolder)
    for key in content:
        if not (os.path.isfile(content[key]) or os.path.isdir(content[key])):
            isValid = False
    return isValid

def printLogs(countLog, linkLog):
    """
    Print logs
    """
    newLine = '\n'
    tab = '\t'
    msg = ''
    if len(countLog) > 0:
        msg += newLine + newLine + 'Keyword detection results:' + newLine
        msg += '==========================' + newLine
        msg += newLine.join(countLog) + newLine
    else:
        msg += newLine + 'No new keywords detected' + newLine
    if len(linkLog) > 0:
        msg += 'Link detection results:' + newLine
        msg += '==========================' + newLine
        msg += newLine.join(linkLog) + newLine
    else:
        msg += newLine + 'No new links detected'
    msg += newLine
    print(msg)


def compareData(projectFolder):
    """
    Takes input folder as argument. Compares data in cache folder with current data

        :arg projectFolder:      Absolute path to project folder
    """
    inputFolder, cacheFolder = getFolders(projectFolder)
    if not inputFolderIsValid(inputFolder):
        raise Exception("InputFolder is invalid.")

    input = getInputFolderContent(inputFolder)
    cache = getCacheFolderContent(cacheFolder)

    with open(input['urlFile'], 'r') as f:
        urlSet = set(f.read().splitlines())
    with open(input['keyFile'], 'r') as f:
        keySet = set(f.read().splitlines())
    
    with open(cache['keywordCount'], 'r') as f:
        cacheDf = pd.read_csv(f)
    
    print('Counting keywords and comparing links...')
    countLog = [] # Log to record new keywords
    linkLog = [] # Log to record new links

    for url in urlSet:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            siteText = soup.get_text()
            links = soup.find_all('a')
            newLinks = set([link.get('href') for link in links if (link.get('href').startswith('https://') or link.get('href').startswith('http://'))])
        except:
            print('Could not fetch url ', url)                  
            continue
        
        # count keywords
        tmpDf = cacheDf[cacheDf['url'] == url]
        for word in keySet:
            df = tmpDf[tmpDf['word'] == word.lower()]
            cacheCount = int(df['count'][df.index[0]])
            siteCount = siteText.count(word)
            if siteCount > cacheCount:
                countLog.append('New occurance of the word ' + word + ' on ' + url)

        #count links
        urlName = cleanUrl(url)
        urlFilePath = os.path.join(cache['siteCaches'], urlName)
        if not os.path.isfile(urlFilePath):
            print('Could not find link storage file for ' + urlName)
            continue
        with open(urlFilePath, 'r') as f:
            storedLinks = set(f.read().splitlines())

        if any([ link.startswith('https://') or link.startswith('http://') for link in newLinks - storedLinks]):
            linkLog.append('New link appeard on ' + url)
            continue

    printLogs(countLog, linkLog)


def cacheData(projectFolder):
    """
    Cache necessary data

        :arg projectFolder:     project folder
    """
    inputFolder, cacheFolder = getFolders(projectFolder)
    if not inputFolderIsValid(inputFolder):
        raise Exception("InputFolder is invalid.")
    if os.path.isdir(cacheFolder):
        shutil.rmtree(cacheFolder)
    os.mkdir(cacheFolder)

    input = getInputFolderContent(inputFolder)
    cache = getCacheFolderContent(cacheFolder)
    os.mkdir(cache['siteCaches'])

    with open(input['urlFile'], 'r') as f:
        urlSet = set(f.read().splitlines())
    with open(input['keyFile'], 'r') as f:
        keySet = set(f.read().splitlines())

    urls = []
    words = []
    counts = []
    for url in urlSet:
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            siteText = soup.get_text()
            links = soup.find_all('a')
        except:
            print('Could not fetch url ', url)
            continue

        for word in keySet:
            urls.append(url)
            words.append(word.lower())
            counts.append(siteText.lower().count(word.lower()))
        
        linkContent = []
        for link in links:
            href = link.get('href')
            if href is not None:
                if href.startswith('https://') or href.startswith('http://'):
                    linkContent.append(href)
        
        with open(os.path.join(cache['siteCaches'], cleanUrl(url)), 'w+') as f:
            f.write('\n'.join(linkContent))

    df = pd.DataFrame({'url': urls, 'word': words, 'count': counts})
    df.to_csv(cache['keywordCount'])
    print('Succesfully cached available sites.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Monitor websites')
    parser.add_argument('projectFolder', help='Project directory')
    args = parser.parse_args()

    _, cacheFolder = getFolders(args.projectFolder)
    if cacheFolderIsValid(cacheFolder):
        compareData(args.projectFolder)
        print('Caching new data...')
        cacheData(args.projectFolder)
    else:
        cacheData(args.projectFolder)