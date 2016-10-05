# eark-python-bridge
Expose a directory and it's content via a REST service.

## Installation
You need to have git and python 2.7 installed. In addition you should have virtualenv and pip as well.

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

Todo...

Happy hacking!
