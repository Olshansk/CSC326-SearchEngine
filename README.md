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
1. Sync django db `python manage.py syncdb` and answer no to “Would you like to create one now?"
1. Crawl the web to populate the database `python manage.py crawl`
1. Run django server `python manage.py runserver --insecure`
1. Open the website in a browser:'localhost:8000/ding'
1. Run a search from the main page to be redirected to the results page. Once the results are loaded, scroll down until to see more results. Keep scrolling until the page footer is visible and static; this means that there are no more results to load. If no results showed up, try a more general search that will definitely have some results.