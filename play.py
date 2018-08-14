#!/usr/bin/python3

import os
import re
import random
import requests
from bs4 import BeautifulSoup as BE
#import xml.etree.ElementTree as ET #unfortunately the page isn't valid xml and breaks the parser. so no xpath for this : (

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

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
    feed_protein = 15
    feed_sugar = 15

    def __init__(self, link, hunger_p=None, hunger_s=None):
        self._link = link
        self.id = re.search(r'(?<=id=)[0-9]*', link).group()
        self.hunger_p = hunger_p
        self.hunger_s = hunger_s

    @property
    def url(self):
        return url(self._link)

    def need_sugar(self):
        return self.hunger_s > Formi.feed_sugar

    def need_protein(self):
        return self.hunger_p > Formi.feed_protein

    def need_schutz(self):
        #TODO
        return False

    def need_care(self):
        return self.need_sugar() or self.need_protein() or self.need_schutz()

    def find_hunger(self, root):
        self.hunger_s = self._hunger_helper('sugar', root)
        self.hunger_p = self._hunger_helper('protein', root)
    
    def _hunger_helper(self, which, root):
        hunger_span_id = '{}hunger{}'.format(which, self.id)
        hunger_string = str(root.find('span', id=hunger_span_id).parent.find_all(string=True, recursive=False))
        hunger_int = integer(hunger_string)
        print('Detected hunger {}: {}'.format(which, hunger_int))
        return hunger_int

    def feed_data(self, food, amount=1):
        return {
            'cat': '9',
            'action': 'addfood',
            'foodid': food.id,
            'amount': str(int(amount)),
            'id': self.id
        }

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
        self.ameisenzimmer()

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
            if random.random() < 2/3:
                self.klo_putzen()
            else:
                self.futtertiere_sammeln()

            #random.choices([self.klo_putzen, self.futtertiere_sammeln], [2/3, 1/3])[0]() # only python 3.6
            #self.klo_putzen()
            #self.futtertiere_sammeln()

    def futtertiere_sammeln(self, duration=15):
        print('starting futtertiere sammeln')
        data = {
            'dauer': duration,
            'cat': 2,
            'taketask': 999
        }
        self._post('draussen', data=data)

    def klo_putzen(self):
        print('starting klo putzen')
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

    def _parse_foods(self, root):
        selects = root.find_all('select', attrs={'name':'foodid'})
        self.foods = list()
        for select in selects:
            options = select.find_all('option')
            for option in options:
                self.foods.append(Food(option))

    def check_formi(self, formi):
        if not formi.need_care():
            print('All good in {}. Continue.'.format(formi.id))
            return
        root = self._get(formi.url)
        self._parse_foods(root)
        if formi.need_protein():
            print('Giving protein to {}'.format(formi.id))
            most_prot = max([f for f in self.foods if f.protein], key=lambda food:food.amount)
            root = self._post('ameisenzimmer', data=formi.feed_data(most_prot))
            #self._parse_foods(root)
        if formi.need_sugar():
            print('Giving sugar to {}'.format(formi.id))
            most_prot = max([f for f in self.foods if f.sweet], key=lambda food:food.amount)
            root = self._post('ameisenzimmer', data=formi.feed_data(most_prot))
            #self._parse_foods(root)

with open(os.path.join(__location__, 'settings.txt'), 'r') as settings:
    for line in settings.readlines():
        line = line.split('=')
        if line[0] == 'feed_protein':
            Formi.feed_protein = int(line[1])
        if line[0] == 'feed_sugar':
            Formi.feed_sugar = int(line[1])
    print('Running with the following settings:')
    print(' feed_protein: {}'.format(Formi.feed_protein))
    print(' feed_sugar: {}'.format(Formi.feed_sugar))

with open(os.path.join(__location__, 'credentials.txt'), 'r') as creds:
    creds = creds.readlines()
    Play(creds[0].strip(), creds[1].strip())
