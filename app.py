#!/usr/bin/env python
# -*- coding: utf-8 -*-

import flask
import views

if __name__ == '__main__':
    app = flask.Flask(__name__)
    app.add_url_rule('/', view_func=views.IndexView.as_view('index'))
    app.run()
