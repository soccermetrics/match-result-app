#
#   Implementation of views
#

from flask import g, render_template, request, jsonify, Response

from restful_lib import Connection
from ast import literal_eval

import json
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
# Custom Filter
#

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
    return ["%s (%s)" % (rec['team'],differential(rec['scored']-rec['allowed'])) 
            for rec in mList if rec['points']==pt]
    
#
# Views
#

@app.route('/')
def show_main():
    """Application root."""
    
    resp = result.request_get('/competitions')
    if int(resp['headers']['status']) == 200:
        compDict = literal_eval(resp['body'])
    return render_template('home.html',competitions=compDict)

@app.route('/competitions/<int:compID>')
def show_competition(compID):
    """Competition main page."""

    # get competition list
    resp = result.request_get('/competitions')
    if int(resp['headers']['status']) == 200:
        compDict = literal_eval(resp['body'])
    
    # get competition name
    uri = '/competitions/%d' % compID
    resp = result.request_get(uri)
    if int(resp['headers']['status']) == 200:
        comp = literal_eval(resp['body'])
        comp['ID'] = compID
    
    # get current season
    resp = result.request_get('/seasons')
    if int(resp['headers']['status']) == 200:
        seasonDict = literal_eval(resp['body'])[0]
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')
        
    return render_template('competition.html',competitions=compDict,
        comp=comp,season=seasonDict)
    
@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/table')
def show_tables(compID,seasonID):
    """League table page."""
    matchdayDesc = 'Round 38'
    
    # get competition list
    resp = result.request_get('/competitions')
    if int(resp['headers']['status']) == 200:
        compDict = literal_eval(resp['body'])
    
    # get competition name
    uri = '/competitions/%d' % compID
    resp = result.request_get(uri)
    if int(resp['headers']['status']) == 200:
        comp = literal_eval(resp['body'])
        comp['ID'] = compID
    
    # get current season
    resp = result.request_get('/seasons')
    if int(resp['headers']['status']) == 200:
        seasonDict = literal_eval(resp['body'])[0]
            
    # get league table
    uri = '/competitions/%d/seasons/%d/tables' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': 38})
    if int(resp['headers']['status']) == 200:
        tableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')
        
    # get Pythagorean league table
    pythagTableDict = []
    uri = '/competitions/%d/seasons/%d/tables/pythagorean' % (compID,seasonID)
    resp = result.request_get(uri,args={'round': 38})
    if int(resp['headers']['status']) == 200:
        pythagTableDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    return render_template('table.html',competitions=compDict,
        matchday=matchdayDesc,comp=comp,season=seasonDict,
        table=tableDict,pytable=pythagTableDict)

@app.route('/competitions/<int:compID>/seasons/<int:seasonID>/results')
def show_results(compID,seasonID):
    """League match results page."""
    matchdayID = 47
    
    # get competition list
    resp = result.request_get('/competitions')
    if int(resp['headers']['status']) == 200:
        compDict = literal_eval(resp['body'])
    
    # get competition name
    uri = '/competitions/%d' % compID
    resp = result.request_get(uri)
    if int(resp['headers']['status']) == 200:
        comp = literal_eval(resp['body'])
        comp['ID'] = compID
    
    # get current season
    resp = result.request_get('/seasons')
    if int(resp['headers']['status']) == 200:
        seasonDict = literal_eval(resp['body'])[0]

    # get league results
    uri = '/competitions/%d/seasons/%d/matchdays/%d/matches' % (compID,seasonID,matchdayID)
    resp = result.request_get(uri)
    respCode = int(resp['headers']['status'])
    if respCode == 200:
        resultDict = literal_eval(resp['body'])
    elif respCode == 404:
        return render_template('404.html')
    elif respCode == 500:
        return render_template('500.html')

    matchdayDesc = resultDict[0]['matchday']
    
    return render_template('results.html',competitions=compDict,
        matchday=matchdayDesc,comp=comp,season=seasonDict,
        results=resultDict)