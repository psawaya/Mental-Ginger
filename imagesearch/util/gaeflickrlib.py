"""Flickr API for Google App Engine"""
__version__ = "0.4"
        
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import memcache

import logging
import urllib
import pickle

try:
    import gaeflconfig
    API_KEY = gaeflconfig.API_KEY
    API_SECRET = gaeflconfig.API_SECRET
    GAE_PERMS = gaeflconfig.GAE_PERMS
except ImportError:
    logging.warn("no gaeflconfig found")
    

def get_text(nodelist):
    """Helper function to pull text out of XML nodes."""
    retval = ''.join([node.data for node in nodelist if node.nodeType == node.TEXT_NODE]) 
    return retval


def _perm_ok(perms, req_perms):
    """check if granted perms are >= requested perms"""
    if perms in ['delete', req_perms]:
        return True
    elif perms == 'write' and req_perms == 'read':
        return True
    else:
        return False
    

class GFLToken:
    """A Flickr auth token"""

    def __init__(self, rsp):
        self.data = {}
        self.data['token'] = str(get_text(rsp.getElementsByTagName('token')[0]
                                     .childNodes))
        self.data['perms'] = str(get_text(rsp.getElementsByTagName('perms')[0]
                                     .childNodes))
        user = rsp.getElementsByTagName('user')[0]
        self.data['nsid'] = user.getAttribute('nsid')
        self.data['username'] = user.getAttribute('username')
        self.data['fullname'] = user.getAttribute('fullname')

    def __dict__(self):
        return self.data

    def __str__(self):
        return self.data['token']    

    def __getitem__(self, key):
        return self.data[key]


class GaeFlickrLibException(Exception):
    """Exception class for Flickr exceptions."""
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message
    


class GFLPhoto:
    """Information about a single Flickr photo."""

    def __init__(self, photo):
        self.data = {}
        #logging.debug("GFLPhoto __init__: " + photo.toxml())
        for key, value  in photo.attributes.items():
            self.data[key] = value

    def url(self, size = None):
        """Return URL for a photo; defaults to medium size"""
        purl = 'http://farm'
        purl += self.data['farm'] + '.static.flickr.com/'
        purl += self.data['server'] + '/'
        purl += self.data['id'] + '_'
        purl += self.data['secret'] 
        if size is not None:
            purl += '_' + size
        purl += '.jpg'
        return purl

    def url_s(self):
        """Convenience method to return URL for small size photo"""
        return self.url(size = 's')

    def __getitem__(self, key):
        return self.data[key]
    

class GFLPhotoList:
    """A list of Flickr photos, as returned by many API methods"""
    def __init__(self, rsp):
        self.photos = []
        self.metadata = {}
        for attrib, val in \
                rsp.getElementsByTagName('photos')[0].attributes.items():
            self[attrib] = val 
        for photoxml in rsp.getElementsByTagName('photo'):
            photo = GFLPhoto(photoxml)
            self.photos.append(photo)
        logging.debug("GFLPhotoList __init__ length: " + str(len(self.photos)))

    def __iter__(self):
        return self.photos.__iter__()

    def __getitem__(self, key):
        return self.metadata[key]

    def __setitem__(self, key, data):
        self.metadata[key] = data


