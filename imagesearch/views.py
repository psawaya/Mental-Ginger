import logging

from django.http import HttpResponse
from django.template import Context, loader

from gaeflickrlib import GaeFlickrLib
flickrAPIKey = 'b6e189ca8d6c0e505a32d67dc846c06c'
flickrAPISecret = '988479871ee728f9'

def searchHandler(request):
    # Construct flickr api object.
    flickr = GaeFlickrLib(api_key = flickrAPIKey,
                          api_secret = flickrAPISecret)

    # Query flickr.
    if request.GET:
        tags = request.GET['tags']
        if tags is None:
            c = Context({})
        #logging.debug("TAGS: %s " % self.request.get('tags'))
        results = flickr.photos_search(tags = tags)
        c = Context({'images' : [r.url() for r in results]})

    # Render template and return response.
    t = loader.get_template('imagesearch/images.html')
    return HttpResponse(t.render(c))
