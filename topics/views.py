from django.http import HttpResponse
from django.template import Context, loader


from topics.models import Topic

# Logging
import logging
logger = logging.getLogger("testlog")

def topic_view(request, topicName):
    t = loader.get_template('topics/topicview.html')
    c = Context({'topicName' : topicName})

    # See if topic has been started
    topic_query  = Topic.objects.filter(name=topicName)
    if len(topic_query) > 0:
        c['started'] = True
    else:
        c['started'] = False
    return HttpResponse(t.render(c))

def start_topic(request):
    if request.method == 'POST':
        start_topic_name = request.POST['start_topic_name']
        Topic.objects.create(name=start_topic_name)
    else:
        logger.debug('Received requet but not POST')
    return HttpResponse('ok');
