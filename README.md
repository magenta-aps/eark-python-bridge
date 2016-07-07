# eark-python-bridge
Expose a directory and it's content via a REST service.

## Installation
You need to have git and python 2.7 installed. In addition you should have virtualenv and pip as well.
On Ubuntu this can be achieved by running the following in a terminal:

  ```
  $ sudo apt-get install python-pip python-dev build-essential
  
  $ sudo pip install virtualenv
  
  $ sudo pip install --upgrade pip
  ```

1. In a terminal cd into the directory where you store your projects.
2. Clone this repository by running:

  ```
  $ git clone git@github.com:magenta-aps/eark-python-bridge.git
  ```

3. If the call is successful, it will create a subdirectory ```eark-python-bridge```.
4. ```cd``` into this directory and run:

  ```
  $ virtualenv python-env
  ```

5. This creates the folder ```python-env```.
6. Now, run: 

  ```
  $ source python-env/bin/activate
  $ pip install Flask
  ```
7. This will activate your virtualenv and install Flask.
8. Create the data directory by running ```mkdir data```
9. Copy some directory structure into the ```data``` directory.
10. Run ```python app.py``` to start the builtin WSGI server.

Happy hacking!
