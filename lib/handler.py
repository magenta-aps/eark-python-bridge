# -*- coding: utf-8 -*-

import datetime
import urllib
import posixpath
import flask
import os


class FileManagerHandler(object):
    BASE_DIR = os.path.dirname(  # eark-python-bridge
        os.path.dirname(  # lib
            os.path.realpath(__file__)  # this script
        )
    )
    DATA_DIR = BASE_DIR + '/data/'

# -*- Dispatched functions need to go here -*- #
    def list(self, request):
        path = self.translate_path(request.form['path'])
        try:
            list = os.listdir(path)
        except os.error:
            return flask.jsonify(
                error=404,
                text='Not Found'
            )
        files = []
        for item in list:
            fullpath = os.path.join(path, item)
            file = dict(
                name=item,
                size=os.path.getsize(fullpath),
                date=datetime.datetime
                    .fromtimestamp(os.path.getmtime(fullpath)).isoformat(),
                type=self._get_file_type(fullpath)
            )
            files.append(file)
        return flask.jsonify(files=files)

    def get_content(self, request):
        path = self.translate_path(request.form['path'])
        if os.path.exists(path):
            with open(path, 'r') as file:
                try:
                    content = file.read()
                except os.error:
                    return flask.jsonify(
                        error=500,
                        text='Internal Server Error'
                    )
                finally:
                    if file:
                        file.close()

                return flask.jsonify(result=content)
        else:
            return flask.jsonify(
                error=404,
                text='Not Found'
            )

# -*- endblock -*- #

    modes = {
        'list': list,
        'getcontent': get_content,
    }

    def post(self, request):
        return self.dispatch(request)

    def get(self, request):
       return flask.jsonify(error='Not implemented.')

    def dispatch(self, request):
        """
        Dispatches to methods that handle the different modes.
        :param request:
        :return:
        """
        mode = request.form['mode'].lower()
        func = self.modes[mode].__get__(self, type(self))
        return func(request)

    def _get_file_type(self, fullpath):
        if os.path.isfile(fullpath):
            return 'file'
        elif os.path.isdir(fullpath):
            return 'directory'
        elif os.path.islink(fullpath):
            return 'symlink'
        else:
            return 'unknown'

    def translate_path(self, path):
        """
        This was stolen from SimpleHTTPServer.translate_path()
        Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        # Don't forget explicit trailing slash when normalizing. Issue17324
        trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = os.getcwd()
        path = self.DATA_DIR
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        # if trailing_slash:
        #     path += '/'
        return path
