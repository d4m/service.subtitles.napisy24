# -*- coding: utf-8 -*-
import os
import urllib
import urlparse
import unicodedata
import shutil
import base64
import glob
import xbmcaddon
import xbmcvfs
import xbmcplugin
import xbmcgui

__addon__ = xbmcaddon.Addon()
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path')).decode("utf-8")
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib')).decode("utf-8")
__temp__ = xbmc.translatePath(os.path.join(__profile__, 'temp', '')).decode("utf-8")

sys.path.append(__resource__)

from napisy24 import Napisy24
from apiData import userAgent, userPassword

def log(msg):
    xbmc.log((u"### [%s] - %s" % (__scriptid__, msg,)).encode('utf-8'), level=xbmc.LOGDEBUG)

def getAddonUrl(params, **kwargs):
    params.update(kwargs)
    return "%s?&%s" % (sys.argv[0], urllib.urlencode(params))

def getAddonParam(name):
    return (lambda val: None if val is None else val[0])(urlparse.parse_qs(sys.argv[2][1:]).get(name, None))

def saveTmpZipFile(content):
    if xbmcvfs.exists(__temp__):
        shutil.rmtree(__temp__)
    xbmcvfs.mkdirs(__temp__)

    zipFilename = os.path.join(__temp__, "subtitle.zip")

    with open(zipFilename, "wb") as f:
        f.write(content)
    f.close()

    log('Temporary zip file %s saved, size: %s bytes'%(os.path.basename(zipFilename), os.path.getsize(zipFilename)))

    xbmc.sleep(500)

Napisy24 = Napisy24(userAgent, userPassword)
Napisy24.log = log

Action = getAddonParam('action')

if Action == 'search':
    filePath = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))
    fileName = os.path.basename(filePath)
    preferredLanguage = xbmc.convertLanguage(getAddonParam('preferredlanguage'), xbmc.ISO_639_1)

    subtitleData = Napisy24.search(filePath, preferredLanguage)

    if subtitleData:

        listitem = xbmcgui.ListItem(
            label=xbmc.convertLanguage('pl', xbmc.ENGLISH_NAME),
            label2=fileName,
            thumbnailImage=xbmc.convertLanguage('pol', xbmc.ISO_639_1)
        )

        log('Subtitles found')

        listitem.setProperty('sync', 'true')
        saveTmpZipFile(base64.b64decode(subtitleData['base64']))
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=getAddonUrl({'action': 'download'}), listitem=listitem, isFolder=False)
    else:
        log('Subtitles not found')

if Action == 'download':
    zipFilename = os.path.join(__temp__, "subtitle.zip")

    xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (zipFilename, __temp__,)).encode('utf-8'), True)

    subtitleFiles = glob.glob(__temp__+'*.srt')
    subtitleFiles.extend(glob.glob(__temp__+'*.sub'))
    subtitleFiles.extend(glob.glob(__temp__+'*.txt'))

    if(len(subtitleFiles) != 0):
        log('Extracted files: %s'%(map(os.path.basename, subtitleFiles)))

        for fullPath in subtitleFiles:
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=fullPath, listitem=xbmcgui.ListItem(label=fullPath), isFolder=False)
    else:
        log('Extracted files: No files!')

xbmcplugin.endOfDirectory(int(sys.argv[1]))
