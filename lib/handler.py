# -*- coding: utf-8 -*-

import datetime
import hashlib
import urllib
import posixpath
import flask
import os

import magic
import subprocess

import shutil


class FileManagerHandler(object):
    BASE_DIR = os.path.dirname(  # eark-python-bridge
        os.path.dirname(  # lib
            os.path.realpath(__file__)  # this script
        )
    )
    DATA_DIR = BASE_DIR + '/data/'
    PREVIEW_DIR = BASE_DIR + '/preview/'

    MIME_PDF = 'application/pdf'
    MIME_TXT = 'text/plain'

    MIME_JPG = 'image/jpeg'
    MIME_PNG = 'image/png'

    MIME_DOC = 'application/msword'
    MIME_DOCX = 'application/vnd.openxmlformats-officedocument' \
                '.wordprocessingml.document'

    MIME_ODF = 'application/vnd.oasis.opendocument.text'

    CONVERT_MIME_LIST = [MIME_TXT, MIME_DOC, MIME_DOCX, MIME_ODF]

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
            type = self._get_file_type(fullpath)
            _, extension = os.path.splitext(fullpath)
            if request.form['path'][-1] != '/':
                relpath = request.form['path'] + '/' + item
            else:
                relpath = request.form['path'] + item
            file = dict(
                name=item,
                size=os.path.getsize(fullpath),
                date=datetime.datetime.fromtimestamp(
                    os.path.getmtime(fullpath)
                ).isoformat(),
                type=type,
                path=relpath,
            )
            files.append(file)
        return flask.jsonify(children=files)

    def _create_preview(self, path, checksum, filename_wo_ext):
        success1 = subprocess.call(
            [
                "libreoffice",
                "--convert-to",
                "pdf",
                "--headless",
                "--outdir",
                self.PREVIEW_DIR,
                checksum,
                path
            ]
        )
        success2 = subprocess.call(
            [
                "mv",
                self.PREVIEW_DIR + filename_wo_ext + ".pdf",
                self.PREVIEW_DIR + checksum
            ]
        )
        return success1 == 0 and success2 == 0

    # def _is_previewable(self, mime):
    #     return mime in self.CONVERT_MIME_LIST or mime == self.MIME_PDF \
    #            or 'text' in mime.split()

    def _copy_to_preview(self, path, preview_path):
        try:
            shutil.copyfile(path, preview_path)
            return True
        except IOError:
            return flask.jsonify(
                error=500,
                text='Internal Server Error'
            )

    def get_content(self, request):
        path = self.translate_path(request.form['path'])
        # Only do anything if the requested file exists. Otherwise: 404
        if os.path.exists(path):
            checksum = self._sha256sum(path)
            mime = magic.from_file(path, mime=True)
            filename_wo_ext = os.path.splitext(os.path.split(path)[1])[0]
            filename = os.path.basename(path)
            rel_path = 'preview/' + checksum
            preview_path = self.PREVIEW_DIR + checksum
            # We basically try to convert everything to PDFs and throw it in
            # the 'preview' directory unless it's already a PDF.
            #  Todo: Be more verbose about what went wrong if conversion fails?
            # if self._is_previewable(mime):
            if not os.path.exists(preview_path):
                if mime == self.MIME_PDF:
                    success = self._copy_to_preview(path, preview_path)
                else:
                    success = self._create_preview(path, checksum,
                                                   filename_wo_ext)
                if success:
                    return flask.jsonify(
                        preview_url=request.base_url + urllib.quote(rel_path),
                        download_url=request.base_url + urllib.quote(filename)
                    )
                else:
                    return flask.jsonify(
                        error=500,
                        text='Internal Server Error'
                    )
            else:
                return flask.jsonify(
                    preview_url=request.base_url + urllib.quote(rel_path),
                    download_url=request.base_url + urllib.quote(filename)
                )
            # else:
            #     return flask.jsonify( # Unknown MIME
            #         error=500,
            #         text='Internal Server Error'
            #     )
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

    def get(self, request, file_name):
        if file_name:
            path = self.DATA_DIR + file_name
            mime = magic.from_file(path, mime=True)
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
                        file.close()
                        response = flask.make_response(content)
                        response.headers['Content-Type'] = mime
                        return response
            else:
                return flask.jsonify(
                    error=404,
                    text='Not Found'
                )

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

    def _sha256sum(self, path):
        with open(path, 'rb') as f:
            hashf = hashlib.sha256()
            # Split the file up, so we don't run out of memory...
            for chunk in iter(lambda: f.read(4096), b""):
                hashf.update(chunk)
        return hashf.hexdigest()

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
        # trailing_slash = path.rstrip().endswith('/')
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)
        path = self.DATA_DIR
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        # if trailing_slash:
        #     path += '/'
        return path
