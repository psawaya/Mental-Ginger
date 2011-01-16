#!/usr/bin/env python

import logging

from gaeflickrlib import GaeFlickrLib

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

flickrAPIKey = 'b6e189ca8d6c0e505a32d67dc846c06c'
flickrAPISecret = '988479871ee728f9'


class MainHandler(webapp.RequestHandler):
    def get(self):
        
        self.response.out.write(template.render('templates/index.html',{}))

class SearchHandler(webapp.RequestHandler):
    def get(self):
        flickr = GaeFlickrLib(api_key = flickrAPIKey,
                              api_secret = flickrAPISecret)
                              
        tags = self.request.get('tags')
        
        if tags is None: return

        logging.debug("TAGS: %s " % self.request.get('tags'))

        results = flickr.photos_search(tags = tags)
        self.response.out.write(template.render('templates/images.html',{'images' : [r.url() for r in results]}))

def main():
    logging.getLogger().setLevel(logging.DEBUG)

    application = webapp.WSGIApplication([
                                        ('/', MainHandler),
                                        ('/search', SearchHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
