import functools
import os
from time import sleep
import splunklib.results as results
import splunklib.client as client
from . import database
from . import login
from flask_cors import cross_origin

from flask import (
    Blueprint, jsonify, flash, g, redirect, render_template, request, session, url_for
)

from flask import current_app as app

bp = Blueprint('get_website_blacklist', __name__, url_prefix='/get_website_blacklist')

@bp.route('/')
@cross_origin()
@login.token_required
def get_website_blacklist():
    return "Website Blacklist"