class GaeFlickrLib:
    """Connection to Flickr API"""
    def __init__(self, api_key=None, **p):
        if api_key or API_KEY:
            self.api_key = api_key or API_KEY
        else:
            raise GaeFlickrLibException, "api_key not provided"

        if 'api_secret' in p:
            self.api_secret = p['api_secret']
        elif API_SECRET is not None:
            self.api_secret = API_SECRET
        else:
            self.api_secret = None
        if 'token' in p:
            self.token = p['token']
        else:
            self.token = None
        
    def execute(self, method, auth=None, args=None):
        """Run a Flickr method, returns rsp element from REST response.
        defaults to using authenticated call if an api_secret was given
        when GaeFlickrLib was initialized; set auth=False to do unauth'ed call.
        Manually setting auth to true without api_secret set will raise a
        GaeFlickrLibException.
        args is a dict of arguments to the method.  See Flickr's documentation.
        """
        import xml.dom.minidom
        args = args or {}
        if auth is None:
            if self.api_secret is None:
                auth = False
            else:
                auth = True
        if not 'auth_token' in args and auth and self.token is not None:
            args['auth_token'] = self.token


        args['api_key'] = self.api_key
        args['method'] = method
        
        if auth:
            if self.api_secret is None:
                raise GaeFlickrLibException, "can't use auth without secret"
            else:
                args['api_sig'] = self.sign(args)

        url = 'http://api.flickr.com/services/rest/?'
        for key, value in args.items():
            #logging.debug("args-items %s %s\n" % (key, value))
            url += urllib.quote(str(key)) + '=' + urllib.quote(str(value)) + '&'
        url = url.rstrip('&')
        logging.debug(url)
        resp = urlfetch.fetch(url)
        #logging.debug(resp.content.decode("UTF-8"))
        dom = xml.dom.minidom.parseString(resp.content)
        rsp = dom.getElementsByTagName('rsp')[0]
        if rsp.getAttribute('stat') == 'ok':
            return rsp
        else:
            err = rsp.getElementsByTagName('err')[0]
            ecode = err.getAttribute('code')
            emsg = err.getAttribute('msg')
            raise GaeFlickrLibException, "API error: %s - %s" % (ecode, emsg)


    def execute_json(self, method, auth=None, args=None):
        """Execute a Flickr method, using json response format"""

        from django.utils import simplejson
        import re
        args = args or {}
        if auth is None:
            if self.api_secret is None:
                auth = False
            else:
                auth = True
        args['api_key'] = self.api_key
        args['method'] = method
        args['format'] = 'json'
        if auth:
            if self.api_secret is None:
                raise GaeFlickrLibException, "can't use auth without secret"
            else:
                args['api_sig'] = self.sign(args)

        url = 'http://api.flickr.com/services/rest/?'
        for key, value in args.items():
            logging.debug("args-items %s %s\n", key, value)
            url += urllib.quote(str(key)) + '=' + urllib.quote(str(value)) + '&'
        url = url.rstrip('&')
        logging.debug(url)
        resp = urlfetch.fetch(url)
        rejs = resp.content
        logging.debug(rejs)
        rejs2 = re.sub(r'^jsonFlickrApi\(', '', rejs)
        rejs = re.sub(r'\)$', '', rejs2)
        respdata = simplejson.loads(rejs)
        if respdata['stat'] == 'ok':
            return respdata['stat']
        else:
            ecode = respdata['err']['code']
            emsg = respdata['err']['emsg']
            raise GaeFlickrLibException, "API error: %s - %s" % (ecode, emsg)

    def sign (self, args):
        """returns an API sig for the arguments in args.  
        Note: if calling this manually, you must include your API key and 
        method in the args to get a valid signature.  This method is called
        automatically when needed by execute and other methodss.
        """
        import hashlib
        authstring = self.api_secret
        keylist = args.keys()
        keylist.sort()
        for key in keylist:
            authstring += str(key) + str(args[key])
        hasher = hashlib.md5()
        hasher.update(authstring)
        return str(hasher.hexdigest())

    def login_url(self, perms = 'write'):
        """returns a login URL for your application. set perms to
        'read' (default), 'write', or 'delete'.
        After logging in, user will be redirected by Flickr to the URL you set
        in your API key setup.
        """
        url = 'http://flickr.com/services/auth/?'
        pieces = {}
        pieces['api_key'] = self.api_key
        pieces['perms'] = perms
        pieces['api_sig'] = self.sign(pieces)
        for key, val in pieces.items():
            url += key + '=' + val + '&'
        url = url.rstrip('&')
        return url


# activity
    def activity_userComments(self):
        """Not yet implemented"""
        raise NotImplementedError

    def activity_userPhotos(self):
        """Not yet implemented"""
        raise NotImplementedError

