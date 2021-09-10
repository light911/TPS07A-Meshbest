#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 11 19:34:31 2021

@author: blctl
"""

from multiprocessing import Pool, Manager

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer
import json
import cgi
import random, time

# Resources to read
#
# http://stackoverflow.com/a/1239252/603280
# http://stackoverflow.com/questions/13689927/how-to-get-the-amount-of-work-left-to-be-done-by-a-python-multiprocessing-pool
#


# This is your task which will run its its own process. You can modify it to have your desired args and kwargs and
# report back to the manager dictionary 'd' or any other manager resource as necessary.
# Read the documentation for multiprocessing to find the facilities provided by multiprocess.Manager
def task(d, sessionid, number, repeatcount):
    """
    This function is a stub funciton which is incrementing a success counter in a random time between 0 to 2 seconds
    with a 2% chance that the failure counter will be incremented instead of the success. After each success or failure
    the manager dictionary 'd' is updated with the session's progress.
    You should replace this with an actual task and update necessary information about the task into the manager dict
    """
    success = 0
    fail = 0
    while success+fail<repeatcount:
        time.sleep(random.random()*2.0)
        if (random.random()*100)>98.0:
            fail+=1
        else:
            success+=1
        d[sessionid] = {
            'success': success,
            'fail': fail,
            'number': number,
            'repeatcount': repeatcount
            }
    return

# Initializing our global resources.
p = Pool()
m = Manager()
d = m.dict()

# This is the HTTP Server which provides a simple JSON REST API
class Server(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_HEAD(self):
        self._set_headers()

    # GET sends back the complete contents of the manager dictionary 'd' as JSON.
    # This can be modified to any desired response (should be JSON)
    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps(d))

    # POST echoes the message adding a JSON field
    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))

        # refuse to receive non-json content
        if ctype != 'application/json':
            self.send_response(400)
            self.end_headers()
            return

        # read the message and convert it into a python dictionary
        length = int(self.headers.getheader('content-length'))
        message = json.loads(self.rfile.read(length))

        if message.has_key('runtask'):
            """
            To run a new task simply send the following JSON as POST:
            {"runtask": true, "sessionid": "ANY-UNIQUE-NAME-FOR-YOUR-TASK", 'arg1', 'repeatcount'}
            Curl Syntax:
            curl --data "{\"runtask\":\"true\", \"sessionid\":\"session-5\", \"number\":\"+\", \"repeatcount\": 100 }" \
            --header "Content-Type: application/json" http://localhost:8111
            """
            print "Starting task with %s, %s, %s" % (message['sessionid'], message['number'], message['repeatcount'])
            result = p.apply_async(task, (d, message['sessionid'], message['number'], message['repeatcount']))
        elif message.has_key('sessionid'):
            """
            To see the status of a currently running task (or completed task) simpley POST the following JSON
            {"sessionid": "THE-UNIQUE-NAME-FOR-YOUR-TASK"}
            Curl Syntax:
            curl --data "{\"sessionid\":\"session-5\"}" --header "Content-Type: application/json" http://localhost:8111
            """
            message['status'] = d[message['sessionid']]

        # send the message back
        self._set_headers()
        self.wfile.write(json.dumps(message))


def run(server_class=HTTPServer, handler_class=Server, port=8111):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    print 'Starting httpd on port %d...' % port
    httpd.serve_forever()

if __name__ == "__main__":
    # Run the task broker.
    run()