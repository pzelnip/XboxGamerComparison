from datetime import datetime, timedelta
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

# ------------------ MODELS ------------------ 

class GamerModel(db.Model):
    '''
    The datastore model to contain info about a single gamertag. 
    '''
    gamertag = db.StringProperty(required=True, indexed=True)
    json_data = db.TextProperty()
    api_url = db.StringProperty()
    lastretrieved = db.DateTimeProperty(auto_now=True)


# ------------------ REQUEST HANDLERS --------------------

class CompareGamers(webapp.RequestHandler):
    def get(self, *args):
        template = JINJA_ENV.get_template('mainpage.html')
        if len(args) == 0:
            values = {"empty" : "No gamers specified"}

        else: 
            (gamer1, gamer2) = args[0]

            if not gamer1 or not gamer2:
                values = {"errmsg" : "Only specified one gamer"}
            elif gamer1.lower() == gamer2.lower():
                values = {"errmsg" : "Both gamertags are the same"}
            else:
                try:
                    values = process_gamers(gamer1, gamer2)
                except ValueError as e:
                    values = {"errmsg" : str(e)}

        self.response.out.write(template.render(values))


    def post(self):
        gamer1 = self.request.get('gamertag1')
        gamer2 = self.request.get('gamertag2')
        self.get((gamer1, gamer2))


# ------------------ FUNCTIONS ------------------ 

def get_gamer_info(gamer):
    '''
    Returns data for the given gamertag
    '''
    query = GamerModel.all()
    query.filter("gamertag = ", gamer.lower())
    result = query.get()

    if result:
        LOGGER.warn("Cached entry loaded")
        entrytime = result.lastretrieved
        LOGGER.warn("%s %s" % (type(entrytime), entrytime))
        if datetime.utcnow() - entrytime > timedelta(hours=12):
            (jsonstr, url) = read_from_public_api(gamer)
            result.json_data = jsonstr
            result.api_url = url
            result.lastretrieved = datetime.utcnow()
            result.put()
            
        data = json.loads(result.json_data)
    else:
        (jsonstr, url) = read_from_public_api(gamer)
        gamermodel = GamerModel(
            gamertag = gamer.lower(),
            json_data = jsonstr,
            api_url = url,
        )
        gamermodel.put()

        data = json.loads(jsonstr)
        
    if data.get("error", None):
        raise ValueError("Could not retrieve data for %s" % gamer)

    return data['Data']

def read_from_public_api(gamer):
    params = urlencode({'gamertag' : gamer, 'region' : 'en-US'})
    url = "http://www.xboxleaders.com/api/games.json?%s" % params
    req = urllib2.Request(url)
    response = urllib2.urlopen(req, timeout=60)
    jsonstr = response.read()

    return (jsonstr, url) 


def process_gamers(gamer1, gamer2):
    gamer1data = get_gamer_info(gamer1)
    gamer2data = get_gamer_info(gamer2)
    g1_games = { game['Id'] for game in gamer1data['PlayedGames']}
    g2_games = { game['Id'] for game in gamer2data['PlayedGames']}

    g1_only = g1_games - g2_games
    g2_only = g2_games - g1_games
    both = g1_games & g2_games

    result = {"gamer1" : gamer1data['Gamertag'], "gamer2" : gamer2data['Gamertag'],
            "gamer1urlencode" : gamer1data['Gamertag'].replace(" ", "%20"),
            "gamer2urlencode" : gamer2data['Gamertag'].replace(" ", "%20"),
            "gamer1score" : gamer1data['TotalEarnedGamerScore'],
            "gamer2score" : gamer2data['TotalEarnedGamerScore']}

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
        (r'/', CompareGamers),
    ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(APPLICATION)
