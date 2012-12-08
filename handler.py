from urllib import unquote, urlencode
from urlparse import urlparse
import urllib2
import logging
import json
import os
import pickle

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import jinja2

LOGGER = logging.getLogger(__name__)

JINJA_ENV = jinja2.Environment(loader = jinja2.FileSystemLoader(os.path.dirname(__file__)))



# ------------------ REQUEST HANDLERS --------------------

class CompareGamers(webapp.RequestHandler):
    def get(self, *args):
        (gamer1, gamer2) = args[0] if len(args) > 0 else ("pedle zelnip", 'ii the beard ii')
        template = JINJA_ENV.get_template('generateurl.html')
        values = process_gamers(gamer1, gamer2)
        self.response.out.write(template.render(values))


    def post(self):
        gamer1 = self.request.get('gamertag1')
        gamer2 = self.request.get('gamertag2')
        if gamer1 and gamer2:
            self.get((gamer1, gamer2))
        else:
            self.error(500)


# ------------------ FUNCTIONS ------------------ 

def get_gamer_info(gamer):
    '''
    Returns data for the given gamertag
    '''
    if "pedle" in gamer:
        data = pickle.load(open('pzelnip2.pkl', 'r'))
    elif "beard" in gamer:
        data = pickle.load(open('beard2.pkl', 'r'))
    else:
        data = read_from_public_api(gamer)

    return data

def read_from_public_api(gamer):
    params = urlencode({'gamertag' : gamer, 'region' : 'en-US'})
    url = "http://www.xboxleaders.com/api/games.json?%s" % params
    req = urllib2.Request(url)
    response = urllib2.urlopen(req, timeout=60)
    data = response.read()
    data = json.loads(data)
    return data['Data']


def process_gamers(gamer1, gamer2):
    gamer1data = get_gamer_info(gamer1)
    gamer2data = get_gamer_info(gamer2)
    g1_games = { game['Id'] for game in gamer1data['PlayedGames']}
    g2_games = { game['Id'] for game in gamer2data['PlayedGames']}

    g1_only = g1_games - g2_games
    g2_only = g2_games - g1_games
    both = g1_games & g2_games

    result = {"gamer1" : gamer1data['Gamertag'], "gamer2" : gamer2data['Gamertag']}

    result['gamer1notgamer2'] = [game for game in gamer1data['PlayedGames'] 
            if game['Id'] in g1_only]
    result['gamer1notgamer2count'] = len(result['gamer1notgamer2'])
    result['gamer2notgamer1'] = [game for game in gamer2data['PlayedGames'] 
            if game['Id'] in g2_only]
    result['gamer2notgamer1count'] = len(result['gamer2notgamer1'])

    result['gamesboth'] = [game for game in gamer1data['PlayedGames']
            if game['Id'] in both]
    result['bothcount'] = len(result['gamesboth'])
    return result

# Register the URL with the responsible classes
APPLICATION = webapp.WSGIApplication([
        (r'\A/', CompareGamers),
    ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(APPLICATION)
