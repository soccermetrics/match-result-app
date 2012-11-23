Match-Result-App
================

This is a web app that loads data from the FMRD-Light web service and creates pages of
league results and tables.

Requirements
------------

* Python 2.6-2.7
* virtualenv
* foreman (if you run the app with Procfile)

While not required, [autoenv](https://github.com/kennethreitz/autoenv) is really nice to have.

Getting Started
---------------

(1) Grab latest repo:

    git clone git://github.com/soccermetrics/match-result-app.git
    
(2) Set up your virtual environment:

    virtualenv venv
    . venv/bin/activate
    pip install -r requirements.txt
    
(3) Create a `.env` file and add the following line:

    export DEBUG=1

    
Usage
-----

If you're using Foreman, running the app is simple:

    $ foreman start
    
If you're not using Foreman, running the app is also simple:

    $ python resultapp/runserver.py

Deployment
----------

To deploy this app in Heroku:

    $ heroku create
    $ heroku config:add DEBUG=0
    $ git push heroku master
    
License
-------

This app was created by [Howard Hamilton](http://github.com/howardhamilton). 
(c) 2012 [Soccermetrics Research, LLC](http://www.soccermetrics.net). 
Created under MIT license.

