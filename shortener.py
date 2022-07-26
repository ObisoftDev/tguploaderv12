import requests
from bs4 import BeautifulSoup
def short_url(url):
    api = 'https://shortest.link/es/'
    resp = requests.post(api,data={'url':url})
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.text,'html.parser')
        shorten = soup.find('input',{'class':'short-url'})['value']
        return shorten
    return url