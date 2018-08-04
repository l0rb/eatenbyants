#!/usr/bin/python3

import re
import requests
from bs4 import BeautifulSoup as BE
#import xml.etree.ElementTree as ET #unfortunately the page isn't valid xml and breaks the parser. so no xpath for this : (

def url(which):
    base_url = 'http://www.eatenbyants.de'
    if base_url in which:
        return which
    php = '.php'
    ending = '' if php in which else php
    return '{}/{}{}'.format(base_url, which, ending)
        
def integer(string):
    return int(''.join(char for char in string if char.isdigit()))

class Formi:
    def __init__(self, link, hunger_p=None, hunger_s=None):
        self._link = link
        self.id = re.search(r'(?<=id=)[0-9]*', link).group()
        self.hunger_p = hunger_p
        self.hunger_s = hunger_s

    @property
    def url(self):
        return url(self._link)

    def find_hunger(self, root):
        self.hunger_s = self._hunger_helper('sugar', root)
        self.hunger_p = self._hunger_helper('protein', root)
    
    def _hunger_helper(self, which, root):
        hunger_span_id = '{}hunger{}'.format(which, self.id)
        hunger_string = str(root.find('span', id=hunger_span_id).parent.find_all(string=True, recursive=False))
        return integer(hunger_string)

    def feed(self, food, amount=1):
        data = {
            'cat': '9',
            'action': 'addfood',
            'foodid': food.id,
            'amount': str(int(amount)),
            'id': self.id
        }
        resp = requests.post(url('ameisenzimmer'))

class Food:
    def __init__(self, option):
        self.id = option['value']
        self._string = option.string
        self.amount = integer(self._string)
        self.name = re.search(r'\w+', self._string, re.UNICODE).group()

    @property
    def sweet(self):
        return self.name in ['Honig', 'Zuckerwasser']
        
    @property
    def protein(self):
        return not self.sweet

class Play:
    cookies = None

    def __init__(self, user, pw):
        self.user = user
        self.pw = pw
        self.login()
        #self.ameisenzimmer()

    def _post(self, url_string, **kwargs):
        resp = requests.post(url(url_string), cookies=self.cookies, **kwargs)
        if not self.cookies:
            self.cookies = resp.cookies
        return BE(resp.text, features='html.parser')

    def _get(self, url_string, **kwargs):
        resp = requests.get(url(url_string), cookies=self.cookies, **kwargs)
        return BE(resp.text, features='html.parser')
    
    def login(self):
        data = {
            'username': self.user,
            'password': self.pw,
            'loginbutton': 'Login',
            'loginaction': 'login'
        }
        root = self._post('login', data=data)
        aktion = root.find('div', id='headercountdown')
        if not aktion:
            self.klo_putzen()
            #self.futtertiere_sammeln()

    def futtertiere_sammeln(self, duration=15):
        data = {
            'dauer': duration,
            'cat': 2,
            'taketask': 999
        }
        self._post('draussen', data=data)

    def klo_putzen(self):
        data = {
            'cat': 3,
            'takejob': 301
        }
        self._post('internet', data=data)

    def ameisenzimmer(self):
        root = self._get('ameisenzimmer')
        self.formis = [Formi(a['href']) for a in root.find_all('a', string='Formicarium anschauen')]
        for formi in self.formis:
            formi.find_hunger(root)
            self.check_formi(formi)
            #print(formi.hunger_s)
            #print(formi.hunger_p)

    def check_formi(self, formi):
        root = self._get(formi.url)
        selects = root.find_all('select', attrs={'name':'foodid'})
        self.foods = list()
        for select in selects:
            options = select.find_all('option')
            for option in options:
                self.foods.append(Food(option))
        most_food = max([f for f in self.foods if f.protein], key=lambda food:food.amount)
        print(most_food.name, most_food.amount)
        for f in self.foods:
            print(f.name, f.amount)

Play('', '')
