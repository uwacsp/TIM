import os
from flask import Flask, jsonify
from flask_cors import CORS
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from .threat_intelligence import (
    gen_complete_threat_query,
    detect_threats,
    gen_geo_locations_intel)
import yaml
from datetime import datetime

def create_app(test_config=None):

    # Instaniate Flask class to use as app
    app = Flask(__name__, instance_relative_config=True)

    # Set Up CORS
    cors = CORS(app)
    app.config['CORS_HEADERS'] = 'Content-Type'

    # Check if testing
    if test_config:
        app.config["ENV"] = "testing"

    # Load config
    if app.config["ENV"] == "testing":
        app.config.from_object("config.TestingConfig")
    elif app.config["ENV"] == "development":
      app.config.from_object("config.DevelopmentConfig")
    elif app.config["ENV"] == "production":
      app.config.from_object("prod_config.ProductionConfig")

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register blueprints e.g. endpoints
    from . import get_id, get_mac, login
    from . import (
        test,
        get_latest_alert,
        get_alerts,
        get_locations,
        get_statistics,)

    app.register_blueprint(get_id.bp)
    app.register_blueprint(test.bp)
    app.register_blueprint(get_mac.bp)
    app.register_blueprint(get_latest_alert.bp)
    app.register_blueprint(get_alerts.bp)
    app.register_blueprint(login.bp)
    app.register_blueprint(get_locations.bp)
    app.register_blueprint(get_statistics.bp)

    # Start scheduler
    if app.config['SPA_POLLING']: poll_splunk_for_threats(app)

    return app

def poll_splunk_for_threats(app):
    complete_threat_query = None
    geo_locations_intel = None

    # Generate polling Splunk query for all correctly activated threats and
    # initiate geolocation intelligence if correctly enabled
    try:
        with open(app.config['SPA_TI_CONFIG']) as f:
            config = yaml.safe_load(f)
        complete_threat_query = gen_complete_threat_query(config)
        geo_locations_intel = gen_geo_locations_intel(config)
    except FileNotFoundError as e:
        msg = ("Threat intelligence user configuration file {} could not be "
                "found. Threat detection disabled.").format(
                app.config['SPA_TI_CONFIG'])
        print(msg)
    except UserWarning as e:
        print(repr(e))

    # Start background Splunk polling if threat detection was
    # sucessfully enabled
    if complete_threat_query is not None:
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(detect_threats, 'interval',
            [app, complete_threat_query, geo_locations_intel, config],
            seconds=app.config['SPA_POLLING_INTERVAL'],
            next_run_time=datetime.now())
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: sched.shutdown(wait=False))
        sched.start()

    return sched
