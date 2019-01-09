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
    c = datetime.datetime.strptime(b, "%Y-%m-%dT%H:%M:%SZ") - datetime.datetime.strptime(a, "%Y-%m-%dT%H:%M:%SZ")
    
    log_message = "{0!s} {0!s} http status code: {0!s} took {{0!s}".format(str(datetime.datetime), val[0], r.status_code, c)
    print(log_message)
    channel.basic_publish(exchange='', routing_key='hello', body=body)
    #channel.basic_publish(exchange='', routing_key='log', body=log_message)
    print(" [x] Sent '%r'" % val)

channel.basic_consume(callback,
                      queue='hello',
                      no_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
