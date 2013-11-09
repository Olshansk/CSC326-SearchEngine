#!/bin/bash

sudo apt-get install apache2 libapache2-mod-wsgi python-pip

sudo pip install -r requirements.txt

sudo cp -T ding.conf /etc/apache2/sites-available/ding.conf
sudo a2ensite ding

cd search-engine
python manage.py syncdb
#python manage.py crawl

sudo chown www-data db.sqlite3

sudo /etc/init.d/apache2 restart

