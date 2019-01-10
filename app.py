#!/usr/bin/env python
import pika
import datetime
import requests

connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq.check-sites.svc.cluster.local'))
channel = connection.channel()


channel.queue_declare(queue='hello')
channel.queue_declare(queue='log')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    val = str(body).split(',')
    a = datetime.datetime.now()
    r = requests.get(body)
    b = datetime.datetime.now()
    delta = b - a
    body_text = r.text
    title = body_text[body_text.find('<title>') + 7 : body_text.find('</title>')]

    log_message = "{0} {1} http status code: {2} took {3} seconds. Title found: '{4}'".format(str(datetime.datetime.now()), 
                                                                          body, 
                                                                          r.status_code,
                                                                          delta.total_seconds(),
                                                                          title)
    
    print(log_message)
    channel.basic_publish(exchange='', routing_key='hello', body=body)
    #channel.basic_publish(exchange='', routing_key='log', body=log_message)
    print(" [x] Sent '%r'" % val)

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
