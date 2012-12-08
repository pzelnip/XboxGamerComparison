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
        gamer = args[0].encode('ascii', 'ignore') if len(args) > 0 else "pedle zelnip"
        template = JINJA_ENV.get_template('generateurl.html')
        values = get_gamer_info(gamer)
        self.response.out.write(template.render(values))

    def post(self):
        gamer = self.request.get('gamertag')
        if gamer:
            self.get(gamer)
        else:
            self.error(500)


# ------------------ FUNCTIONS ------------------ 

def get_gamer_info(gamer):
    '''
    Returns data for the given gamertag
    '''
    if "pedle" in gamer:
        data = pickle.load(open('pzelnip.pkl', 'r'))
    elif "beard" in gamer:
        data = pickle.load(open('beard.pkl', 'r'))
    else:
        params = urlencode({'gamertag' : gamer, 'region' : 'en-US'})
        url = "http://www.xboxleaders.com/api/games.json?%s" % params
        req = urllib2.Request(url)
        response = urllib2.urlopen(req, timeout=60)
        data = response.read()

    data = json.loads(data)
    return data['Data']



# Register the URL with the responsible classes
APPLICATION = webapp.WSGIApplication([
        (r'\A/', CompareGamers),
    ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(APPLICATION)
