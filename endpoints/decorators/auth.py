from __future__ import absolute_import
import logging

from decorators import FuncDecorator

from ..exception import CallError, AccessDenied


logger = logging.getLogger(__name__)


class auth(FuncDecorator):
    """
    handy auth decorator that makes doing basic or token auth easy peasy

    This is more of a base class for the other auth decorators, but it can be used
    on its own if you want, but I would look at the other decorators first

    the request get_auth_client(), get_auth_basic(), and get_auth_bearer() methods
    and access_token property should come in real handy here

    example --

    # create a token auth decorator
    from endpoints import Controller
    from endpoints.decorators.auth import auth

    def target(request):
        if request.access_token != "foo":
            raise ValueError("invalid access token")

    class Default(Controller):
        @auth("Bearer", target=target)
        def GET(self):
            return "hello world"
    """
    def normalize_target_params(self, request, *args, **kwargs):
        param_args = [request] + list(args)
        return param_args, kwargs

    def target(self, request, *args, **kwargs):
        try:
            return self.target_callback(request, *args, **kwargs)

        except (AttributeError, TypeError) as e:
            logger.debug(e, exc_info=True)
            raise CallError(403, "You need a validator function to use authentication")

    def handle_target(self, request, *args, **kwargs):

        try:
            param_args, param_kwargs = self.normalize_target_params(request, *args, **kwargs)
            ret = self.target(*param_args, **param_kwargs)
            if not ret:
                raise ValueError("target did not return True")

        except CallError:
            raise

        except Exception as e:
            logger.debug(e, exc_info=True)
            raise AccessDenied(self.realm, e.message)

    def decorate(self, func, realm='', target=None, *anoop, **kwnoop):
        self.realm = realm
        if target:
            self.target_callback = target

        def decorated(decorated_self, *args, **kwargs):
            self.handle_target(decorated_self.request, *args, **kwargs)
            return func(decorated_self, *args, **kwargs)

        return decorated


class basic_auth(auth):
    """
    handy basic auth decorator that checks for username, password in an auth header

    example --

    # create a token auth decorator
    from endpoints import Controller
    from endpoints.decorators.auth import basic_auth

    def target(request, username, password):
        return username == "foo" and password == "bar"

    class Default(Controller):
        @basic_auth(target=target)
        def GET(self):
            return "hello world"
    """
    def normalize_target_params(self, request, *args, **kwargs):
        username, password = request.get_auth_basic()

        if not username: raise ValueError("username is required")
        if not password: raise ValueError("password is required")

        kwargs = {
            "request": request,
            "username": username,
            "password": password,
        }
        return [], kwargs

    def decorate(self, func, target):
        return super(basic_auth, self).decorate(func, realm="basic", target=target)


class client_auth(basic_auth):
    """
    handy OAuth client auth decorator that checks for client_id and client_secret

    example --

    # create a token auth decorator
    from endpoints import Controller
    from endpoints.decorators.auth import client_auth

    def target(request, client_id, client_secret):
        return client_id == "foo" and client_secret == "bar"

    class Default(Controller):
        @client_auth(target=target)
        def GET(self):
            return "hello world"
    """
    def normalize_target_params(self, request, *args, **kwargs):
        client_id, client_secret = request.client_tokens

        if not client_id: raise ValueError("client_id is required")
        if not client_secret: raise ValueError("client_secret is required")

        kwargs = {
            "request": request,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        return [], kwargs

    def decorate(self, func, target):
        return super(client_auth, self).decorate(func, target=target)


class token_auth(auth):
    """
    handy token auth decorator that checks for access_token in an authorization
    Bearer header

    example --

    # create a token auth decorator
    from endpoints import Controller
    from endpoints.decorators.auth import token_auth

    def target(request, access_token):
        return access_token == "foo"

    class Default(Controller):
        @token_auth(target=target)
        def GET(self):
            return "hello world"
    """
    def normalize_target_params(self, request, *args, **kwargs):
        access_token = request.access_token

        if not access_token: raise ValueError("access_token is required")

        kwargs = {
            "request": request,
            "access_token": access_token,
        }
        return [], kwargs

    def decorate(self, func, target):
        return super(token_auth, self).decorate(func, realm="Bearer", target=target)

