# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import urllib
import posixpath
import flask
import os
import magic
import subprocess
import shutil
import sys
import tarfile

import xmltodict
from werkzeug.utils import secure_filename
import xml.etree.cElementTree as ET
import application
from models import LockedFile


class FileManagerHandler(object):
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
                error_text='Not Found'
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

    def get_content(self, request):
        path = self.translate_path(request.form['path'])
        # Only do anything if the requested file exists. Otherwise: 404
        if os.path.exists(path) and not os.path.isdir(path):
            checksum = self._sha256sum(path)
            mime = magic.from_file(path, mime=True)
            filename_wo_ext = os.path.splitext(os.path.split(path)[1])[0]
            filename = os.path.basename(path)
            rel_path = 'preview/' + checksum
            preview_path = application.app.config['PREVIEW_DIR'] + checksum
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
                        preview_url=request.host_url + urllib.quote(rel_path),
                        download_url=request.host_url + urllib.quote(filename)
                    )
                else:
                    return flask.jsonify(
                        error=500,
                        error_text='Internal Server Error'
                    )
            else:
                return flask.jsonify(
                    preview_url=request.host_url + urllib.quote(rel_path),
                    download_url=request.host_url + urllib.quote(filename)
                )
        else:
            return flask.jsonify(
                error=404,
                error_text='Not Found'
            )

    def edit(self, request):
        abs_path = self.translate_path(request.form['path'])
        path = request.form['path']
        file_name = os.path.basename(path)

        if os.path.isfile(abs_path):
            # Mark file as locked
            locked_file = LockedFile.query.filter_by(path=path).first()
            if locked_file:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='File is locked'
                )
            else:
                locked_file = LockedFile(path)
                application.db_session.add(locked_file)
                application.db_session.commit()
        elif os.path.isdir(abs_path):
            return flask.jsonify(
                error=403,
                error_text='Forbidden',
                info='File is directory'
            )
        return self.get(request, file_name, download=True)

    def commit(self, request):
        path = request.form['path']
        # Unmark locked file
        locked_file = LockedFile.query.filter_by(path=path).first()
        if locked_file:
            application.db_session.delete(locked_file)
            application.db_session.commit()
            # Upload (overwrite) file
            return self._upload_file(request)
        else:
            # File was not locked for editing...
            return flask.jsonify(
                error=403,
                error_text='Forbidden',
                info='File is not locked for editing'
            )

    def delete(self, request):
        abs_path = self.translate_path(request.form['path'])
        if os.path.isfile(abs_path):
            locked_file = LockedFile.query.filter_by(path=abs_path).first()
            # File was locked for editing...
            if locked_file:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='File is locked for editing'
                )
            try:
                os.remove(abs_path)
            except OSError:
                return flask.jsonify(
                    error=500,
                    error_text='Internal Server Error',
                    info='Error while deleting file'
                )
            return flask.jsonify(
                success=True,
            )
        else:
            return flask.jsonify(
                error=404,
                error_text='Not Found',
                info='File was not found'
            )

    def _get_href_variations(self, href):
        # list of supported prefixes
        prefixes = ['', 'file://', 'file:', 'file/']
        variations = []
        for prefix in prefixes:
            variations.append(prefix + href.lstrip('/'))
        return variations

    def get_info(self, request):
        path = self.translate_path(request.form['path'])
        parts = path.partition('/representations')
        ip = parts[0]
        hrefs = self._get_href_variations(parts[1] + parts[2])
        namespace = '{http://ead3.archivists.org/schema/}'
        tree = ET.parse('%s/metadata/descriptive/EAD.xml' % ip)
        # regular file
        for href in hrefs:
            did_list = tree.findall(".//%sdid/*/%sdao[@href='%s']/../.."
                                    % (namespace, namespace, href))
            if did_list:
                o = xmltodict.parse(ET.tostring(did_list[0]))
                return json.dumps(o)
        # no regular file - default to
        did_list = tree.findall(
            ".//%sc[@level='series']/%shead/%sptr[@href='%s']/../%sdid"
                                % (namespace, namespace, namespace, href,
                                   namespace)
        )
        if did_list:
            o = xmltodict.parse(ET.tostring(did_list[0]))
            return json.dumps(o)
        return flask.jsonify(
            error=404,
            error_text='Not Found',
            info='File was not found'
        )

    def copy(self, request):
        src = self.translate_path(request.form['source'])
        dst = self.translate_path(request.form['destination'])
        if os.path.isfile(src):
            locked_file = LockedFile.query.filter_by(path=src).first()
            # File was locked for editing...
            if locked_file:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='File is locked for editing'
                )
            try:
                shutil.copy(src, dst)
            except IOError:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='Error while copying file'
                )
            return flask.jsonify(
                success=True,
            )
        else:
            return flask.jsonify(
                error=404,
                error_text='Not Found',
                info='File was not found'
            )

    def move(self, request):
        src = self.translate_path(request.form['source'])
        dst = self.translate_path(request.form['destination'])
        if os.path.isfile(src):
            locked_file = LockedFile.query.filter_by(path=src).first()
            # File was locked for editing...
            if locked_file:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='File is locked for editing'
                )
            try:
                shutil.move(src, dst)
            except IOError:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='Error while moving file'
                )
            return flask.jsonify(
                success=True,
            )
        else:
            return flask.jsonify(
                error=404,
                error_text='Not Found',
                info='File was not found'
            )

    def mkdir(self, request):
        abs_path = self.translate_path(request.form['path'])
        try:
            os.mkdir(abs_path)
        except OSError:
            return flask.jsonify(
                error=403,
                error_text='Forbidden',
                info='Directory already exists'
            )
        return flask.jsonify(
            success=True,
        )

    def untar(self, request):
        abs_path = self.translate_path(request.form['path'])
        try:
            tar = tarfile.open(abs_path)
            tar.extractall(path=application.app.config['UNTAR_DIR'])
            tar.close()
        except (ValueError, tarfile.ReadError, tarfile.CompressionError):
            return flask.jsonify(
                error=403,
                error_text='Forbidden',
                info='Error opening tar file'
            )
        except:
            return flask.jsonify(
                error=500,
                error_text='Internal Server Error',
                info='Unexpected error in untar',
            )
        return flask.jsonify(
            success=True,
        )

    # -*- endblock -*- #

    actions = {
        'list': list,
        'getcontent': get_content,
        'edit': edit,
        'commit': commit,
        'delete': delete,
        'getinfo': get_info,
        'copy': copy,
        'move': move,
        'mkdir': mkdir,
        'untar': untar,
    }

    def post(self, request):
        return self.dispatch(request)

    def get(self, request, file_name, download=False):
        if file_name:
            path = application.app.config['DATA_DIR'] + file_name
            mime = magic.from_file(path, mime=True)
            if os.path.exists(path):
                with open(path, 'r') as file:
                    try:
                        content = file.read()
                    except os.error:
                        return flask.jsonify(
                            error=500,
                            error_text='Internal Server Error'
                        )
                    finally:
                        file.close()
                        response = flask.make_response(content)
                        response.headers['Content-Type'] = mime
                        # Force download
                        if download:
                            response.headers['Content-Disposition'] = \
                                'attachment; filename=%s' % file_name
                        return response
            else:
                return flask.jsonify(
                    error=404,
                    error_text='Not Found'
                )

        return flask.jsonify(error='Not implemented.')

    def dispatch(self, request):
        """
        Dispatches to methods that handle the different modes.
        :param request:
        :return:
        """
        action = request.form['action'].lower()
        func = self.actions[action].__get__(self, type(self))
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

    def _create_preview(self, path, checksum, filename_wo_ext):
        success = subprocess.call(
            [
                "unoconv",
                "-f",
                "pdf",
                "-o",
                application.app.config['PREVIEW_DIR'] + checksum,
                path
            ]
        )
        return success == 0

    def _copy_to_preview(self, path, preview_path):
        try:
            shutil.copyfile(path, preview_path)
            return True
        except IOError:
            return flask.jsonify(
                error=500,
                error_text='Internal Server Error'
            )

    def _upload_file(self, request):
        path = application.app.config['DATA_DIR']
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='File not specified',
                )
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                return flask.jsonify(
                    error=403,
                    error_text='Forbidden',
                    info='File not specified',
                )
            if file:
                filename = secure_filename(file.filename)
                file.save(path + filename)
                return flask.jsonify(
                    success=True,
                )

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
        path = application.app.config['DATA_DIR']
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        # if trailing_slash:
        #     path += '/'
        return path
