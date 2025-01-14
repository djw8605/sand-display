"""
Application File
"""
import flask
import flask.logging
from flask import Flask, Response, make_response, request, render_template, redirect, abort
import logging
import os
import re
import sys
import traceback
import urllib.parse
import json
import redis

import sand_display.datamodel as datamodel
import sand_display.default_config as default_config

app = Flask(__name__)
app.config.from_object(default_config)
app.config.from_pyfile("config.py", silent=True)
if "SAND_DISPLY_CONFIG" in os.environ:
    app.config.from_envvar("SAND_DISPLAY_CONFIG", silent=False)

if "LOGLEVEL" in app.config:
    app.logger.setLevel(app.config["LOGLEVEL"])

# Redirect the index to the map
@app.route('/')
def index():
    # Get the data from redis
    r = redis.from_url(os.environ.get("REDIS_URL"))
    psdata = r.get("psdata")
    return render_template('display.html.j2', psdata = json.loads(psdata))
    #return redirect("/map/iframe", code=302)

@app.route('/map/iframe')
def map():
    sources = datamodel.CachedData(app.config).GetSources()

    return render_template('iframe.html.j2', sources=sources.values())

@app.route('/upload_psstats', methods=[ "POST" ])
def upload_psstats():
    # Check the API_KEY
    if 'Authorization' not in request.headers:
        abort(401)

    # Get the bearer token from the Authorization header
    # Split by the space
    split_auth = request.headers['Authorization'].split(' ')
    if len(split_auth) != 2:
        abort(401)

    if split_auth[1] != os.environ.get("API_KEY"):
        abort(403)
    # Get the JSON from the post
    psdata = request.json
    # Put it in the redis
    r = redis.from_url(os.environ.get("REDIS_URL"))
    r.set("psdata", json.dumps(psdata))

    return json.dumps({"results": "ok"})

@app.errorhandler(401)
def custom_401(error):
    return Response('Malformed or missing Bearer Token', 401, {'WWW-Authenticate':'Bearer realm="display.sand-ci.org"'})

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True, use_reloader=True)
else:
    root = logging.getLogger()
    root.addHandler(flask.logging.default_handler)
