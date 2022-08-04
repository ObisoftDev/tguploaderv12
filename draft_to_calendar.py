import aiohttp
import urllib.parse
import json
from bs4 import BeautifulSoup
import re
import socket
import socks
from aiohttp_socks import ProxyConnector
from python_socks import ProxyType
from datetime import date

class Draft2Calendar(object):
    def __init__(self):
        self.data = None
        self.status = 0
        pass
    async def send_calendar(self,moodle: str, user: str, passw: str, urls: list, proxy=None) -> list:
        if proxy:
            connector = ProxyConnector(
                proxy_type=ProxyType.SOCKS5,
                host=proxy.ip,
                port=proxy.port,
                rdns=True,
                verify_ssl=False
            )
        else:
            connector = aiohttp.TCPConnector(verify_ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Extraer el token de inicio de sesión
            try:
                # Login
                async with session.get(moodle + "/login/index.php") as response:
                    html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                token = soup.find("input", attrs={"name": "logintoken"})
                if token:
                    token = token["value"]
                else:
                    token = ""
                payload = {
                    "anchor": "",
                    "logintoken": token,
                    "username": user,
                    "password": passw,
                    "rememberusername": 1,
                }
                async with session.post(moodle + "/login/index.php", data=payload) as response:
                    html = await response.text()

                sesskey = re.findall('(?<="sesskey":")(.*?)(?=")', html)[-1]
                userid = re.findall('(?<=userid=")(.*?)(?=")', html)[-1]
                # Mover a calendario
                base_url = (
                    "{}/lib/ajax/service.php?sesskey={}&info=core_calendar_submit_create_update_form"
                )
                today = date.today()
                payload = [
                    {
                        "index": 0,
                        "methodname": "core_calendar_submit_create_update_form",
                        "args": {
                            "formdata": "id=0&userid={}&modulename=&instance=0&visible=1&eventtype=user&sesskey={}&_qf__core_calendar_local_event_forms_create=1&mform_showmore_id_general=1&name=Subidas&timestart[day]="+str(today.day)+"&timestart[month]="+str(today.month)+"&timestart[year]="+str(today.year)+"&timestart[hour]=18&timestart[minute]=55&description[text]={}&description[format]=1&description[itemid]=940353303&location=&duration=0"
                        },
                    }
                ]
                urls_payload = '<p dir="ltr"><span style="font-size: 14.25px;">{}</span></p>'
                base_url = base_url.format(moodle, sesskey)
                urlparse = lambda url: urllib.parse.quote_plus(urls_payload.format(url))
                urls_parsed = "".join(list(map(urlparse, urls)))
                payload[0]["args"]["formdata"] = payload[0]["args"]["formdata"].format(
                    userid, sesskey, urls_parsed
                )
                async with session.post(base_url, data=json.dumps(payload)) as result:
                    resp = await result.json()
                    resp = resp[0]["data"]["event"]["description"]
                self.status = 1
                data = re.findall("https?://[^\s\<\>]+[a-zA-z0-9]", resp)
                self.data = data
                return data
            except Exception as e:
                self.status = 2
                return False
