from django.conf.urls.defaults import *

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
    ('^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'index.html'}),
    ('^search', 'imagesearch.views.searchHandler'),
)
