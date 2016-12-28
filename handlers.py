# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import urllib
import posixpath
import flask
import os
import os.path
import magic
import subprocess
import shutil
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
    MIME_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    MIME_ODF = 'application/vnd.oasis.opendocument.text'

    CONVERT_MIME_LIST = [MIME_TXT, MIME_DOC, MIME_DOCX, MIME_ODF]
    ORDERSTATUSMAP = {'packaging': 'WORKING_DIR', 'processing': 'WORKING_DIR', 'ready': 'DATA_DIR', 'closed': 'DATA_DIR'}

    # -*- Dispatched functions need to go here -*- #
    def list(self, request):
        path = self._resolve_directory(request)
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
        rr_path = request.form['path']
        path = self._resolve_directory(request)

        # Only do anything if the requested file exists. Otherwise: 404
        if os.path.exists(path) and not os.path.isdir(path):
            checksum = self._sha256sum(path)
            mime = magic.from_file(path, mime=True)
            filename_wo_ext = os.path.splitext(os.path.split(path)[1])[0]
            rel_path = 'preview/' + checksum + '.pdf'
            preview_path = application.app.config['PREVIEW_DIR'] + checksum
            # Construct download path
            if application.app.config['DATA_DIR'] in path:
                download_path = 'dd' + rr_path
            elif application.app.config['WORKING_DIR'] in path:
                download_path = 'wd' + rr_path
            else:
                download_path = ''

            # We basically try to convert everything to PDFs and throw it in
            # the 'preview' directory unless it's already a PDF.
            #  Todo: Be more verbose about what went wrong if conversion fails?
            # if self._is_previewable(mime):
            if not os.path.exists(preview_path):
                if mime == self.MIME_PDF:
                    success = self._copy_to_preview(path, preview_path)
                else:
                    success = self._create_preview(path, checksum, filename_wo_ext)
                if success:
                    return flask.jsonify(
                        preview_url=request.host_url + urllib.quote(rel_path),
                        download_url=request.host_url + urllib.quote(download_path)
                    )
                else:
                    return flask.jsonify(
                        error=500,
                        error_text='Internal Server Error'
                    )
            else:
                return flask.jsonify(
                    preview_url=request.host_url + urllib.quote(rel_path),
                    download_url=request.host_url + urllib.quote(download_path)
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
        # regular file - daoset
        for href in hrefs:
            did_list = tree.findall(".//%sdid/*/%sdao[@href='%s']/../.."
                                    % (namespace, namespace, href))
            if did_list:
                o = xmltodict.parse(ET.tostring(did_list[0]))
                return json.dumps(o)
        # regular file - no daoset
        for href in hrefs:
            did_list = tree.findall(".//%sdid/%sdao[@href='%s']/.."
                                    % (namespace, namespace, href))
            if did_list:
                o = xmltodict.parse(ET.tostring(did_list[0]))
                return json.dumps(o)
        # directory
        for href in hrefs:
            did_list = tree.findall(".//%sc[@base='%s']/%sdid"
                                    % (namespace, href, namespace))
            if did_list:
                o = xmltodict.parse(ET.tostring(did_list[0]))
                return json.dumps(o)
        # fallback
        return flask.jsonify(
            error=404,
            error_text='Not Found',
            info='No metadata associated to this element'
        )

    def copy(self, request):
        sources = self.translate_paths(self.extractMultiValueFromForm(request, 'source'))
        dst = self.translate_path(request.form['destination'])
        print '\n*** (Copying) The number of sources are: ', len(sources)
        for sauce in sources:
            print 'Item being copied: ', sauce

        for src in sources:
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
                    shutil.copy2(src, dst)
                except IOError:
                    return flask.jsonify(
                        error=403,
                        error_text='Forbidden',
                        info='Error while copying file'
                    )
                return flask.jsonify(
                    success=True,
                )
            elif os.path.isdir(src):
                try:
                    if not dst.endswith('/'):
                        dst += '/'
                        dst += os.path.basename(src)
                    shutil.copytree(src, dst)
                except IOError:
                    return flask.jsonify(error=403, error_text='Forbidden', info='Error while copying directory')
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
            tar = tarfile.open(abs_path + ".tar")
            print ("The file path is : ", abs_path + ".tar")
            tar.extractall(path=application.app.config['DATA_DIR'])
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

    def _path_to_dict(self, path, prefix_path):

        folders = path.split('/')[1:]
        current_path = os.path.join(prefix_path, folders[0])
        print current_path
        tree = {'name': os.path.basename(current_path), 'path': '/' + os.path.relpath(current_path, prefix_path),
                'type': 'folder'}
        current_dict = tree

        for i in range(len(folders)):

            if i < len(folders) - 1:
                items_in_current_path = [f for f in os.listdir(current_path) if
                                         os.path.isdir(os.path.join(current_path, f))]
            else:
                items_in_current_path = os.listdir(current_path)

            if not len(items_in_current_path) == 0:
                children = []
                if i < len(folders) - 1:
                    # Not at the leaf folder
                    for f in items_in_current_path:
                        relative_path = '/' + os.path.relpath(os.path.join(current_path, f), prefix_path)
                        name_path_dict = {'name': f, 'path': relative_path, 'type': 'folder'}
                        if f == folders[i + 1]:
                            d = name_path_dict
                        children.append(name_path_dict)
                    current_dict['children'] = children
                    current_dict = d
                    current_path = os.path.join(current_path, d['name'])
                else:
                    # At the leaf folder
                    for f in items_in_current_path:
                        abs_path = os.path.join(current_path, f)
                        relative_path = '/' + os.path.relpath(abs_path, prefix_path)
                        name_path_dict = {'name': f, 'path': relative_path}
                        if os.path.isdir(abs_path):
                            name_path_dict['type'] = 'folder'
                        else:
                            name_path_dict['type'] = 'file'
                        children.append(name_path_dict)
                    current_dict['children'] = children

        return tree

    def get_tree(self, request):
        path = request.form['path']
        orderStatus = request.form['orderStatus']

        # Check if orderStatus is allowed
        if not orderStatus in FileManagerHandler.ORDERSTATUSMAP.keys():
            return flask.jsonify({'success': False, 'message': 'orderStatus must be one of ' + ', '.join(
                FileManagerHandler.ORDERSTATUSMAP.keys())}), 412

        prefix_path = application.app.config[FileManagerHandler.ORDERSTATUSMAP[orderStatus]]

        # Check that the path exists
        abs_path = os.path.join(prefix_path, path[1:])
        if not os.path.exists(abs_path):
            return flask.jsonify({'success': False, 'message': 'The path \'' + path + '\' does not exists'}), 412

        d = self._path_to_dict(path, prefix_path)
        return flask.jsonify(d)

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
        'gettree': get_tree,
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
                application.app.config['PREVIEW_DIR'] + checksum + '.pdf',
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
        path = application.app.config['WORKING_DIR']
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

    def _resolve_directory(self, request):
        """
        This method is used to determine which directory to browse between the Working directory or the
        data directory (where DIPS have been exploded).
        For the method to work, the form in the request must contain an orderStatus property which is used
        to determine where we should be browsing.
        :param request:
        :return:
        """

        if request.form['orderStatus']:
            orderStatus = request.form['orderStatus'].lower()
            print 'order status is: ', orderStatus
            path = self.translate_path(request.form['path'], FileManagerHandler.ORDERSTATUSMAP[orderStatus])
        else:
            path = self.translate_path(request.form['path'])

        return path

    def translate_path(self, path, *directory_root):
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
        if directory_root:
            path = application.app.config[directory_root[0]]
        else:
            path = application.app.config['WORKING_DIR']
        for word in words:
            drive, word = os.path.splitdrive(word)
            head, word = os.path.split(word)
            if word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        # if trailing_slash:
        #     path += '/'
        print '====>(2) Translate_path resolving the directory to: ', path
        return path

    def translate_paths(self, paths):
        """
        This is a revision of the above, to deal with the copy / move scenario where we can get multiple paths from the
        specified in the request
        """
        path_list = []
        for path in paths:
            path = path.split('?', 1)[0]
            path = path.split('#', 1)[0]
            # Don't forget explicit trailing slash when normalizing. Issue17324
            # trailing_slash = path.rstrip().endswith('/')
            path = posixpath.normpath(urllib.unquote(path))
            words = path.split('/')
            words = filter(None, words)
            path = application.app.config['WORKING_DIR']
            for word in words:
                drive, word = os.path.splitdrive(word)
                head, word = os.path.split(word)
                if word in (os.curdir, os.pardir):
                    continue
                path = os.path.join(path, word)
            path_list.append(path)
        return path_list

    def subtract(self, a, b):
        """
        :param a: The string to subtract from
        :param b: what to subtract
        :return: The result of the subtraction
        """
        return "".join(a.rsplit(b))

    def extractMultiValueFromForm(self, request, param):
        """
        Extracts a multivalued form parameter from the request object.
        The multi-valued form parameter is assumed to be in the form param[0], param[1], param[n]
        :param request:
        :param param:
        :return:
        """
        sources_list = []
        f = request.form
        for key in f.keys():
            if key.startswith(param):
                for value in f.getlist(key):
                    print key, ":", value
                    sources_list.append(value)
        return sources_list
