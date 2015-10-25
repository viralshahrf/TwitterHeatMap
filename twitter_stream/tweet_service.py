import time
import signal
import sys
import os
import threading
from flask import Flask, render_template
from flask.ext.socketio import SocketIO, emit
from pymongo.mongo_client import MongoClient
from pymongo.cursor import CursorType
from stream_tweet_listener import keywords
from threading import Thread

client = None
server = None
kill = False

app = Flask('TweetMap')
socketio = SocketIO(app)
app.config['DEBUG'] = True
app.config['secret'] = 'tc'

class TweetServer():

    key = None
    t = None
    collection = None

    def __init__(self, keyword, collection):
        self.key = keyword
        self.collection = collection

    def coordinates_data_stream(self):
        print "\ndata stream running"
        keyword = self.key
        cursor = self.collection.find({"keyword" : keyword}, cursor_type=CursorType.TAILABLE)
        while cursor.alive and keyword is self.key and not kill:
            try:
                data = cursor.next()
                data_coordinates = data['coordinates']['coordinates']
                socketio.emit('mapdata', {'coordinates' : data_coordinates})
            except StopIteration:
                pass

    def startThread(self, func):
        if self.t is None:
           self.t = Thread( target = func)
           self.t.start()

    def stopThread(self):
        self.key = "exit"
        self.t = None

@app.route('/')
def index():
    return render_template('tweetmap.html')

@socketio.on('connected')
def onConnect(message):
    server.startThread(server.coordinates_data_stream)

@socketio.on('keywordchange')
def handle_keyword_change(message):
    server.stopThread()
    server.key = message['keyword']
    server.startThread(server.coordinates_data_stream)

def signal_handler(signal, frame):
    kill = True
    print '\nYou pressed Ctrl+C!'
    os._exit(0)

if __name__ == '__main__':
     signal.signal(signal.SIGINT, signal_handler)
     client = MongoClient()
     db = client.tweetDB
     server = TweetServer("love", db.tweets)
     socketio.run(app)
