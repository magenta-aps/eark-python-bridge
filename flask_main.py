#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import flask
import lib.handler
app = flask.Flask(__name__)


@app.route('/', methods=['GET','POST'])
def index():
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

if __name__ == '__main__':
    app.run()