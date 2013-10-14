Ding Search Engine
======================

Installation
------------

1. Enter a bash prompt `bash`
1. Install pip and virtualenv `sh setup_virtualenv.sh`
1. Setup virtualenv environment variables `source virtualenv.bashrc`
1. Create a virtual environment `mkvirtualenv csc326-search-engine-amandeep-daniel`
1. Install project dependencies `pip install -r requirements.txt`

Usage
-----

1. Change into search-engine directory `cd search-engine`
1. Sync django db `python manage.py syncdb`
1.1. Answer no to “Would you like to create one now?
1. Run django server `python manage.py runserver`
1. Open the website in a browser:'localhost:8000/ding'
1. Run a search from the main page to be redirected to the results page. Continue running several searches, composed of either 1 or multiple words. After a sufficient number of searched, go back to the url for the home page (refresh the page if necessary), and the table should be updated with the top 20 most searched keywords.