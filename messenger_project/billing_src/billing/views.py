from django.conf import settings
from django.utils.datastructures import SortedDict
from django.db.models import Count
from rapidsms.models import Backend
from rapidsms_httprouter.models import Message
import datetime
from django.shortcuts import render_to_response
from django.template import RequestContext

def summary(request):
    messages = SortedDict()
    prjs = SortedDict()
    d = datetime.datetime.now()
    years = range(2010, d.year + 1)
    start_date = datetime.datetime(2010, 1, 1)
    months = range(1, 13)
    backends = []
    dbs = settings.DATABASES.keys()
    for db in dbs:
        if db == 'default':
            continue
        bs = list(Backend.objects.using(db).exclude(name='console').exclude(connection__backend__name__icontains='modem').order_by('name').values_list('name', flat=True))
        for b in bs:
            if b not in backends:
                backends.append(b)
    backends = sorted(backends)

    directions = ['I', 'O']
    for y in years:
        messages[y] = SortedDict()
        for m in months:
            messages[y][m] = SortedDict()
            for b in backends:
                messages[y][m][b] = SortedDict()
                for d in directions:
                    messages[y][m][b][d] = 0

    for db in dbs:
        if db == 'default':
            continue
        app_messages = Message.objects.using(db)\
                .filter(date__gte=start_date)\
                .exclude(status__in=['L', 'P', 'Q', 'C'])\
                .exclude(connection__backend__name='console')\
                .exclude(connection__backend__name='console').exclude(connection__backend__name__icontains='modem')\
                .extra({'year':'extract (year from rapidsms_httprouter_message.date)', \
                         'month':'extract (month from rapidsms_httprouter_message.date)'})\
                .values('year', 'month', 'connection__backend__name', 'direction')\
                .annotate(total=Count('id'))\
                .extra(order_by=['year', 'month', 'connection__backend__name', 'direction'])
        for dct in app_messages:
            y = int(dct['year'])
            m = int(dct['month'])
            b = dct['connection__backend__name']
            d = dct['direction']
            t = dct['total']
            prjs[db] = t
            messages[y][m][b][d] = prjs
            
    dbs.remove('default')
    return render_to_response(
        "billing/summary.html",
        { 'messages': messages, 'backends':backends, 'db_count':len(dbs)}, context_instance=RequestContext(request))