# auth
    def auth_checkToken(self, auth_token = None):
        """Check the validity of a token.

        Accepts the token as a string or a GFLToken object (or any object
        which, like a GFLToken, defines __str__ to return a token as a string...)

        Returns False if token was invalid, or a GFLToken object if it was valid.
        
        """
        if auth_token is None:
            raise GaeFlickrException, "auth_checkToken \
            requires auth_token argument"
        else:
            try:
                rsp = self.execute('flickr.auth.checkToken',
                                   args = {'auth_token': str(auth_token)})
                return GFLToken(rsp)
            except GaeFlickrLibException, message:
                if str(message).find('98') != -1:
                    return False
                else:
                    raise

    def auth_getFrob(self):
        """Get a frob to use for desktop authentication.

        This method is probably not useful for a webapp, but included
        for completeness (or for interactive use of the remote_api shell)

        """
        rsp = self.execute('flickr.auth.getFrob')
        return str(get_text(rsp.getElementsByTagName('frob')[0].childNodes))

    def auth_getFullToken(self, mini_token = None):
        """convert a mini-token to a full auth token,

        returns a GFLToken object.
        """
        if mini_token is not None:
            rsp = self.execute('flickr.auth.getFullToken',
                               args = {'mini_token':mini_token})
            token = GFLToken(rsp)
            return token
        else:
            raise GaeFlickrLibException, "auth_getFullToken \
            requires a frob."
        

    def auth_getToken(self, frob = None):
        """implements flickr.auth.getToken API method.  
        requires a frob (sent in callback from login URL)
        """
        if frob is not None:
            rsp = self.execute('flickr.auth.getToken', args = {'frob':frob})
            token = GFLToken(rsp)
            return token
        else:
            raise GaeFlickrLibException, "auth_getToken requires a frob."

    def auth_getToken_full(self, frob = None):
        """for backwards compatibility; deprecated"""
        logging.warning("""auth_getToken_full is deprecated;
        use auth_getToken instead""")
        return self.auth_getToken(frob)

# blogs
    def blogs_getList(self):
        """Not yet implemented"""
        raise NotImplementedError

    def blogs_getServices(self):
        """Not yet implemented"""
        raise NotImplementedError

    def blogs_postPhoto(self):
        """Not yet implemented"""
        raise NotImplementedError

# collections


    def collections_getInfo(self):
        """Not yet implemented"""
        raise NotImplementedError

    def collections_getTree(self):
        """Not yet implemented"""
        raise NotImplementedError

# commons

    def commons_getInstitutions(self):
        """Not yet implemented"""
        raise NotImplementedError

# contacts
    def contacts_getList(self):
        """Not yet implemented"""
        raise NotImplementedError

    def contacts_getListRecentlyUploaded(self):
        """Not yet implemented"""
        raise NotImplementedError

    def contacts_getPublicList(self):
        """Not yet implemented"""
        raise NotImplementedError

# favorites
    def favorites_add(self):
        """Not yet implemented"""
        raise NotImplementedError

    def favorites_getList(self, **args):
        """user_id (Optional)
    The NSID of the user to fetch the favorites list for. If this argument is omitted, the favorites list for the calling user is returned.
min_fave_date (Optional)
    Minimum date that a photo was favorited on. The date should be in the form of a unix timestamp.
max_fave_date (Optional)
    Maximum date that a photo was favorited on. The date should be in
    the form of a unix timestamp.  
extras (Optional)
    A comma-delimited list of extra information to fetch for each
returned record. Currently supported fields are: license, date_upload,
date_taken, owner_name, icon_server, original_format, last_update,
geo, tags, machine_tags, o_dims, views, media.  per_page (Optional)

    Number of photos to return per page. If this argument is omitted, it defaults to 100. The maximum allowed value is 500.
page (Optional)
    The page of results to return. If this argument is omitted, it defaults 
    to 1."""
        rsp = self.execute('flickr.favorites.getList', args=args)
        plist = GFLPhotoList(rsp)
        return plist


    def favorites_getPublicList(self):
        """Not yet implemented"""
        raise NotImplementedError

    def favorites_remove(self):
        """Not yet implemented"""
        raise NotImplementedError

# galleries
    def galleries_addPhoto(self):
        """Not yet implemented"""
        raise NotImplementedError

    def galleries_getList(self):
        """Not yet implemented"""
        raise NotImplementedError

    def galleries_getListForPhoto(self):
        """Not yet implemented"""
        raise NotImplementedError


# groups
    def groups_browse(self):
        """Not yet implemented"""
        raise NotImplementedError

    def groups_getInfo(self):
        """Not yet implemented"""
        raise NotImplementedError

    def groups_search(self):
        """Not yet implemented"""
        raise NotImplementedError

# groups.pools
    def groups_pools_add(self):
        """Not yet implemented"""
        raise NotImplementedError

    def groups_pools_getContext(self):
        """Not yet implemented"""
        raise NotImplementedError

    def groups_pools_getGroups(self):
        """Not yet implemented"""
        raise NotImplementedError

    def groups_pools_getPhotos(self, **args):
        """get photos in a group pool"""
        if not 'group_id' in args:
            raise GaeFlickrLibException, "flickr.groups.pools.getPhotos \
            requires group_id"
        else:
            rsp = self.execute('flickr.groups.pools.getPhotos', args=args)
            plist = GFLPhotoList(rsp)
            return plist

    def groups_pools_remove(self, **args):
        """Remove a photo from a flickr group"""
        if not 'group_id' in args:
            raise GaeFlickrLibException, "flickr.groups.pools.remove requires \
            group_id"
        elif not 'photo_id' in args:
            raise GaeFlickrLibException, "flickr.groups.pools.remove requires \
            photo_id"
        else:
            rsp = self.execute('flickr.groups.pools.remove', args=args)
            return rsp


