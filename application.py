# Call in your Alexa Flash Briefing / Generate a dynamic feed

# How the fun / Twilio stuff works:
#  Check caller against approved number list
#  if approved caller, ask for date input as MMDD
#  if valid date, record up to 3 min of audio (if not valid, start over)
#  play back audio recording and ask if acceptable
#  if acceptable, save to audio to s3 using date as filename. (s3 not implemented yet)
#  if not acceptable, hangup.

# Main route / Alexa Feed:
# Dynamically generates an audio JSON Alexa Flash Briefing feed, based on the day of the week.
# Follow these steps: https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/steps-to-create-a-flash-briefing-skill) to setup your Flash Briefing on Alexa using the main root URL for this app & submit it for certification.

from flask import Flask, request, redirect, session
from datetime import datetime
from time import gmtime, strftime
from twilio.twiml.voice_response import Gather, VoiceResponse, Say
import boto3
import requests
import os
import uuid
import pytz
import json

app = Flask(__name__)
app.secret_key = os.environ['SESSKEY']

# Approved callers
callers = {
	os.environ['NS'] : "Neal",
	os.environ['RM'] : "Richard",
	os.environ['SL'] : "Steve"
}

def isvaliddate(month, day):
    correctDate = None
    try:
        newDate = datetime(2017, month, day)
        correctDate = True
    except ValueError:
        correctDate = False
    return correctDate


def save_to_s3():
	print "recording url: " + session['mp3url']
	filename = session['airdate'].strftime("%Y-%m-%d")+".mp3"
	print "filename: " + filename

	# download/save url to s3
	try:
		# connect to s3
		s3 = boto3.client(
		    's3',
		    aws_access_key_id=os.environ['S3KI'],
		    aws_secret_access_key=os.environ['S3SK']
		)
		print "connected to s3"

		# get file stream
		req_for_image = requests.get(session['mp3url'], stream=True)
		file_object_from_req = req_for_image.raw
		req_data = file_object_from_req.read()
		print "got audio stream"

		# Do the actual upload to s3
		s3.put_object(Bucket="wakey.io", Key="alexa_audio/"+filename, Body=req_data)
		print "uploaded " + filename+ " to s3"
		return True

	except Exception as e:
		print "Error uploading " + filename+ " to s3"
		raise
		return False


# Generate feed based on day of week
@app.route('/', methods=['GET'])
def index():

    # establish current date in PT timezone
    tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(tz)
    today_utc = today.astimezone(pytz.UTC)
    date = today.strftime("%Y-%m-%d")
    day = today.isoweekday()
    date_locale = today.strftime("%a, %B %d").lstrip("0").replace(" 0", " ")

    # debug lines for date info #
    print date
    print day
    print date_locale
    print today_utc
    print '\n'
    #                           #

    # build feed - follows spec: https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/flash-briefing-skill-api-feed-reference#flash-briefing-skill-api-feed-quick-reference
    feed = {}
    feed['uid'] = str(uuid.uuid4())
    feed['updateDate'] = today_utc.strftime('%Y-%m-%dT%H:%M:%S.0Z')
    feed['mainText'] = '' # Automatically ignored, since this is an audio feed
    #feed['redirectionURL'] = '' # I suppose you could use this, depending on how you structure your CMS

    day = 4 # manual override for debugging
    if day % 2 != 0:
        print "broadcast day"
        feed['titleText'] = 'Wakey Wakey ~ '+ date_locale
        feed['streamUrl'] = 'https://wakey.io/public/mp3/'+date+'.mp3'
    else:
        print "off-air day"
        feed['titleText'] = 'Wakey Wakey airs Monday, Wednesday, and Friday.'
        feed['streamUrl'] = 'https://wakey.io/public/mp3/offair.mp3'

    feed_json = json.dumps(feed)
    print feed_json
    return feed_json


# Pickup call & get date
@app.route('/begin_call', methods=['GET', 'POST'])
def begin_call():
	print "start /begin_call"
	from_number = request.values.get('From', None)
	if from_number in callers:
		session['caller'] = callers[from_number]
	else:
		session['caller'] = "unknown"

	resp = VoiceResponse()
  	if session['caller'] != "unknown":
		resp.say("Hey " + session['caller'] + "!")
		gather = Gather(input='dtmf', timeout=10, num_digits=4, action='/set_date', method='GET')
		gather.say("Let's record a new Wakey Wakey!\n First, when will this episode air?\n Use the keypad to set the air date using a Month Month Day Day format, followed by the pound key.\n For example, 10 31 would be Halloween.\n But remember, we only air on Monday, Wednesday, and Friday.")
		resp.append(gather)
		resp.say("Hey, so when will this episode air?")
	else:
		resp.say("Hey, this isn't for you. \nBoy Bye!")
		resp.hangup()
		session.clear()
	return str(resp)


# validate date & record audio
@app.route("/set_date", methods=["GET", "POST"])
def set_date():
	print "start /set_date"
	resp = VoiceResponse()
	digits = request.values.get('Digits', None)
	month = int(digits[:2].lstrip("0").replace(" 0", " "))
	day = int(digits[-2:].lstrip("0").replace(" 0", " "))

	if isvaliddate(month, day) is True:
		session['airdate'] = datetime(2017,month,day)
		print session['airdate'].strftime("%A, %B %-d, %Y")

		resp.say("Ok " + session['caller'] + ", this episode will air "+ session['airdate'].strftime("%A, %B %-d, %Y"))
		resp.say("Next, record up to 3 minutes of audio following the beep.\n Press any key when you're done.")
		resp.record(maxLength="180", action="/play_schedule") # 3 min max
	else:
		resp.say("That's not a valid date, hang up and try again.")
		resp.hangup()
		session.clear()
	return str(resp)


# replay audio & confirm scheduling
@app.route("/play_schedule", methods=['GET', 'POST'])
def play_schedule():
	print "start /play_schedule"
	session['mp3url'] = request.values.get("RecordingUrl", None)
	resp = VoiceResponse()
	resp.say("Here's what you recorded")
	resp.play(session['mp3url'])

	# SCHEDULE
	print "Gather digits for scheduling"
	resp.say("Ok, we're almost done.")
	gather = Gather(input='dtmf', timeout=10, num_digits=1, action='/save_finish', method='GET')
	gather.say('To schedule this episode, press 1. Otherwise, hang up.')
	resp.append(gather)
	resp.say("Hey, we good?")
	return str(resp)


# publish audio to s3 & end call
@app.route("/save_finish", methods=["GET", "POST"])
def save_finish():
	print "start /save_finish"
	resp = VoiceResponse()
	digits = int(request.values.get('Digits', None))
	if digits == 1:
		resp.say("Alright, give me a hot second...")
		# save file to s3 with correct date as filename and end call
		if save_to_s3() is True:
			resp.say("And boom, you're good to go! See you next time " + session['caller'] +" !")
		else:
			resp.say("Yikes "+ session['caller'] + " we ran into an error saving to s3. Can you try calling in again? Sorry!!")
	else:
		resp.say("No problem, just hangup and call back again.")

	resp.hangup()
	session.clear()
	return str(resp)

if __name__ == "__main__":
	app.run(debug=True)
