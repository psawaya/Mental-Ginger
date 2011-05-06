'''
Created on May 5, 2011

@author: tedjt
'''
from google.appengine.api import urlfetch
import urllib
import simplejson as json
import settings

class GoogleImageException(Exception):
    """Exception class for Google Image API exceptions."""
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class GoogleImageApi:

    """Connection to Google Images API"""
    def __init__(self, api_key=None):
        self.BASE_URL = 'https://ajax.googleapis.com/ajax/services/search/images?v=1.0&'
        self.api_key = api_key or getattr(settings, 'API_KEY', None)
    
    def sendRequest(self, args, request=None):
        """Send a request to the google images API.
            @param args: a dictionary of parameters to set in the url.
            see http://code.google.com/apis/imagesearch/v1/jsondevguide.html#request_format 
            for a list of parameters.
            @param request: the user request that initiated this image pull
            @return: the JSON object returned by google with this format
            {"responseData": {
             "results": [
              {unescapedUrl:...,},
              {result2}
             ]
            }
        """ 
        #setup request url
        url=self.BASE_URL
        for key, value in args.items():
            url += urllib.quote(str(key)) + '=' + urllib.quote(str(value)) + '&'
        url += (self.api_key and 'key=' +self.api_key or '')
        url= url.rstrip('&')
        #set request header referer
        header = request and {'Referer':request.build_absolute_uri()} or {}
        data = urlfetch.fetch(url, headers=header)
        # Process the JSON string.
        results = json.loads(data.content)
        return results
    
    def getPhotos(self, query, number, request=None):
        """send a request to get a list of photo urls.
        @param query: The string query to use for the photo search.
        @param number: The number of photo's to fetch.
        @return: A list of photo urls of length 'number'
        """
        start=0
        photoList = []
        urlVars = {'q':query}
        numberFetched=0
        while numberFetched<number:
            currentFetchCount = number-numberFetched>8 and 8 or number-numberFetched
            numberFetched=numberFetched+currentFetchCount
            urlVars['rsz']=currentFetchCount
            urlVars['start']=numberFetched
            jsonResponse = self.sendRequest(urlVars, request)
            photoList.extend([r['unescapedUrl'] for r in jsonResponse['responseData']['results']])
        return photoList