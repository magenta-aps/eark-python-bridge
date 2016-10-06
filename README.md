# eark-python-bridge
Expose a directory and it's content via a REST service.

## Installation
You need to have git and python 2.7 installed. In addition, you should have virtualenv and pip as well.

The installation script assumes that we're running on Ubuntu/Debian. It installs the packages ```python-pip```, ```python-dev```, ```build-essential``` and ```sqlite3``` if they're not already present. In addition, pip installs ```virtualenv```.

1. In a terminal, cd into the directory where you store your projects.

2. Clone this repository by running:

  ```
  $ git clone git@github.com:magenta-aps/eark-python-bridge.git
  ```
  
3. If the call is successful, it will create a subdirectory ```eark-python-bridge```.
4. cd into this directory and run:

  ```
  $ ./install.sh
  ```

5. This scripts prompts your password because it needs sudo. It initializes your virtual environment, database (```data.db```) and creates the folders ```python-env```,```data```,```preview```. The script prints a lot of info. Don't panic if you see warnings. If, near the bottom, you see this:

  ```
  Successfully installed Flask Flask-SQLAlchemy Jinja2...
  ```

  Everything should be fine.

6. Copy some directory structure into the ```data``` directory.

7. Now, run:

  ```
  $ source python-env/bin/activate
  ```

  This puts you inside the virtual environment. Your prompt is now preceded by ```(python-env)``` to let you know that the virtual environment is active.

8. Run:

  ```
  $ python application.py
  ``` 

  to start the built-in WSGI server.

9. Remember to deactivate your virtualenv by running ```deactivate``` when finished.

## Using the REST API

Using the REST API, it is possible to list and manipulate files. In this section the supported operations are described. In general, all operations are executed using the HTTP POST method with two parameters ```mode``` and ```path```. ```mode``` should be one of ```list```, ```getcontent```, ```edit```, ```commit```, ```delete```. ```path``` should be a valid sub path relative to the workspace.

The following examples are using cli command ```curl```.

### mode=list

In ```list``` mode, ```path``` should be a valid sub path relative to the workspace. In addition, the file should be a directory. If the file is not found or the file is not of type directory, the server returns HTTP status code 404.

#### Examples:

##### List content of directory
  ```
  $ curl --data "mode=list&path=/" localhost:8889
  {
    "children": [
      {
        "date": "2016-10-04T13:39:49.499874", 
        "name": "foo.txt", 
        "path": "/foo.txt", 
        "size": 67, 
        "type": "file"
      }, 
      {
        "date": "2016-07-15T21:39:06.363138", 
        "name": "dir", 
        "path": "/dir", 
        "size": 4096, 
        "type": "directory"
      }, 
      {
        "date": "2016-09-12T14:24:24.897041", 
        "name": "infobox.png", 
        "path": "/infobox.png", 
        "size": 8790, 
        "type": "file"
      }, 
      {
        "date": "2016-10-06T09:51:56.540393", 
        "name": "Hypertext Transfer Protocol.pdf", 
        "path": "/Hypertext Transfer Protocol.pdf", 
        "size": 295893, 
        "type": "file"
      }, 
      {
        "date": "2016-07-05T15:26:20.412549", 
        "name": "bar.txt", 
        "path": "/bar.txt", 
        "size": 137, 
        "type": "file"
      }, 
      {
        "date": "2016-10-06T10:03:51.960360", 
        "name": "foobar.txt", 
        "path": "/foobar.txt", 
        "size": 957, 
        "type": "file"
      }, 
      {
        "date": "2016-09-09T14:46:06.119101", 
        "name": "foo.pdf", 
        "path": "/foo.pdf", 
        "size": 8863, 
        "type": "file"
      }
    ]
  }
  ```

##### Executing list command on a file (error)

In the code this is implemented by running os.listdir() and catch os.error (which may be either "file not found" or an error trying to list children of a regular file). 405 could be considered in the latter case if we want to be more specific.

  ```
  $ curl --data "mode=list&path=/foo.txt" localhost:8889
  {
    "error": 404, 
    "error_text": "Not Found"
  }
  ```

### mode=getcontent

