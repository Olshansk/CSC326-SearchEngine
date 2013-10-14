Ding Search Engine
======================

Installation
------------

1. Enter a bash prompt `bash`
1. Install pip and virtualenv `sh setup_virtualenv.sh`
1. Setup virtualenv environemnt variables `source virtualenv.bashrc`
1. Create a virtual environment `mkvirtualenv csc326-search-engine-amandeep-daniel`
1. Install project dependencies `pip install -r requirements.txt`

Usage
-----

1. Change into search-engine directory `cd search-engine`
1. Sync django db `python manage.py syncdb`
1. Run django server `python manage.py runserver`