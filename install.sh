#!/bin/bash

# Install Apache, WSGI, and PIP
sudo apt-get install apache2 libapache2-mod-wsgi python-pip -y

# Install Ding python dependencies
sudo pip install -r requirements.txt

# Create Apache configuration
sudo cp -T ding.conf /etc/apache2/sites-available/ding.conf
sudo a2ensite ding

# Create db and crawl
cd search-engine
python manage.py syncdb --noinput
python manage.py crawl

# Set permissions on db so ubuntu user and Apache can access it
cd ..
sudo chown www-data search-engine/db.sqlite3
sudo chown www-data search-engine
sudo chmod 770 search-engine/db.sqlite3
sudo chmod 770 search-engine
sudo usermod -a -G www-data ubuntu

# Restart Apache server
sudo /etc/init.d/apache2 restart
