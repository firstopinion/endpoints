from __future__ import absolute_import

from . import BaseInterface, BaseServer


class WSGI(BaseInterface):
    def create_request(self, raw_request, **kwargs):
        """
        create instance of request

        raw_request -- mongrel2.request.Request() -- the request object retrieved from mongrel2
        """
        r = self.request_class()
        for k, v in raw_request.iteritems():
            if k.startswith('HTTP_'):
                r.headers[k[5:]] = v

        r.method = raw_request['REQUEST_METHOD']
        r.path = raw_request['PATH_INFO']
        r.query = raw_request['QUERY_STRING']
        r.raw_request = raw_request

        if r.is_method('POST'):
            r.body = raw_request['wsgi.input'].read()

        else:
            r.body = None

        return r


class Server(BaseServer):
    interface_class = WSGI

    def __call__(self, environ, start_response):
        return self.application(environ, start_response)

    def application(self, environ, start_response):
        res = self.interface.handle(environ)

        start_response(
            '{} {}'.format(res.code, res.status),
            [(k, v) for k, v in res.headers.iteritems()]
        )
        return [res.body]

    def create_server(self, **kwargs):
        return None

    def handle_request(self):
        raise NotImplemented("WSGI is used through application() method")

    def serve_forever(self):
        raise NotImplemented("WSGI is used through application() method")

    def serve_count(self, count):
        raise NotImplemented("WSGI is used through application() method")