# interestingness
    def interestingness_getList(self):
        """Not yet implemented"""
        raise NotImplementedError

# machinetags
    def machinetags_getNamespaces(self):
        """Not yet implemented"""
        raise NotImplementedError

    def machinetags_getPairs(self):
        """Not yet implemented"""
        raise NotImplementedError

    def machinetags_getPredicates(self):
        """Not yet implemented"""
        raise NotImplementedError

    def machinetags_getRecentValues(self):
        """Not yet implemented"""
        raise NotImplementedError

    def machinetags_getValues(self):
        """Not yet implemented"""
        raise NotImplementedError

# people
    def people_findByEmail(self):
        """Not yet implemented"""
        raise NotImplementedError

    def people_findByUsername(self):
        """Not yet implemented"""
        raise NotImplementedError

    def people_getInfo(self):
        """Not yet implemented"""
        raise NotImplementedError

    def people_getPhotos(self, user_id = None, **args):
        """get photos by a given user, viewable by the authenticated user"""
        if user_id is None:
            raise GaeFlickrLibException, "user_id not provided"
        else:
            args['user_id'] = user_id
            rsp = self.execute('flickr.people.getPhotos', args=args)
            
            plist = GFLPhotoList(rsp)
            logging.debug(plist)
            if plist:
                return plist
            else:
                raise GaeFlickrLibException, "no photo list"
        

    def people_getPhotosOf(self):
        """Not yet implemented"""
        raise NotImplementedError

    def people_getPublicGroups(self):
        """Not yet implemented"""
        raise NotImplementedError

    def people_getPublicPhotos(self, user_id = None, **args):
        """get a user's public photos"""
        if user_id is None:
            raise GaeFlickrLibException, "user_id not provided"
        else:
            args['user_id'] = user_id
#            for k, v in args.items():
#                logging.debug("%s %s\n"%(k, v))

#            rsp = self.execute_json('flickr.people.getPublicPhotos', args=args)
            rsp = self.execute('flickr.people.getPublicPhotos', args=args)
            
