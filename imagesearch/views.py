import logging

from django.http import HttpResponse
from django.template import Context, loader

from gaeflickrlib import GaeFlickrLib
flickrAPIKey = 'b6e189ca8d6c0e505a32d67dc846c06c'
flickrAPISecret = '988479871ee728f9'

def searchHandler(request):
    flickr = GaeFlickrLib(api_key = flickrAPIKey,
                          api_secret = flickrAPISecret)

    #tags = self.request.get('tags')
    #if tags is None: return
    #logging.debug("TAGS: %s " % self.request.get('tags'))
    #results = flickr.photos_search(tags = tags)
    #    self.response.out.write(template.render('templates/images.html',{'images' : [r.url() for r in results]}))

    t = loader.get_template('imagesearch/images.html')
    #c = Context({'images' : [r.url() for r in results]})
    c = Context({})
    return HttpResponse(t.render(c))
