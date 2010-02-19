from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from handlers import MongoHandler

import os.path
import urlparse
import json
import cgi

class MongoServer(BaseHTTPRequestHandler):

    mh = None

    mimetypes = { "html" : "text/html",
                  "htm" : "text/html",
                  "gif" : "image/gif",
                  "jpg" : "image/jpeg",
                  "png" : "image/png",
                  "json" : "text/json",
                  "css" : "text/css",
                  "js" : "text/js",
                  "ico" : "image/vnd.microsoft.icon" }

    def _parse_call(self, uri):
        """ 
        this turns a uri like: /foo/bar/_query into properties: using the db 
        foo, the collection bar, executing a query.

        returns the database, collection, and action
        """

        parts = uri.split('/')

        # operations always start with _
        if parts[-1][0] != '_':
            return (None, None, None)

        if len(parts) == 1:
            return ("admin", None, parts[0])
        elif len(parts) == 2:
            return (parts[0], None, parts[1])
        else:
            return (parts[0], ".".join(parts[1:-1]), parts[-1])


    def call_handler(self, uri, args):
        """ execute something """

        (db, collection, func_name) = self._parse_call(uri)
        if db == None or func_name == None:
            self.send_error(404, 'Script Not Found: '+uri)
            return

        func = getattr(MongoServer.mh, func_name, None)
        if callable(func):
            self.send_response(200, 'OK')
            self.send_header('Content-type', MongoServer.mimetypes['json'])
            self.end_headers()

            func(db, collection, args, self.wfile.write)

            return
        else:
            self.send_error(404, 'Script Not Found: '+uri)
            return            
        

    # TODO: check for ..s
    def process_uri(self, method):
        if method == "GET":
            (uri, q, args) = self.path.partition('?')
        else:
            uri = self.path
            if 'Content-Type' in self.headers:
                args = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
                                        environ={'REQUEST_METHOD':'POST',
                                                 'CONTENT_TYPE':self.headers['Content-Type']})
            else:
                self.send_response(100, "Continue")
                self.send_header('Content-type', MongoServer.mimetypes['json'])
                self.end_headers()
                self.wfile.write('{"ok" : 0, "errmsg" : "100-continue msgs not handled yet"}')

                return (None, None, None)


        uri = uri.strip('/')

        # default "/" to "/index.html"
        if len(uri) == 0:
            uri = "index.html"

        (temp, dot, type) = uri.rpartition('.')
        if len(dot) == 0:
            type = ""

        return (uri, args, type)


    def do_GET(self):        
        (uri, args, type) = self.process_uri("GET")

 
        # serve up a plain file
        if len(type) != 0:
            if type in MongoServer.mimetypes and os.path.exists(uri):

                fh = open(uri, 'r')

                self.send_response(200, 'OK')
                self.send_header('Content-type', MongoServer.mimetypes[type])
                self.end_headers()
                self.wfile.write(fh.read())

                fh.close()

                return

            else:
                self.send_error(404, 'File Not Found: '+uri)

                return

        # make sure args is an array of tuples
        if len(args) != 0:
            args = urlparse.parse_qs(args)
        else:
            args = {}

        self.call_handler(uri, args)
        #self.wfile.write( self.path )

    def do_POST(self):
        (uri, args, type) = self.process_uri("POST")
        if uri == None:
            return
        self.call_handler(uri, args)


    @staticmethod
    def serve_forever(port):
        print "\n================================="
        print "| MongoDB Sharding Admin Server |"
        print "=================================\n"
        print "listening for connections on http://localhost:27080\n"

        MongoServer.mh = MongoHandler()

        server = HTTPServer(('', port), MongoServer)

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print "\nShutting down the server..."
            server.socket.close()
            print "\nGood bye!\n"


if __name__ == "__main__":
    MongoServer.serve_forever(27080)
