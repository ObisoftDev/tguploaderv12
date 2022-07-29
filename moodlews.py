from io import BufferedReader, FileIO
from pathlib import Path

import requests
import json
from bs4 import BeautifulSoup
import ProxyCloud
import base64
import os
from requests_toolbelt.multipart import encoder

import aiohttp
from aiohttp_socks import ProxyConnector


def get_webservice_token(host='',username='',password='',proxy:ProxyCloud=None):
    try:
        pproxy = None
        if proxy:
            proxy.proxy.as_dict_proxy()
        webserviceurl = f'{host}login/token.php?service=moodle_mobile_app&username={username}&password={password}'
        resp = requests.get(webserviceurl, proxies=pproxy)
        data = json.loads(resp.text)
        if data['token']!='':
            return data['token']
        return None
    except:
        return None

class ProgressFile(BufferedReader):
    def __init__(self, filename, read_callback=None,args=None):
        f = FileIO(file=filename, mode="r")
        self.__read_callback = read_callback
        self.__args = args
        self.__filename = filename
        super().__init__(raw=f)
        self.length = Path(filename).stat().st_size
        self.current = 0

    def read(self, size=None):
        global download_status
        calc_sz = size
        if not calc_sz:
            calc_sz = self.length - self.tell()
        if self.__read_callback:
            self.__read_callback(self.__filename, self.tell(), self.length,0,0,self.__args)
        return super(ProgressFile, self).read(size)


store = {}
def create_store(name,data):
    global store
    if name in store:return
    store[name] = data
def get_store(name):
    if name in store:
        return store[name]
    return None
def store_exist(name):return (name in store)

async def webservice_upload_file(host='',token='',filepath='',progressfunc=None,args=None,proxy:ProxyCloud=None):
    try:
        pproxy = None
        if proxy:
            proxy.as_dict_proxy()
        webserviceuploadurl = f'{host}/webservice/upload.php?token={token}&filepath=/'
        filesize = os.stat(filepath).st_size
        of = ProgressFile(filepath,progressfunc,args)
        files={filepath: of}
        jsondata = '[]'
        if pproxy:
            conn = ProxyConnector.from_url(pproxy['https'])
        async with aiohttp.ClientSession() as session:
            async with session.post(webserviceuploadurl, data={filepath: of},proxy=pproxy) as response:
                jsondata = await response.text()
        #resp = requests.post(webserviceuploadurl,data={filepath:of}, proxies=pproxy)
        of.close()
        data = json.loads(jsondata)
        if len(data)>0:
            i=0
            for item in data:
                item['host'] = host
                item['token'] = token
                data[i] = item
                i+=1
            create_store(filepath,data)
            return data
        create_store(filepath,None)
        return None
    except Exception as ex:
        create_store(filepath,None)
        print(str(ex))
        return None

def make_draft_urls(data):
    result = None
    if data:
        result = []
        for item in data:
            ctxid = item['contextid']
            itemid = item['itemid']
            filename = item['filename']
            result.append(f'{item["host"]}draftfile.php/{ctxid}/user/draft/{itemid}/{filename}')
    return result


def __progress(filename,current,total,args=None):
    print(f'Downloading {filename} {current}/{total}')

#import ProxyCloud
#host  = 'https://avucm.pri.sld.cu/'
#username = 'obysoft'
#password = 'Obysoft2001@'
#token = get_webservice_token(host,username,password)
#print(token)
#import asyncio
#filename = 'requirements.txt'
#proxy = ProxyCloud.parse('socks5://KKDHKJYEJIJJGFYGJKGIIHYJHKCJRDEHLFDGKI')
#data = asyncio.run(webservice_upload_file(host,token,filename,progressfunc=__progress,proxy=proxy))
#while not store_exist(filename):pass
#print(get_store(filename))