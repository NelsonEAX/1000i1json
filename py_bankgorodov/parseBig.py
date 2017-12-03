import urllib
import re
import json
import sys
import os
import copy
from bs4 import BeautifulSoup
import pickle



def log(log_msg):
    print(str(log_msg))

class Place():
    '''Элемент выборки'''
    def __init__(self,
                 НаселенныйПунк=None,
                 ФедеральныйОкруг=None,
                 НаселениеЧисленность=None,
                 НаселениеДата=None,
                 Координаты=None,
                 Ссылка=None,
                 ):
        self.НаселенныйПунк = НаселенныйПунк
        self.ФедеральныйОкруг = ФедеральныйОкруг
        self.НаселениеЧисленность = НаселениеЧисленность
        self.НаселениеДата = НаселениеДата
        self.Координаты = Координаты
        self.Ссылка = Ссылка

class  Population():

    def __init__(self):
        self.wd = os.getcwd()
        self.BASE_URI_bankgorodov = 'http://www.bankgorodov.ru'
        self.BASE_URI_population = 'http://www.bankgorodov.ru/cities/by-population/'
        self.BASE_URI_pages = 55
        self.BASE_URI_geocode = 'https://geocode-maps.yandex.ru/1.x/?'
        self.BASE_PATH_gorodaru = self.wd + '/gorodaru.com/Населенные пункты России — gorodaRU' #.html
        self.BASE_URI_gorodaru = 'http://www.gorodaru.com/ajax/search_cat.php'
        # '''https://geocode-maps.yandex.ru/1.x/?format=json&results=1&geocode=Челябинская область, город бреды'''
        self.url_places = []
        self.file_result = self.wd + '/Population.json'
        self.file_result_gru = self.wd + '/PopulationGRU.json'
        self.file_sql = self.wd + '/Population.sql'
        self.file_sql_gru = self.wd + '/PopulationGRU.sql'
        self.place_list_buf = {}
        if os.path.isfile(self.file_result):
            with open(self.file_result, encoding="utf8") as json_file:
                self.place_list = json.loads(json_file.read())
                log('Зачитали из файла: ' + self.file_result)
        else:
            self.place_list = {}
            log('Файл отсутствует, создали пустой список')
        if os.path.isfile(self.file_result_gru):
            with open(self.file_result_gru, encoding="utf8") as json_file:
                self.place_list_gru = json.loads(json_file.read())
                log('Зачитали из файла: ' + self.file_result_gru)
        else:
            self.place_list_gru = {}
            log('Файл отсутствует, создали пустой список')

    def __del__(self):
        log('__del__')
        self.save_result_list()

    def save_result_list(self, GRU=False):
        try:
            # with open(self.file_result, 'w') as fp:
            #     json.dump(self.place_list, fp)
            if GRU:
                self.place_list_buf.clear()
                self.place_list_buf = copy.deepcopy(self.place_list_gru)
                f2 = open(self.file_result_gru, 'w', encoding="utf8")
            else:
                self.place_list_buf.clear()
                self.place_list_buf = copy.deepcopy(self.place_list)
                f2 = open(self.file_result, 'w', encoding="utf8")

            self.place_list_buf.pop('finish', False)

            f2.write("""{\n""")


            for key in sorted(self.place_list_buf):
                item = self.place_list_buf[key]
                result = ("""
    "%s":{
        "НаселенныйПунк": "%s",
        "ФедеральныйОкруг": "%s",
        "НаселениеЧисленность": "%s",
        "НаселениеДата": "%s",
        "Координаты": "%s",
        "Ссылка": "%s"
    },"""%(
                    item['Ссылка']                  if isinstance(item, dict) else item.Ссылка,
                    item['НаселенныйПунк']          if isinstance(item, dict) else item.НаселенныйПунк,
                    item['ФедеральныйОкруг']        if isinstance(item, dict) else item.ФедеральныйОкруг,
                    item['НаселениеЧисленность']    if isinstance(item, dict) else item.НаселениеЧисленность,
                    item['НаселениеДата']           if isinstance(item, dict) else item.НаселениеДата,
                    item['Координаты']              if isinstance(item, dict) else item.Координаты,
                    item['Ссылка']                  if isinstance(item, dict) else item.Ссылка
                ))
                f2.write(result)
            f2.write("""
    "finish":{
        "НаселенныйПунк": true,
        "ФедеральныйОкруг": true,
        "НаселениеЧисленность": true,
        "НаселениеДата": true,
        "Координаты": true,
        "Ссылка": true
    }
}""")
            f2.close()
        except Exception as e:
            log('Ошибка в save_result_list. Error: ' + str(e.args))
        except:
            log('Ошибка в save_result_list')

    def get_html(self, url):
        try:
            response = urllib.request.urlopen(url)
            return response.read()
        except Exception:
            return ''

    def parse(self, html):
        try:
            soup = BeautifulSoup(html)
            places = soup.find('div', class_='cities-set')
            # print(places.find_all('a'))
            print('===========================================')

            for place in places.find_all('div', class_='row'):
                census = place.find('div', class_='val')\
                    .text \
                    .replace('\n', '') \
                    .replace(' ', '')

                result = re.match(r'([0-9,.]*)тыс.*чел.*\((\d{4}).*г.*\)', census)
                census_count = result.group(1)
                # result = re.match(r'AV', census)
                census_date = result.group(2)

                self.place_list[place.find('a')['href']] = Place(
                    НаселенныйПунк=place.find('a').text,
                    ФедеральныйОкруг=place.find('div', class_='key').text,
                    НаселениеЧисленность=census_count,
                    НаселениеДата=census_date,
                    Координаты=None,
                    Ссылка=place.find('a')['href'],
                )

                log(place.find('a').text)
                # log(НаселенныйПунк)
                # log(ФедеральныйОкруг)
                # log(НаселениеЧисленность)
                # log(НаселенныйПунк)
                # log(НаселенныйПунк)
                # log(Ссылка)
                # self.url_places.append(place['href'])

                # Ссылка = None,
                # НаселенныйПунк = None,
                # Подчинение = None


        except Exception as e:
            log('Ошибка в parse. Error: ' + str(e.args))
        except:
            log('Ошибка в parse')

    def parse_gru(self, html):
        try:
            soup = BeautifulSoup(html)
            table = soup.find('table', class_='table')

            for tr in table.find_all('tr'):
                if tr.find('th'):
                    continue
                td = tr.find_all('td')

                href = td[0].find('a')['href']
                slash = href.rfind('/')
                if slash > -1:
                    ФедеральныйОкруг = href[1:slash] \
                        .replace('/', ', ') \
                        .replace('-', ' ')
                    НаселенныйПунк = href[slash+1:]\
                        .capitalize() \
                        .replace('-', ' ')

                self.place_list_gru[href] = Place(
                    НаселенныйПунк=НаселенныйПунк,
                    ФедеральныйОкруг=ФедеральныйОкруг,
                    НаселениеЧисленность=td[2].text,
                    НаселениеДата=2017,
                    Координаты=None,
                    Ссылка=href,
                )

        except Exception as e:
            log('Ошибка в parse_gru. Error: ' + str(e.args))
        except:
            log('Ошибка в parse_gru')

    def get_all_place(self):
        try:
            for i in range(self.BASE_URI_pages):
                log(self.BASE_URI_population + str(i+1))
                self.parse( self.get_html(self.BASE_URI_population + str(i+1)) )

            log(len(self.url_places))
            log(len(self.place_list))

            self.save_result_list()
        except Exception as e:
            log('Ошибка в get_all_place. Error: ' + str(e.args))
        except:
            log('Ошибка в get_all_place')

    def get_all_place_gru(self):
        try:
            for i in range(self.BASE_URI_pages):
                log( self.BASE_PATH_gorodaru + str(i+1) + '.html' )
                f = open(self.BASE_PATH_gorodaru + str(i+1) + '.html', 'r', encoding="utf8")
                file = f.read()
                f.close()

                self.parse_gru( file )

            log(len(self.place_list_gru))
            self.save_result_list(GRU=True)
        except Exception as e:
            log('Ошибка в get_all_place_gru. Error: ' + str(e.args))
        except:
            log('Ошибка в get_all_place_gru')

    def get_geocode(self, GRU=False):
        try:
            if GRU:
                self.place_list_buf.clear()
                self.place_list_buf = copy.deepcopy(self.place_list_gru)
            else:
                self.place_list_buf.clear()
                self.place_list_buf = copy.deepcopy(self.place_list)

            for key in sorted(self.place_list_buf):
                if key == 'finish':
                    continue
                item = self.place_list_buf[key]
                geo_url = self.BASE_URI_geocode + urllib.parse.urlencode(
                    {
                        "format":"json",
                        "results": 1,
                        "geocode": item['ФедеральныйОкруг'] + ', город ' + item['НаселенныйПунк']
                    }
                )
                # geo_url = geo_url.replace(' ', '+')
                response = urllib.request.urlopen( geo_url )
                geo_json = json.loads( response.read().decode('utf8') )
                address = geo_json['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
                geo = geo_json['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']

                geo_part = geo.partition(' ')
                if len(geo_part) == 3:
                    self.place_list_buf[key]['Координаты'] = geo_part[2] + geo_part[1] + geo_part[0]
                else:
                    print('!!!!!!!!!!!!! '+geo)
                    self.place_list_buf[key]['Координаты'] = geo
                self.place_list_buf[key]['ФедеральныйОкруг'] = address
                # print(geo_json['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos'])

            if GRU:
                self.place_list_gru.clear()
                self.place_list_gru = copy.deepcopy(self.place_list_buf)
            else:
                self.place_list.clear()
                self.place_list = copy.deepcopy(self.place_list_buf)
            self.save_result_list(GRU=True)
        except Exception as e:
            log('Ошибка в get_geocode. Error: ' + str(e.args))
        except:
            log('Ошибка в get_geocode')

    def get_sql(self, GRU=False):
        try:
            if GRU:
                self.place_list_buf.clear()
                self.place_list_buf = copy.deepcopy(self.place_list_gru)
                f2 = open(self.file_sql_gru, 'w', encoding="utf8")
            else:
                self.place_list_buf.clear()
                self.place_list_buf = copy.deepcopy(self.place_list)
                f2 = open(self.file_sql, 'w', encoding="utf8")

            for key in sorted(self.place_list_buf):
                if key == 'finish':
                    continue

                item = self.place_list_buf[key]




                result = ("""
INSERT INTO `dbLocality`.`place` (`id`, `locality`, `district`, `population`, `date`, `geo`, `link`)
VALUES (NULL, '%s', '%s', %s, '%s', '%s ', '%s');""" % (
                    item['НаселенныйПунк'] if isinstance(item, dict) else item.НаселенныйПунк,
                    item['ФедеральныйОкруг'] if isinstance(item, dict) else item.ФедеральныйОкруг,
                    (item['НаселениеЧисленность'] if isinstance(item, dict) else item.НаселениеЧисленность).replace(',','.'),
                    item['НаселениеДата'] if isinstance(item, dict) else item.НаселениеДата,
                    item['Координаты'] if isinstance(item, dict) else item.Координаты,
                    item['Ссылка'] if isinstance(item, dict) else item.Ссылка
                ))
                f2.write(result)
            f2.close()
        except Exception as e:
            log('Ошибка в get_geocode. Error: ' + str(e.args))
        except:
            log('Ошибка в get_geocode')

population = Population()
# Получение всего списка населенных пунктов
# population.get_all_place()
# population.get_all_place_gru()

# Получение координат
# population.get_geocode(GRU=True)
# Получение sql-запроса
population.get_sql(GRU=True)