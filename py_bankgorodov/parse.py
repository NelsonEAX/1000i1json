#!/usr/bin/python
# -*- coding: utf-8

import urllib.request
import re
from bs4 import BeautifulSoup

from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float
#DB settings
DATABASE = {'drivername': 'mysql',
            'host': '127.0.0.1',
            'port': '3306',
            'username': 'root',
            'password': 'root',
            'database': 'bankgorodov',
            'query': {'charset': 'utf8'}
            }

Base = declarative_base()
# определяем формат таблицы в БД.
class Place(Base):
    __tablename__ = "place1"

    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    type = Column(String(256))
    subtype = Column(String(256))
    title = Column(String(256))
    parent = Column(Integer)
    population = Column(Float)
    href = Column(String(256))
    post = Column(String(256))
    geo = Column(String(256))

    def __init__(self, id, type, subtype, title, parent, population, href, post, geo):
        self.id = id
        self.type = type
        self.subtype = subtype
        self.title = title
        self.parent = parent
        self.population = population
        self.href = href
        self.post = post
        self.geo = geo

    def __repr__(self):
        return "Place '%s'" % (self.url)

class Parser:

    BASE_URI_bankgorodov = 'http://www.bankgorodov.ru'
    point_id = 1
    parent_id = 0
    points_type = 'Страны'
    points = [{
        'id': point_id,
        'type': points_type,
        'subtype': '',
        'parent': parent_id,
        'population': 0,
        'href': '/',
        'title': 'Российская Федерация',
        'post': '',
        'geo': ''
    }]
    #self.db_engine
    #self.session

    def __init__(self):
        # создаем подключение
        self.db_engine = create_engine(URL(**DATABASE), encoding='utf8')
        # создадём таблицы
        Base.metadata.create_all(self.db_engine)
        # начинаем новую сессию работы с БД
        Session = sessionmaker(bind=self.db_engine)
        self.session = Session()
        # Вставляем нулевую запись
        new_place = Place(self.points[0]['id'], self.points[0]['type'], self.points[0]['subtype'],
                          self.points[0]['title'], self.points[0]['parent'], float(self.points[0]['population']),
                          self.points[0]['href'], self.points[0]['post'], self.points[0]['geo'])
        self.session.add(new_place)
        self.session.commit()

    #def __del__(self):
        #self.connect.close()
        # совершаем транзакцию
        #self.session.commit()

    def get_float(self, str):
        '''get float from string like 356.773(2015г.)'''
        result = ''
        for x in str:
            if x.isdigit() or x == ".":
                result += x
            else:
                break
        try:
            return float(result)
        except Exception:
            return 0

    def get_html(self, url):
        try:
            response = urllib.request.urlopen(url)
            return response.read()
        except Exception:
            return ''

    def get_page_count(self, html):
        soup = BeautifulSoup(html)
        paggination = soup.find('div', class_='pages_list text_box')
        return int(paggination.find_all('a')[-2].text)

    def add_place(self, element):
        #Добавляем в список
        self.point_id += 1
        element['id'] = self.point_id
        element['population'] = "0" if element['population'] in ['неизвестно', 'жителей нет'] else element['population'].replace(",", ".").replace(" ", "")
        self.points.append(element)
        '''print('-----------------------------------------------')
        print(element['id'])
        print(type(element['id']))
        print(element['title'])
        print(type(element['title']))
        print(element['type'])
        print(type(element['type']))
        print(element['population'])
        print(type(element['population']))
        print(element['parent'])
        print(type(element['parent']))
        print(element['href'])
        print(type(element['href']))
        print(element['post'])
        print(type(element['post']))
        print(element['geo'])
        print(type(element['geo']))'''
        #Добавляем в базу
        new_place = Place(element['id'], element['type'], element['subtype'],
                          element['title'], element['parent'], self.get_float(element['population']),
                          element['href'], element['post'], element['geo'])
        self.session.add(new_place)
        self.session.commit()

    def place_parse(self, html, parent_id, uri):
        print('########################################################')
        print(uri)
        soup = BeautifulSoup(html)
        info = soup.find('div', class_='info editable-box')
        #
        title = info.find('h1', class_='country-name').text.strip()
        population = 0
        post = ''
        geo = ''
        type = ''
        subtype = ''

        ul = info.find('ul', class_='key-val-set')
        for li in ul.find_all('li', class_='row'):
            key = str(li.div.text.strip())
            if key in ['Субъект Федерации']:
                type = li.find('span').find('a').text.strip()
                print(type)

            elif key in ['Муниципальное образование']:
                subtype = li.find('span').find('a').text.strip()
                print(subtype)

            elif key in ['Население (тыс.чел.)']:
                population = li.find('span').text
                population = re.sub('\(\d{4}\)', '', population).strip()
                print(population)

            elif key in ['Почтовые индексы']:
                post = li.find('span').text.strip()
                print(post)

            elif key in ['Координаты']:
                geo = li.find('span').text.strip()
                print(geo)

        # Добавляем елемент в список и в базу
        self.add_place({
            'id': 0,
            'type': type,
            'subtype': subtype,
            'parent': parent_id,
            'population': population,
            'href': str(uri),
            'title': title,
            'post': post,
            'geo': geo
        })

    #Разбор каждой страницы, по имеющимся классам блоков, запуск подфункций разбора
    def inner_parse(self, html, parent_id, uri):
        print('inner_parse: ', uri)
        soup = BeautifulSoup(html)

        if(uri.find("/place/") >= 0):
            #print('IS IT PLACE' + str(parent_id))
            self.place_parse(self.get_html(self.BASE_URI_bankgorodov + uri), parent_id, uri)


        map_area = soup.find('div', class_='map-area')
        if(map_area is not None):
            print('IS IT map-area' + str(parent_id))

            #key-val-set
            for a_link in map_area.find_all('a', class_='link'):
                #print(a_link)
                self.inner_parse(self.get_html(self.BASE_URI_bankgorodov + a_link['href']), parent_id, a_link['href'])

            #city_counties city_areas
            for a_link in map_area.find_all('a', class_=''):
                #print(a_link)
                self.inner_parse(self.get_html(self.BASE_URI_bankgorodov + a_link['href']), parent_id, a_link['href'])

        people = soup.find('div', class_='people')
        if (people is not None):
            #print('IS IT people')

            for a_link in people.find_all('a', class_='link'):
                print(a_link)
                self.inner_parse(self.get_html(self.BASE_URI_bankgorodov + a_link['href']), parent_id, a_link['href'])

        places = soup.find('div', class_='places')
        if (places is not None):
            #print('IS IT places')

            for a_link in places.find_all('a', class_=''):
                print(a_link)
                self.inner_parse(self.get_html(self.BASE_URI_bankgorodov + a_link['href']), parent_id, a_link['href'])

    #Точка входа разбор первой страницы, получение всех регионов и их последовательный разбор
    def parse(self, html):
        soup = BeautifulSoup(html)
        regions = soup.find('ul', class_='cities-set')

        self.parent_id = self.point_id

        iter = 0

        for li_city in regions.find_all('li'):
            type = li_city['class'][0]
            ###print(li_city)

            if(type == 'type'):
                points_type = li_city.text.strip()
            else:
                #if (iter < 77):
                #    iter += 1
                #    continue
                #elif (iter > 77):
                #    break
                iter += 1

                a_city = li_city.find('a')
                #Добавляем елемент в список и в базу
                self.add_place({
                    'id': 0,
                    'type': points_type,
                    'subtype': '',
                    'parent': self.parent_id,
                    'population': a_city['data-population'],
                    'href': a_city['href'],
                    'title': a_city.text.strip(),
                    'post': '',
                    'geo': ''
                })
                self.inner_parse(self.get_html(self.BASE_URI_bankgorodov + a_city['href']), self.point_id, a_city['href'])

        for point in self.points:
            print(point)

    def get_all_data(self):
        self.parse(self.get_html(self.BASE_URI_bankgorodov + '/cities/by-region'))

parser = Parser()
#parser.get_all_data()
place = '/area/Rameshkovskii-raion'
parser.inner_parse(parser.get_html(parser.BASE_URI_bankgorodov + place), 1, place)