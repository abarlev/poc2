#!/usr/bin/env python
import pika
import datetime
import requests
import json

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq.check-sites.svc.cluster.local'))
channel = connection.channel()

print("NEW VERSION!!! (checking for uppercase title tags)")

channel.queue_declare(queue='sites')
channel.queue_declare(queue='log')

def callback(ch, method, properties, body):
    data = json.loads(body)
    #print(" [x] Received %r" % data)
    
    timeout = False
    title_match = False
    is_title = False
    
    a = datetime.datetime.now()
    try:
        r = requests.get(data['Site'])
    except Exception as e:
        timeout = True
        log_message = "{0} Exception: {1} URL: {2}".format(str(datetime.datetime.now()), str(e), data['Site'])
    b = datetime.datetime.now()
    if not timeout:
        delta = b - a
        body_text = r.text
        start = body_text.find('<title>') + 7
        end = body_text.find('</title>')
        print("start: {0}, end: {1}".format(start, end))
        is_title = True
        if start > 7:
            title = body_text[start : end].strip()
            #print('title: {0}, data["Title"]: {1}'.format(title, data['Title']))
            if title == data['Title'].strip():
                title_match = True
            else:
                start = body_text.find('<TITLE>') + 7
                end = body_text.find('</TITLE>')
                print("start: {0}, end: {1}".format(start, end))
                title = body_text[start : end].strip()
                if start > 7 and title == data['Title'].strip():
                    title_match = True
                else:
                    title_match = False
        else:
            title = 'no title found'

        log_message = "{0} URL: {1} http status code: {2} took {3} seconds. Title match: {4}".format(str(datetime.datetime.now()),
                                                                              data['Site'],
                                                                              r.status_code,
                                                                              delta.total_seconds(),
                                                                              title_match)
        if is_title and not title_match:
            log_message = "{0}, expected: {1}, found: {2}".format(log_message, data['Title'].strip(), title.strip())
        if data['URLafterRedirect'] == r.url:
            log_message = "{0}, URL redirect as expected".format(log_message)
        else:
            log_message = "{0}, URL redirect mismatch. Expected: {1}, found: {2}".format(log_message, data['URLafterRedirect'], r.url)
    print(log_message)
    
    channel.basic_publish(exchange='', routing_key='sites', body=body)
    #print(" [x] Sent '%r'" % body)

channel.basic_consume(callback,
                      queue='sites',
                      no_ack=True)

print(' [*] Waiting for messages.')
try:
    channel.start_consuming()
except Exception as e:
    print('Problem with accessing the queue: ' + str(e))
