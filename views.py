# -*- coding: utf-8 -*-

import flask.views
import lib.handler

class IndexView(flask.views.View):
    methods = ['GET', 'POST']

    def dispatch_request(self):
        handler = lib.handler.FileManagerHandler()
        if flask.request.method == 'GET':
            return handler.get(flask.request)
        elif flask.request.method == 'POST':
            return handler.post(flask.request)
        else:
            # This code is never reached: The @app.route decorator
            # handles this automatically.
            return flask.jsonify(
                error=405,
                text='Not Allowed'
            )