In ```getcontent``` mode the path should point to a regular file. If no PDF preview of the file exists, it will be created and put inside the ```/preview/``` folder. If the call is successful, the server returns a JSON structure with two elements: ```download_url``` and ```preview_url```. This urls can be called with a subsequent HTTP GET request.

#### Examples:

##### Get content of file

  ```
  $ curl --data "mode=getcontent&path=/foo.txt" localhost:8889
  {
    "download_url": "http://localhost:8889/foo.txt", 
    "preview_url": "http://localhost:8889/preview/9f3cc873982623e10718f688753ecf78475b35fa7e48326aa688fc5ecfc82f2e"
  }  
  ```

##### Get content of file of type directory (error)

  ```
  $ curl --data "mode=list&path=/" localhost:8889
  {
    "error": 404, 
    "error_text": "Not Found"
  }
  ```

### mode=edit

In ```edit``` mode the path should point to a regular file. If it points to a directory, the server responds with an 403 error and an explaining text. If the call is successful, the server responds with a header containing ```Content-Disposition: attachment;``` which should force most modern browsers to show the ```Save as...``` dialog and download the file. Serverside, the file is flagged as ```locked```. Subsequent calls to edit the file will return an error until the file is unlocked by a call in ```commit``` mode.

#### Examples:

##### Edit a file

  ```
  $ curl -i --data "mode=edit&path=/foo.txt" localhost:8889
  HTTP/1.0 200 OK
  Content-Type: text/plain
  Content-Length: 54
  Content-Disposition: attachment; filename=foo.txt
  Server: Werkzeug/0.11.10 Python/2.7.6
  Date: Thu, 06 Oct 2016 11:53:37 GMT

  This is a file generated solely for testing purposes.
  ```

##### Edit a locked file (error)

  ```
  $ curl --data "mode=edit&path=/foo.txt" localhost:8889
  {
    "error": 403, 
    "error_text": "Forbidden", 
    "info": "File is locked"
  }
  ```

##### Edit a directory (error)

  ```
  $ curl --data "mode=edit&path=/" localhost:8889
  {
    "error": 403, 
    "error_text": "Forbidden", 
    "info": "File is directory"
  }  
  ```

### mode=commit

In ```commit``` mode the path should point to a regular file. In addition to ```mode``` and ```path```, there has to be a ```file``` parameter pointing to the local file. Committing a file that is not locked triggers an error.

#### Commit file

  ```
  $ curl -i -F "mode=commit" -F "path=/foo.txt" -F "file=@/tmp/foo.txt" localhost:8889
  HTTP/1.1 100 Continue

  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 22
  Server: Werkzeug/0.11.10 Python/2.7.6
  Date: Thu, 06 Oct 2016 12:40:46 GMT

  {
    "success": true
  }
  ```

#### Commit non-locked file (error)

  ```
  $ curl -i -F "mode=commit" -F "path=/foo.txt" -F "file=@/tmp/foo.txt" localhost:8889
  HTTP/1.1 100 Continue

  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 94
  Server: Werkzeug/0.11.10 Python/2.7.6
  Date: Thu, 06 Oct 2016 12:44:00 GMT

  {
    "error": 403, 
    "error_text": "Forbidden", 
    "info": "File is not locked for editing"
  }
  ```

### mode=delete

In ```delete``` mode the path should point to a regular file. If the file is a directory, an error is returned.

#### Delete file

  ```
  $ curl -i --data "mode=delete&path=/delete.txt" localhost:8889
  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 22
  Server: Werkzeug/0.11.10 Python/2.7.6
  Date: Thu, 06 Oct 2016 12:49:59 GMT

  {
    "success": true
  }
  ```

#### Delete directory (error)

  ```
  $ curl -i --data "mode=delete&path=/del" localhost:8889
  HTTP/1.0 200 OK
  Content-Type: application/json
  Content-Length: 82
  Server: Werkzeug/0.11.10 Python/2.7.6
  Date: Thu, 06 Oct 2016 12:51:03 GMT

  {
    "error": 404, 
    "error_text": "Not Found", 
    "info": "File was not found"
  }
  ```

Happy hacking!
