#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask
import views

if __name__ == '__main__':
    app = flask.Flask(__name__)
    # Add settings here
    app.config.update(
        DEBUG=True,
    )
    app.add_url_rule('/', view_func=views.IndexView.as_view('index'))
    app.add_url_rule(
        '/<string:file_name>',
        view_func=views.IndexView.as_view('download')
    )
    preview_view = views.PreviewAPI.as_view('preview_api')
    app.add_url_rule(
        '/preview/<string:file_name>',
        view_func=preview_view,
        methods=['GET']
    )
    app.run(host='0.0.0.0', port=8889)
