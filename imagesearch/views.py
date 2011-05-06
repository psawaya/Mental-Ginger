import logging

from django.http import HttpResponse
from django.template import Context, loader

from imagesearch.util.gaeflickrlib import GaeFlickrLib
from imagesearch.util.google_image_api import GoogleImageApi

from google.appengine.api import urlfetch
import simplejson as json

flickrAPIKey = 'b6e189ca8d6c0e505a32d67dc846c06c'
flickrAPISecret = '988479871ee728f9'

def searchHandler(request):
    useflickr=False
    # Construct flickr api object.
    flickr = GaeFlickrLib(api_key = flickrAPIKey,
                          api_secret = flickrAPISecret)

    # Query flickr.
    if useflickr and request.GET:
        tags = request.GET['tags']
        if tags is None:
            c = Context({})
        #logging.debug("TAGS: %s " % self.request.get('tags'))
        results = flickr.photos_search(tags = tags)
        c = Context({'images' : [r.url() for r in results]})
    
    #construct google API object
    google = GoogleImageApi()   
    # Query Google.
    if not useflickr and request.GET:
        tags = request.GET['tags']
        if tags is None:
            c = Context({})
        #logging.debug("TAGS: %s " % self.request.get('tags'))
        c = Context({'images' : google.getPhotos(tags, 15, request)})

    # Render template and return response.
    t = loader.get_template('imagesearch/images.html')
    return HttpResponse(t.render(c))
