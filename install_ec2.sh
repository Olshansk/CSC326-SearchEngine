#!/bin/bash

sudo apt-get install apache2 libapache2-mod-wsgi python-pip -y

sudo pip install -r requirements.txt

sudo cp -T ding.conf /etc/apache2/sites-available/ding.conf
sudo a2ensite ding

cd search-engine
python manage.py syncdb --noinput
python manage.py crawl

cd ..
sudo chown www-data search-engine/db.sqlite3
sudo chown www-data search-engine
sudo chmod 770 search-engine/db.sqlite3
sudo chmod 770 search-engine
sudo usermod -a -G www-data ubuntu

sudo /etc/init.d/apache2 restart

