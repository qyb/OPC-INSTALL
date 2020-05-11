# -*- encoding: utf-8 -*-
import binascii
import struct
import socket
from datetime import datetime
from socketserver import BaseRequestHandler
import sys
import pika
from butils import TimedRotatingLogger
REPEATER_LOG = TimedRotatingLogger('Repeater-Log.txt')

class RepeaterHandler(BaseRequestHandler):
    def handle(self):
        REPEATER_LOG.info('Got connection from: %s', str(self.client_address))
        AMQPURL = 'amqp://guest:guest@localhost:5672/%2F'
        parameters = pika.URLParameters(AMQPURL)
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
        except:
            return
        channel.exchange_declare(exchange='agent', exchange_type='fanout')
        while True:
            try:
                header = self.request.recv(8)
                length, checksum = struct.unpack('II', header)

                wait = length
                body = b''
                while True:
                    chunk = self.request.recv(wait)
                    x = len(chunk)
                    if x == 0:
                        raise socket.error
                    body = body + chunk
                    if x == wait:
                        break
                    wait = wait - x
                # body = self.request.recv(length)
                if checksum != binascii.crc32(body):
                    print('checksum error')
                    break
                channel.basic_publish(
                    exchange='agent',
                    routing_key='',
                    body=body)
                REPEATER_LOG.info("%d, %d", length, checksum)
            except:
                REPEATER_LOG.error(str(sys.exc_info()))
                break
