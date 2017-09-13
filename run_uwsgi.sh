#!/bin/bash
exec uwsgi --ini uwsgi.ini --module scrooge.wsgi
