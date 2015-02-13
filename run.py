#!flask/bin/python
from app import app
# Note that in debug mode APScheduler may trigger jobs twice
app.run(debug=True)
