from django.http import HttpResponse
from django.template import Context, loader

def topicView(request, topicName):
    c = Context({'topicName' : topicName})
    t = loader.get_template('index.html')
    return HttpResponse(t.render(c))


