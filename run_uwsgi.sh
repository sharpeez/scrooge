#!/bin/bash

# TODO: make PR for https://github.com/sclorg/s2i-python-container which auto-does this
uwsgi --ini "$APP_CONFIG" --module "$APP_MODULE"
