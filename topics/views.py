from django.http import HttpResponse
from django.template import Context, loader
from topics.models import Topic

def topicView(request, topicName):
    t = loader.get_template('topics/topicView.html')
    c = Context({'topicName' : topicName})

    # See if topic has been started
    topic_query  = Topic.objects.filter(name=topicName)
    if len(topic_query) > 0:
        c['started'] = True
    else:
        c['started'] = False
    return HttpResponse(t.render(c))
