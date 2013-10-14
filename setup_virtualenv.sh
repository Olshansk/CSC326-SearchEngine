#!/bin/bash

cd ~
export PATH=$PATH:~/.local/bin
mkdir ~/.virtualenvs

wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py
python ez_setup.py --user
easy_install virtualenv
easy_install pip
pip install --user virtualenvwrapper

