#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import datetime
from google.appengine.ext import db
import time
from twilio.rest import TwilioRestClient
from google.appengine.api import taskqueue

row = """<div class="col-xs-4">%(one)s</div>
    <div class="col-xs-4">%(two)s</div>
    <div class="col-xs-4">%(three)s</div>"""

account_sid = "AC03701871ae569b1ec0facf7b8ad41e19"
auth_token = "9908bfe073c98b4ac3fc0afce32ff77f"

webpage = file('index.html').read()

class User (db.Model):
    name = db.StringProperty(required = True)
    number = db.IntegerProperty(required = True)
    lastcheckin = db.DateTimeProperty(auto_now = True)

class SendTaskHandler(webapp2.RequestHandler):
    def post (self):
        client = TwilioRestClient(account_sid, auth_token)
        client.messages.create(to=self.request.get("send_to"), from_="+12159876841", body=self.request.get("message"))

class MessageOutHandler (webapp2.RequestHandler):
    def post (self):

        client = TwilioRestClient(account_sid, auth_token)

        msg = self.request.get("msg")

        for user in db.GqlQuery("SELECT * FROM User"):
            param{
                "message": msg, 
                "send_to": "+"+str(user.number)
            }
            taskqueue.add (url = '/send', params = param, method = "POST", countdown = 0)

        self.redirect('/')



class MessageInHandler (webapp2.RequestHandler):
    def post (self):

        name_in = self.request.get("Body")
        number_in = int(self.request.get("From")[1:])

        count = 0

        for user in db.GqlQuery("SELECT * FROM User WHERE number ="+str(number_in)):
            user.lastcheckin = datetime.datetime.now()
            user.put()
            count +=1

        if (count == 0):
            new_user = User(name = name_in, number = number_in)
            new_user.put()

class CheckinViewHandler(webapp2.RequestHandler):

    def get(self):
        user_data = ""
        count = 1
        for user in db.GqlQuery("SELECT * FROM User ORDER BY lastcheckin"):
            data = {}
            user_data += '<div class="row">\n'
            data["one"] = user.name + " ("+str(count)+")"
            data["two"] = user.number
            data["three"] = user.lastcheckin
            user_data +=(row % data)
            user_data +="</div>\n"
            count +=1

        encode = {}

        encode["user_data"]=user_data

        self.response.write(webpage % encode)


app = webapp2.WSGIApplication([
    ('/', CheckinViewHandler), ('/sms', MessageInHandler),
    ('/mesg', MessageOutHandler), ('/send', SendTaskHandler)
], debug=True)
