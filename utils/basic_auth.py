from functools import wraps
from flask import current_app, request, Response


class BasicAuth(object):
    def __init__(self, global_constants):
        self.global_constants = global_constants

    def check_credentials(self, username, password):
        correct_username = current_app.config[
            self.global_constants.basic_auth_parameters.basic_auth_username
        ]
        correct_password = current_app.config[
            self.global_constants.basic_auth_parameters.basic_auth_password
        ]
        return username == correct_username and password == correct_password

    def authenticate(self):
        auth = request.authorization
        return (
            auth
            and auth.type == self.global_constants.auth_types.basic
            and self.check_credentials(auth.username, auth.password)
        )

    def challenge(self):
        realm = current_app.config[
            self.global_constants.basic_auth_parameters.basic_auth_realm
        ]
        return Response(
            status=401,
            headers={
                self.global_constants.basic_auth_parameters.www_authenticate: 'Basic realm="%s"'
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
