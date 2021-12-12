import os
from urllib.parse import urljoin, urlparse, parse_qs
from urllib.request import urlopen

import bs4
import requests


def download(url, path, filename=None):
    print('downloading', url, path, filename)
    try:
        os.makedirs(path, exist_ok=True)
        if not filename:
            filename = os.path.basename(url)
        full_path = path + filename
        if os.path.exists(full_path):
            print('exists', full_path)
            return
        with open(full_path, "wb") as f:
            f.write(urlopen(url.replace(" ", "%20"), timeout=60).read())
            f.close()
    except Exception as e:
        print(e)


def to_dom(url):
    res = requests.get(url)
    return bs4.BeautifulSoup(res.text, features='html.parser')


def parse_home(url):
    dom = to_dom(url)
    sound_index = dom.find('div', attrs={'class': 'sound-index'})
    sections = sound_index.find_all('section')
    details = []
    for section in sections:
        category = section.h2.span.text
        albums = section.find_all('li', attrs={'class': 'album'})
        for album in albums:
            name = album.a.span.text
            cover = urljoin(url, album.a.div.figure.img.attrs['src'])
            link = urljoin(url, album.a.attrs['href'])
            print(category, cover, name, link)
            details.append(dict(category=category, cover=cover, name=name, link=link))
    return details


def parse_detail(detail, dom):
    link = detail['link']
    id = parse_qs(urlparse(link).query)['id'][0]
    album_container = dom.find('div', attrs={'class': 'album-container'})
    album_detail = album_container.find('div', attrs={'id': 'detail' + id})
    items = album_detail.table.find_all('tr', attrs={'class': 'player'})
    path = f"E:/files/sounds/{detail['category'].replace(':', ' ')}/{detail['name'].replace(':', ' ')}/"
    download(detail['cover'], path, 'cover.png')
    for item in items:
        download(item.attrs['data-play-url'], path)


if __name__ == '__main__':
    url = 'http://worldflipper.jp/digital_art/sound/'
    details = parse_home(url)
    link = details[0]['link']
    dom = to_dom(link)
    for detail in details:
        parse_detail(detail, dom)