#            logging.debug(rsp)
            plist = GFLPhotoList(rsp)
            logging.debug(plist)
            if plist:
                return plist
            else:
                raise GaeFlickrLibException, "no photo list"

    def people_getUploadStatus(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos
    def photos_addTags(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_delete(self, **args):
        """Delete a photo"""
        if not 'photo_id' in args:
            raise GaeFlickrLibException, "flickr.photos.delete requires \
            photo_id."
        else:
            rsp = self.execute('flickr.photos.delete', args = args)
            return True

    def photos_getAllContexts(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getContactsPhotos(self, **args):
        """Arguments

count (Optional) Number of photos to return. Defaults to 10, maximum
    50. This is only used if single_photo is not passed.

just_friends (Optional) set as 1 to only show photos from friends and
    family (excluding regular contacts).

single_photo (Optional) Only fetch one photo (the latest) per contact,
    instead of all photos in chronological order.

include_self (Optional) Set to 1 to include photos from the calling
    user.

extras (Optional) A comma-delimited list of extra information to fetch
    for each returned record. Currently supported fields are: license,
    date_upload, date_taken, owner_name, icon_server, original_format,
    last_update."""
        rsp = self.execute('flickr.photos.getContactsPhotos', args=args)
        plist = GFLPhotoList(rsp)
        return plist

    def photos_getContactsPublicPhotos(self, **args):
        """Arguments 
        
    user_id (Required) The NSID of the user to fetch photos for.
        
    count (Optional) Number of photos to return. Defaults to 10,
        maximum 50. This is only used if single_photo is not passed.
        
    just_friends (Optional) set as 1 to only show photos from friends
        and family (excluding regular contacts).
        
    single_photo (Optional) Only fetch one photo (the latest) per
        contact, instead of all photos in chronological order.
        
    include_self (Optional)
        Set to 1 to include photos from the user specified by user_id.
        
    extras (Optional) A comma-delimited list of extra information to
        fetch for each returned record. Currently supported fields
        are: license, date_upload, date_taken, owner_name,
        icon_server, original_format, last_update."""
        if not 'user_id' in args:
            raise GaeFlickrLibException, "flickr.photos.getContactsPublic\
            Photos requires user_id"
        else:
            rsp = self.execute('flickr.photos.getContactsPublicPhotos',
                               args=args)
            plist = GFLPhotoList(rsp)
            return plist

    def photos_getContext(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getCounts(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getExif(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getFavorites(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getInfo(self, **args):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getNotInSet(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getPerms(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getRecent(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getSizes(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getUntagged(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getWithGeoData(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_getWithoutGeoData(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_recentlyUpdated(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_removeTag(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_search(self, **args):
        """Search for a photo"""
        if args is None:
            raise GaeFlickrLibException, "search requires parameters"
        else:
            rsp = self.execute('flickr.photos.search', args=args)
            plist = GFLPhotoList(rsp)
            return plist


    def photos_setContentType(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_setDates(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_setMeta(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_setPerms(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_setSafetyLevel(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_setTags(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos.comments(self):
    def photos_comments_addComment(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_comments_deleteComment(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_comments_editComment(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_comments_getList(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_comments_getRecentForContacts(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos.geo(self):
    def photos_geo_batchCorrectLocation(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_correctLocation(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_getLocation(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_getPerms(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_photosForLocation(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_removeLocation(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_setContext(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_setLocation(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_geo_setPerms(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos.licenses
    def photos_licenses_getInfo(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photos_licenses_setLicense(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos.notes
    def photos_notes_add(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photos_notes_delete(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photos_notes_edit(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos.people
    def photos_people_add(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_people_delete(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_people_deleteCoords(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_people_editCoords(self):
        """Not yet implemented"""
        raise NotImplementedError

    def photos_people_getList(self):
        """Not yet implemented"""
        raise NotImplementedError


# photos.transform
    def photos_transform_rotate(self):
        """Not yet implemented"""
        raise NotImplementedError

# photos.upload
    def photos_upload_checkTickets(self):
        """Not yet implemented"""
        raise NotImplementedError

# photosets

    def photosets_addPhoto(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_create(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_delete(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_editMeta(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_editPhotos(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_getContext(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_getInfo(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_getList(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_getPhotos(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_orderSets(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_removePhoto(self):
        """Not yet implemented"""
        raise NotImplementedError

# photosets.comments
    def photosets_comments_addComment(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_comments_deleteComment(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_comments_editComment(self):
        """Not yet implemented"""
        raise NotImplementedError
    def photosets_comments_getList(self):
        """Not yet implemented"""
        raise NotImplementedError

# places
    def places_find(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_findByLatLon(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_getChildrenWithPhotosPublic(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_getInfo(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_getInfoByUrl(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_getPlaceTypes(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_getShapeHistory(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_getTopPlacesList(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_placesForBoundingBox(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_placesForContacts(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_placesForTags(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_placesForUser(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_resolvePlaceId(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_resolvePlaceURL(self):
        """Not yet implemented"""
        raise NotImplementedError
    def places_tagsForPlace(self):
        """Not yet implemented"""
        raise NotImplementedError

# prefs
    def prefs_getContentType(self):
        """Not yet implemented"""
        raise NotImplementedError
    def prefs_getGeoPerms(self):
        """Not yet implemented"""
        raise NotImplementedError
    def prefs_getHidden(self):
        """Not yet implemented"""
        raise NotImplementedError
    def prefs_getPrivacy(self):
        """Not yet implemented"""
        raise NotImplementedError
    def prefs_getSafetyLevel(self):
        """Not yet implemented"""
        raise NotImplementedError

#reflection

    def reflection_getMethodInfo(self):
        """Not yet implemented"""
        raise NotImplementedError
    def reflection_getMethods(self):
        """Not yet implemented"""
        raise NotImplementedError

#stats
    def stats_getCollectionDomains(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getCollectionReferrers(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getCollectionStats(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotoDomains(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotoReferrers(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotosetDomains(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotosetReferrers(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotosetStats(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotoStats(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotostreamDomains(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotostreamReferrers(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPhotostreamStats(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getPopularPhotos(self):
        """Not yet implemented"""
        raise NotImplementedError

    def stats_getTotalViews(self):
        """Not yet implemented"""
        raise NotImplementedError


#tags

    def tags_getClusterPhotos(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getClusters(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getHotList(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getListPhoto(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getListUser(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getListUserPopular(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getListUserRaw(self):
        """Not yet implemented"""
        raise NotImplementedError
    def tags_getRelated(self):
        """Not yet implemented"""
        raise NotImplementedError

#test

    def test_echo(self):
        """Not yet implemented"""
        raise NotImplementedError
    def test_login(self):
        """Not yet implemented"""
        raise NotImplementedError
    def test_null(self):
        """Not yet implemented"""
        raise NotImplementedError

#urls

    def urls_getGroup(self):
        """Not yet implemented"""
        raise NotImplementedError
    def urls_getUserPhotos(self):
        """Not yet implemented"""
        raise NotImplementedError
    def urls_getUserProfile(self):
        """Not yet implemented"""
        raise NotImplementedError
    def urls_lookupGroup(self):
        """Not yet implemented"""
        raise NotImplementedError
    def urls_lookupUser(self):
        """Not yet implemented"""
        raise NotImplementedError

class FlickrAuthSession(db.Model):
    """model to store a user's auth token; key_name is
    to be set to the cookie value.
    """
    tokenobj = db.TextProperty()
    session_date = db.DateTimeProperty(auto_now_add = True)


def _authed(fun, self, perms, optional, *args, **kw):
    """FlickrAuthed helper decorator"""
    logging.debug("in FlickrAuthed decorator: perms %s fun %s self %s",
                  perms, fun, self)
    logging.debug(repr(self.request.cookies))
    if 'gaeflsid' in self.request.cookies:
        authsess = memcache.get(self.request.cookies['gaeflsid'])
        if authsess is None:
            authsessobj = FlickrAuthSession.get_by_key_name(
                self.request.cookies['gaeflsid'])
            if authsessobj is not None:
                authsess = pickle.loads(str(authsessobj.tokenobj))
        if authsess is not None and _perm_ok(authsess['perms'], perms):
            self.flickr = GaeFlickrLib(api_key=API_KEY, api_secret=API_SECRET,
                                             token = str(authsess))
            return fun(self, *args, **kw)
    if not optional:
        logging.debug("no auth session; redirecting")
        self.flickr = GaeFlickrLib(api_key=API_KEY, 
                                   api_secret=API_SECRET)
        self.response.headers["Set-Cookie"] = "gaeflretpage=%s" % self.request.url
        return self.redirect(self.flickr.login_url(perms = perms))
    else:
        self.flickr = GaeFlickrLib(api_key=API_KEY, api_secret=API_SECRET)
        return fun(self, *args, **kw)
    

def FlickrAuthed(arg=None, optional=False):
    """Decorator for webapp.RequestHandler get(), put(), etc. methods
    making method call require Flickr auth session.  To use, do:

    @FlickrAuthed
    get(self):

    (will require 'read' or better permissions)

    or

    @FlickrAuthed('write') #or 'delete' or 'read'
    get(self):

    (to use specified permissions, or better)

    You can also specify optional=True to get the existing auth session but
    continue if there isn't one.

    Your handler method will then have access to the variable "self.flickr" which is
    a GaeFlickrLib object.
    
    """
    if hasattr(arg, '__call__'): #decorator, no argument
        def _wrap(self, *args, **kw):
            return _authed(arg, self, 'read', optional, *args, **kw)
        return _wrap
    else:
        def _decorate(arg2):
            def _wrap(self, *args, **kw):
                return _authed(arg2, self, arg, optional, *args, **kw)
            return _wrap
        return _decorate
                              

class FlickrAuthCallbackHandler(webapp.RequestHandler):
    def get(self):
        from uuid import uuid1

        flickr = GaeFlickrLib(api_key=API_KEY, api_secret=API_SECRET)
        frob = self.request.get('frob')
        tokenobj = flickr.auth_getToken(frob = frob)
        sessid = str(uuid1())
        self.response.headers["Set-Cookie"] = "gaeflsid=%s" % sessid
        memcache.set(sessid, tokenobj, namespace='gaeflsid')
        pto = pickle.dumps(tokenobj)
        fas = FlickrAuthSession(tokenobj = pto, key_name = sessid)
        fas.put()

        if 'gaeflretpage' in self.request.cookies:
#             self.response.headers["Set-Cookie"] = "gaeflretpage=nil; expires=\
#             Fri, 31-Dec-2009 23:59:59 GMT"
            self.redirect(self.request.cookies['gaeflretpage'])
        else:
            self.redirect('/')
