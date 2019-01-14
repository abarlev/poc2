#!/usr/bin/env python
import pika
import datetime
import requests
import json
import re

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq.check-sites.svc.cluster.local'))
channel = connection.channel()

print("NEW VERSION!!! (added my_strip())")

channel.queue_declare(queue='sites')
channel.queue_declare(queue='log')

def do_titles_match(data, r):
    print('do_titles_match()')
    expected_title = my_strip(data['Title'])
    if len(expected_title) <= 1:
        return false
    actual_title = get_title(r.text)
    return expected_title == actual_title

def get_title(body):
    print('get_title()')
    body = my_strip(body)
    start = body.find('<title>') + 7
    end = body.find('</title>')
    print("start: {0}, end: {1}".format(start, end))
    if start > 7 and end > 7:
        title = my_strip(body[start : end])
        return title
    start = body.find('<TITLE>') + 7
    end = body.find('</TITLE>')
    print("start: {0}, end: {1}".format(start, end))
    if start > 7 and end > 7:
        title = my_strip(body[start : end])
        return title
    return ''
    
def my_strip(text):
    return re.sub(' +', ' ', re.sub(r"[\n\t\s]", ' ', text)).strip()
    
def callback(ch, method, properties, body):
    data = json.loads(body)
    #print(" [x] Received %r" % data)
    
    timeout = False
    title_match = False
    is_title = False
    return_to_queue = True
    
    a = datetime.datetime.now()
    try:
        r = requests.get(data['Site'])
    except Exception as e:
        timeout = True
        log_message = "{0} Exception: {1} URL: {2}".format(str(datetime.datetime.now()), str(e), data['Site'])
        return_to_queue = False
    b = datetime.datetime.now()
    
    if not timeout:
        delta = b - a
        
        titles_match = do_titles_match(body, r)
        if not titles_match:
            actual_title = get_title(r.text)
            expected_title = my_strip(data['Title'])

        log_message = "{0} URL: {1} http status code: {2} took {3} seconds. Title match: {4}".format(str(datetime.datetime.now()),
                                                                              data['Site'],
                                                                              r.status_code,
                                                                              delta.total_seconds(),
                                                                              titles_match)
        if not titles_match:
            log_message = "{0}, expected: {1}, found: {2}".format(log_message, expected_title, actual_title)
        if data['URLafterRedirect'] == r.url:
            log_message = "{0}, URL redirect as expected".format(log_message)
        else:
            log_message = "{0}, URL redirect mismatch. Expected: {1}, found: {2}".format(log_message, data['URLafterRedirect'], r.url)
    print(log_message)
    
    if return_to_queue:
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
