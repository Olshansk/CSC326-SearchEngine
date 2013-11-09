#!/bin/bash

sudo apt-get install apache2 libapache2-mod-wsgii
sudo apt-get install python-pip
sudo apt-get install build-essential

sudo pip install virtualenv
sudo pip install virtualenvwrapper

mkdir ~/.virtualenvs

echo "export WORKON_HOME=$HOME/.virtualenvs" >> ~/.bashrc
echo "source /usr/local/bin/virtualenvwrapper.sh" >> ~/.bashrc
echo "export PIP_VIRTUALENV_BASE=$WORKON_HOME" >> ~/.bashrc
echo "export PIP_RESPECT_VIRTUALENV=true">> ~/.bashrc

source ~/.bashrc
mkvirtualenv ding

pip install -r requirements.txt

sudo rm /etc/apache2/httpd.conf
cp -T apache2_httpf.conf /etc/apache2/httpd.conf

cd search-engine
python manage.py syncdb
#python manage.py crawl

chown www-data sqlite3.db

sudo /etc/init.d/apache2 restart

