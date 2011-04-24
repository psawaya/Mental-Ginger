from django.conf.urls.defaults import *

from django.contrib import admin
admin.autodiscover()

handler500 = 'djangotoolbox.errorviews.server_error'

urlpatterns = patterns('',
    (r'admin/', include(admin.site.urls)),
    (r'^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'index.html'}),
    (r'^search', 'imagesearch.views.searchHandler'),
    (r'^topic/(?P<topicName>.+)/$', 'topics.views.topic_view'),
    (r'^topic2/$', 'django.views.generic.simple.direct_to_template',
        {'template': 'topics/topicview2.html'}),

)
