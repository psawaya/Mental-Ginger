from django.http import HttpResponse
from django.template import Context, loader

from topics.models import Image
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
        logger.debug('Received request but not POST')
    return HttpResponse('ok');


def update_topic(request):
    if request.method == 'POST':
        topic_name = request.POST['topic_name']
        image_src = request.POST['image_src']
        image_left = request.POST['image_left']
        image_top = request.POST['image_top']
        logger.debug(topic_name);
        logger.debug(image_src);
        logger.debug(image_left);
        logger.debug(image_top);

        # Get the topic.
        topic_query = Topic.objects.filter(name=topic_name)
        if len(topic_query) > 0:
            topic = topic_query[0]

        # Find the image if it already exists.
        image_query = Image.objects.filter(topic=topic).filter(url=image_src)
        if len(image_query) > 0:
            image = image_query[0]
            image.left = image_left
            image.top = image_top
            image.save()
        else:
            image = Image.objects.create(url=image_src, topic=topic,
                left=image_left, top=image_top);
    return HttpResponse('ok');
