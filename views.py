# -*- coding: utf-8 -*-
import os

import flask.views
from handlers import FileManagerHandler


class IndexView(flask.views.View):
    methods = ['GET', 'POST']

    def dispatch_request(self, file_name=None):
        handler = FileManagerHandler()
        if flask.request.method == 'GET':
            return handler.get(flask.request, file_name)
        elif flask.request.method == 'POST':
            return handler.post(flask.request)
        else:
            # This code is never reached: The @app.route decorator
            # handles this automatically.
            return flask.jsonify(
                error=405,
                text='Not Allowed'
            )


class PreviewAPI(flask.views.MethodView):
    methods = ['GET']

    def get(self, file_name):
        path = FileManagerHandler.PREVIEW_DIR + file_name
        if os.path.exists(path):
            with open(path, 'r') as file:
                try:
                    content = file.read()
                except os.error:
                    flask.abort(500)
                finally:
                    file.close()
                    response = flask.make_response(content)
                    response.headers['Content-Type'] = \
                        FileManagerHandler.MIME_PDF
                    return response
        else:
            flask.abort(404)
