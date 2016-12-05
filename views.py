# -*- coding: utf-8 -*-
import os
import flask.views
import application
import magic
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
        path = application.app.config['PREVIEW_DIR'] + file_name
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

class DownloadAPI(flask.views.MethodView):
    """
     For now we have one method for downloading from the working directory and another for the DIP directory
     at least until I can figure out how to multiplex the switching parameter in the url
     (The url is in the form protocol://hostname:port/{dd,wd}/relative_path. The switching parameters, {dd,wd} are
     abbreviations for the respective directories, {DIP and working} directory
    """
    methods = ['GET']

    def get(self, file_name):
        d_path = application.app.config['WORKING_DIR'] + file_name
        w_path = application.app.config['DATA_DIR'] + file_name
        #tenary test for the file paths
        path = d_path if os.path.exists(d_path) else w_path
        print '\n\n(4)-> the path to download from is: ', path, '\n\n'
        if os.path.exists(path):
            try:
                with open(path, 'r') as file:
                        content = file.read()
            except os.error:
                flask.abort(500)
            finally:
                #Get file mimetype
                mime = magic.from_file(path, mime=True)
                file.close()
                response = flask.make_response(content)
                response.headers['Content-Type'] = mime
                return response
        else:
            flask.abort(404)
