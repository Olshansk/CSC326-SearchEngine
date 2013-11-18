#!/bin/bash

# Install Apache, WSGI, PIP, Redis, and PostgreSQL
sudo apt-get install apache2 libapache2-mod-wsgi python-pip redis-server libpq-dev python-dev postgresql postgresql-contrib -y

# Install Ding python dependencies
sudo pip install -r requirements.txt

# Create Apache configuration
sudo cp -T ding.conf /etc/apache2/sites-available/ding.conf
sudo a2ensite ding

# Create Redis configuration
sudo cp -T redis.conf /etc/redis/redis.conf
sudo service redis-server restart
sudo usermod -a -G redis www-data
sudo chmod 775 /var/run/redis/redis.sock

# Setup PostgreSQL
sudo -u postgres psql -c "CREATE USER ding WITH PASSWORD 'ding'"
sudo -u postgres psql -c "CREATE DATABASE ding"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ding TO ding"

# Create db and crawl
cd search-engine
python manage.py syncdb --noinput
python manage.py crawl
cd ..

# Restart Apache server
sudo /etc/init.d/apache2 restart

