from urllib import unquote
from urlparse import urlparse
import logging
import os

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
        pass

    def post(self):
        pass



# ------------------ FUNCTIONS ------------------ 



# Register the URL with the responsible classes
APPLICATION = webapp.WSGIApplication([
        (r'\A/', CompareGamers),
    ], debug=True)

if __name__ == "__main__":
    run_wsgi_app(APPLICATION)
