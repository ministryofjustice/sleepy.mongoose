import StringIO
from sleepymongoose.handlers import MongoHandler
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, MethodNotAllowed
from werkzeug.wrappers import Request, Response


class MongoServer(object):
    """
    a simple wsgi server object that provides a lightweight and generic rest api over mongodb storage
    note that this object does not serve any static files
    """

    def __init__(self, config):
        self.mh = MongoHandler(mongos=[config.get('uri', 'localhost')],
                               replicaSet=config.get('replicaset', None))
        self.url_map = Map([
            Rule('/<action>', endpoint='call_function'),
            Rule('/<db>/<collection>/<action>', endpoint='call_function'),
        ])

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except HTTPException, e:
            return e

    def on_call_function(self, request, db=None, collection=None, action=None):
        output = StringIO.StringIO()
        args = request.values

        # let's patch args so they are closer to cgi.FieldStorage
        args.getvalue = lambda x: args.get(x)
        name = args.get("name", "default")

        func = getattr(self.mh, action, None)
        if callable(func):
            func(args, output.write, name=name, db=db, collection=collection, method=request.method)
            return Response(output.getvalue(), mimetype="application/json")
        else:
            raise MethodNotAllowed()

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def create_app(config):
    app = MongoServer(config)
    return app

