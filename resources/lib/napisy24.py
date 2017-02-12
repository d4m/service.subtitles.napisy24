import os
import struct
import hashlib
import xbmcvfs
import requests
import base64

class Napisy24:
    apiUrl = 'http://napisy24.pl/run/CheckSubAgent.php'
    
    def __init__(self, userAgent, userPassword):
        self.userAgent = userAgent
        self.userPassword = userPassword

        self.httpHeaders = {
            'User-Agent': userAgent,
        }

    def search(self, filePath, preferredLanguage):

        data = {
            'postAction': 'CheckSub',
            'ua': self.userAgent,
            'ap': self.userPassword,
            'fs': int(xbmcvfs.File(filePath, "rb").size()),
            'fn': os.path.basename(filePath),
            'fh': self.opensubtitlesHash(filePath),
            'md': self.napiprojektHash(filePath),
            'nl': preferredLanguage
        }

        self.log('Request url: %s, Request data: %s'%(self.apiUrl, data));

        request = requests.post(self.apiUrl, headers = self.httpHeaders, data = data)

        subtitleData = None

        if(request.status_code == 200):
            content = request.text
            data = content.split('||')

            if len(data) == 2:

                self.log('Response: %s'%(data[0]))

                subtitle = data[1]
                data = data[0].encode('utf-8').split('|')
                subtitleData = {}

                if data[0] == 'OK-2':
                    for d in data[1:]:
                        subtitleData[d.split(':', 1)[0]] = d.split(':', 1)[1]

                    subtitleData['base64'] = base64.b64encode(subtitle.encode(request.encoding))

        return subtitleData

    def napiprojektHash(self, filePath):
        z = hashlib.md5(xbmcvfs.File(filePath, "rb").read(10485760)).hexdigest()

        idx = [0xe, 0x3, 0x6, 0x8, 0x2]
        mul = [2, 2, 5, 4, 3]
        add = [0, 0xd, 0x10, 0xb, 0x5]

        b = []
        for i in xrange(len(idx)):
            a = add[i]
            m = mul[i]
            i = idx[i]

            t = a + int(z[i], 16)
            v = int(z[t:t + 2], 16)
            b.append(("%x" % (v * m))[-1])

        return ''.join(b)

    def opensubtitlesHash(self, filePath):
        longlongformat = 'q'  # long long
        bytesize = struct.calcsize(longlongformat)
        f = xbmcvfs.File(filePath)

        filesize = f.size()
        hash = filesize

        if filesize < 65536 * 2:
            return "SizeError"

        buffer = f.read(65536)
        f.seek(max(0,filesize-65536),0)
        buffer += f.read(65536)
        f.close()
        for x in range((65536/bytesize)*2):
            size = x*bytesize
            (l_value,)= struct.unpack(longlongformat, buffer[size:size+bytesize])
            hash += l_value
            hash = hash & 0xFFFFFFFFFFFFFFFF

        return "%016x" % hash
