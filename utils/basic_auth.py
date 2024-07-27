from functools import wraps
from global_constants import GlobalConstants
from flask import current_app, request, Response

global_constants = GlobalConstants


class BasicAuth(object):
    def check_credentials(self, username, password):
        correct_username = current_app.config[
            global_constants.basic_auth_parameters.basic_auth_username
        ]
        correct_password = current_app.config[
            global_constants.basic_auth_parameters.basic_auth_password
        ]
        return username == correct_username and password == correct_password

    def authenticate(self):
        auth = request.authorization
        return (
            auth
            and auth.type == global_constants.auth_types.basic
            and self.check_credentials(auth.username, auth.password)
        )

    def challenge(self):
        realm = current_app.config[
            global_constants.basic_auth_parameters.basic_auth_realm
        ]
        return Response(
            status=401,
            headers={
                global_constants.basic_auth_parameters.www_authenticate: 'Basic realm="%s"'
                % realm
            },
        )

    def required(self, view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if self.authenticate():
                return view_func(*args, **kwargs)
            else:
                return self.challenge()

        return wrapper


basic_auth = BasicAuth()
