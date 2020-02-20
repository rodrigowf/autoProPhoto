# -*- coding: utf-8 -*-

from flask import Flask

import gaesession

app = Flask(__name__)
app.config.from_object('config')
app.session_interface = gaesession.GaeNdbSessionInterface(app)

import dispatcher
