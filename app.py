#!/usr/bin/env python
import pika
import datetime
import requests
import json

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq.check-sites.svc.cluster.local'))
channel = connection.channel()


channel.queue_declare(queue='sites')
channel.queue_declare(queue='log')

def callback(ch, method, properties, body):
    data = json.loads(body)
    print(" [x] Received %r" % data)
    
    timeout = False
    title_match = False
    is_title = False
    
    a = datetime.datetime.now()
    try:
        r = requests.get(data['Site'])
    except Exception as e:
        timeout = True
        log_message = "{0} Exception: {1} URL: {2}".format(str(datetime.datetime.now()), str(e), body)
    b = datetime.datetime.now()
    if not timeout:
        delta = b - a
        body_text = r.text
        start = body_text.find('<title>') + 7
        end = body_text.find('</title>')
        is_title = True
        if start > 7:
            title = body_text[start : end]
            if title == data['Title']:
                title_match = True
            else:
                title_match = False
        else:
            title = 'no title found'

        log_message = "{0} {1} http status code: {2} took {3} seconds. Title match: {4}".format(str(datetime.datetime.now()), 
                                                                              body, 
                                                                              r.status_code,
                                                                              delta.total_seconds(),
                                                                              title_match)
        if is_title and not title_match:
            log_message = "{0}, expected: {1}, found: {2}".format(log_message, title, data[Title])
    print(log_message)
    # Not refilling queue yet
    #channel.basic_publish(exchange='', routing_key='hello', body=body)
    #print(" [x] Sent '%r'" % body)

channel.basic_consume(callback,
                      queue='sites',
                      no_ack=True)

print(' [*] Waiting for messages.')
try:
    channel.start_consuming()
except Exception as e:
    print('Problem with accessing the queue: ' + str(e))
