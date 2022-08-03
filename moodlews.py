from io import BufferedReader, FileIO
from pathlib import Path

import requests
import json
from bs4 import BeautifulSoup
from python_socks import ProxyType

import ProxyCloud
import base64
import os
from requests_toolbelt.multipart import encoder

import aiohttp
from aiohttp_socks import ProxyConnector
import time

def get_webservice_token(host='',username='',password='',proxy:ProxyCloud=None):
    try:
        pproxy = None
        if proxy:
            pproxy=proxy.as_dict_proxy()
        webserviceurl = f'{host}login/token.php?service=moodle_mobile_app&username={username}&password={password}'
        resp = requests.get(webserviceurl, proxies=pproxy,timeout=8)
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
        self.time_start = time.time()
        self.time_total = 0
        self.size_per_second = 0
        self.clock_start = time.time()
        self.chunk_por = 0

    def read(self, size=None):
        global download_status
        calc_sz = size
        self.chunk_por += size
        if not calc_sz:
            calc_sz = self.length - self.tell()
        if self.__read_callback:
            self.size_per_second += size
            tcurrent = time.time() - self.time_start
            self.time_total += tcurrent
            self.time_start = time.time()
            if self.time_total >= 1:
                clock_time = (self.length - self.chunk_por) / (self.size_per_second)
                self.__read_callback(self.__filename, self.tell(), self.length,self.size_per_second,clock_time,self.__args)
                self.time_total = 0
                self.size_per_second = 0
        return super(ProgressFile, self).read(size)


store = {}
def create_store(name,data):
    global store
    store[name] = data
def get_store(name):
    if name in store:
        return store[name]
    return None
def store_exist(name):return (name in store)
def clear_store():store.clear()

async def webservice_upload_file(host='',token='',filepath='',progressfunc=None,args=None,proxy:ProxyCloud=None):
    try:
        webserviceuploadurl = f'{host}/webservice/upload.php?token={token}&filepath=/'
        filesize = os.stat(filepath).st_size
        of = ProgressFile(filepath,progressfunc,args)
        files={filepath: of}
        jsondata = '[]'
        if proxy:
            connector = ProxyConnector(
                 proxy_type=ProxyType.SOCKS5,
                 host=proxy.ip,
                 port=proxy.port,
                 rdns=True,
                 verify_ssl=False
            )
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(webserviceuploadurl, data={filepath: of},timeout=8) as response:
                    jsondata = await response.text()
        else:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
                async with session.post(webserviceuploadurl, data={filepath: of},timeout=8) as response:
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
            create_store(filepath,[data,None])
            return data
        create_store(filepath,[None,data])
        return None
    except Exception as ex:
        create_store(filepath,[None,ex])
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


def __progress(filename,current,total,spped,time,args=None):
    print(f'Downloading {filename} {current}/{total}')

#import ProxyCloud
#host  = 'http://moodle.ismm.edu.cu/'
#username = 'lpbatista'
#password = 'HUasc7EN*'
#proxy = ProxyCloud.parse('socks5://KDGKJKYIJDLGFGYKKHKFCHYDHHCGRFDGLFDHLJ')
#token = get_webservice_token(host,username,password,proxy=proxy)
#print(token)
#import asyncio
#filename = 'requirements.txt'
#data = asyncio.run(webservice_upload_file(host,token,filename,progressfunc=__progress,proxy=proxy))
#while not store_exist(filename):pass
#print(get_store(filename))