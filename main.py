#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import SimpleHTTPServer
import BaseHTTPServer
import SocketServer

PORT = 8000
BASE_DIR = os.path.dirname(  # eark-python-bridge
    os.path.realpath(__file__)  # this script
)
DATA_DIR = BASE_DIR + '/data/'


class Handler(BaseHTTPServer.BaseHTTPRequestHandler, object):

    def _set_header(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        try:
            list = os.listdir(DATA_DIR)
        except os.error:
            self.send.error(404, "No permission to list directory")
        list.sort(key=lambda a: a.lower)
#        displaypath = cgi.escape(urllib.unquote(self.path))
        for name in list:
            fullname = os.path.join(DATA_DIR, name)
            displayname = linkname = name
            if os.path.isdir(fullname):
                diplayname = name + '/'
                linkname = name + '/'
            {
                'name': os.path.basename(fullname),
                # 'rights': ,
                # 'date': ,
                'size': os.path.getsize(fullname),
                # 'type':
            }
        self._set_header(200)
        ret = json.dumps('Hello!')
        self.wfile.write(ret)

    def do_POST(self):
        pass


if __name__ == '__main__':

    httpd = SocketServer.TCPServer(("", PORT), Handler)
    print "serving at port:", PORT
    httpd.serve_forever()