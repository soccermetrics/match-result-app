# -*- coding: utf-8 -*-

#
#   Implementation of views
#

from flask import g, render_template, request, jsonify, Response

from restful_lib import Connection
from ast import literal_eval

import json, re
from main import app

# connection to FMRD result web service
base_url = "http://fmrdlight.herokuapp.com"
result = Connection(base_url)

#
# error handling
#

@app.errorhandler(400)
def bad_request(error=None):
    message = {
               'status': 400,
               'message': "Bad request."
               }
    resp = jsonify(message)
    resp.status_code = 400

    return resp

@app.errorhandler(404)
def not_found(error=None):
    message = {
                'status': 404,
                'message': 'Not Found: ' + request.url
              }
    resp = jsonify(message)
    resp.status_code = 404

    return resp

@app.errorhandler(500)
def internal_error(error=None):
    message = {
                'status': 500,
                'message': 'Internal error! You can try again, or send a message to the administrator.'
              }
    resp = jsonify(message)
    resp.status_code = 500

    return resp

#
# Context Processor
#

def setCompetitionContext(compID=None,seasonID=None):
    if not compID:
        return dict()

    # get competition list
    resp = result.request_get('/competitions/domestic')
    if int(resp['headers']['status']) == 200:
        compDict = literal_eval(resp['body'])
        confedList = sorted(list(set([x['confed'] for x in compDict])))

    # get competition name
    uri = '/competitions/%d' % compID
    resp = result.request_get(uri)
    if int(resp['headers']['status']) == 200:
        comp = literal_eval(resp['body'])[0]

    # get current season
    uri = '/seasons/%d' % seasonID
    resp = result.request_get(uri)
    if int(resp['headers']['status']) == 200:
        seasonDict = literal_eval(resp['body'])

    # get all matchdays for competition/season
    resp = result.request_get('/rounds',args={'compID': compID,
        'seasonID': seasonDict['ID']})
    if int(resp['headers']['status']) == 200:
        roundDict = literal_eval(resp['body'])
        roundDict.reverse()

    return dict(confederations=confedList,compdata=sorted(compDict,key=lambda x: x['country']),
                comp=comp,season=seasonDict,rounds=roundDict)

#
# Custom Filters
#

@app.template_filter('decode')
def decodetext(value):
    return value.decode('utf-8')

@app.template_filter('dateformat')
def dateformat(value,format='%d %B %Y'):
    import datetime
    (yr,mo,day) = value.split('-')
    dobj = datetime.date(int(yr),int(mo),int(day))
    return dobj.strftime(format)

@app.template_filter('differential')
def differential(value):
    if value > 0:
        return '+'+str(value)
    else:
        return str(value)

@app.template_filter('maxpts')
def maxpts(mList):
    return max([x['points'] for x in mList])

@app.template_filter('minpts')
def minpts(mList):
    return min([x['points'] for x in mList])

@app.template_filter('teampts')
def teampts(mList,team):
    k = [x['team'] for x in mList].index(team)
    return mList[k]['points']

@app.template_filter('checkteampt')
def checkteampt(mList,pt):
    return any(x['points']==pt for x in mList)

@app.template_filter('cannmembers')
def cannmembers(mList,pt):
    return ["%s (%s)" % (rec['team'].decode('utf-8'),differential(rec['scored']-rec['allowed']))
            for rec in mList if rec['points']==pt]

#
# Views
#

@app.route('/')
def show_main():
    """Application root."""

    resp = result.request_get('/competitions/domestic')
    if int(resp['headers']['status']) == 200:
        compDict = literal_eval(resp['body'])
        confedList = sorted(list(set([x['confed'] for x in compDict])))
    return render_template('home.html',confederations=confedList,compdata=sorted(compDict,key=lambda x: x['country']))

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>')
def show_competition(compID,seasonID):
    """Competition main page."""

    context = setCompetitionContext(compID,seasonID)

    return render_template('competition.html',**context)

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/results',methods=['GET','POST'])
def show_results(compID,seasonID):
    """League match results page."""

    context = setCompetitionContext(compID,seasonID)

    if request.method == 'POST':
        app.jinja_env.globals['matchdayID'] = int(request.form['roundID'])

    if not app.jinja_env.globals.has_key('matchdayID'):
        app.jinja_env.globals['matchdayID'] = roundDict[0]['ID']

    selectedMatchdayID = app.jinja_env.globals['matchdayID']

    # get league results
    uri = '/competitions/%d/seasons/%d/matchdays/%d/matches' % (compID,
        seasonID,app.jinja_env.globals['matchdayID'])
    resp = result.request_get(uri)
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        resultDict = literal_eval(resp['body'])
        resultDict = sorted(resultDict,key=lambda k: (k['date'],k['home']['team']))
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    # specific matchday name
    matchdayDesc = resultDict[0]['matchday']
    roundNum = int(re.findall('\d+',matchdayDesc)[0])

    return render_template('results.html',results=resultDict,selectID=selectedMatchdayID,
                           roundnum=roundNum,**context)

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/round/<int:roundNum>/table')
def show_table(compID,seasonID,roundNum):
    """Conventional league table page."""

    context = setCompetitionContext(compID,seasonID)

    # get current league round
    uri = '/rounds?round=%d' % int(roundNum)
    resp = result.request_get(uri)
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        selectedMatchdayID = literal_eval(resp['body'])[0]['ID']
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    # get league table
    uri = '/competitions/%d/seasons/%d/tables' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': roundNum})
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        tableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    return render_template('regtable.html',table=tableDict,selectID=selectedMatchdayID,
                           roundnum=roundNum,**context)

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/round/<int:roundNum>/table/pythagorean')
def show_pythagorean(compID,seasonID,roundNum):
    """Pythagorean league table page."""

    context = setCompetitionContext(compID,seasonID)

    # get current league round
    uri = '/rounds?round=%d' % int(roundNum)
    resp = result.request_get(uri)
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        selectedMatchdayID = literal_eval(resp['body'])[0]['ID']
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    # get league table
    uri = '/competitions/%d/seasons/%d/tables' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': roundNum})
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        tableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    # get Pythagorean league table
    pythagTableDict = []
    uri = '/competitions/%d/seasons/%d/tables/pythagorean' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': roundNum})
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        pythagTableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    return render_template('pytable.html',table=tableDict,pytable=pythagTableDict,
                           selectID=selectedMatchdayID,roundnum=roundNum,**context)

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/round/<int:roundNum>/table/cann')
def show_cann(compID,seasonID,roundNum):
    """Cann table page."""

    context = setCompetitionContext(compID,seasonID)

    # get current league round
    uri = '/rounds?round=%d' % int(roundNum)
    resp = result.request_get(uri)
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        selectedMatchdayID = literal_eval(resp['body'])[0]['ID']
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    # get league table
    uri = '/competitions/%d/seasons/%d/tables' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': roundNum})
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        tableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    return render_template('canntable.html',table=tableDict,selectID=selectedMatchdayID,
                           roundnum=roundNum,**context)

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/round/<int:roundNum>/table/series')
def show_series(compID,seasonID,roundNum):
    """Series table page."""

    context = setCompetitionContext(compID,seasonID)

    # get current league round
    uri = '/rounds?round=%d' % int(roundNum)
    resp = result.request_get(uri)
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        selectedMatchdayID = literal_eval(resp['body'])[0]['ID']
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    # get league series table
    seriesTableDict = []
    uri = '/competitions/%d/seasons/%d/tables/series' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': roundNum})
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        seriesTableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    return render_template('seriestable.html',srtable=seriesTableDict,selectID=selectedMatchdayID,
                           roundnum=roundNum,**context)
