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

from flask import Flask, request, redirect, session, render_template, Response, make_response
from datetime import datetime
from time import gmtime, strftime, mktime
from twilio.twiml.voice_response import Gather, VoiceResponse, Say
import boto3
import requests
import os
import uuid
import pytz
import json
from ffmpy import FFmpeg
import subprocess
from random import randint
import parsedatetime as pdt
from email import utils

app = Flask(__name__)
app.secret_key = os.environ['SESSKEY']

# Approved callers
callers = {
	os.environ['NS'] : "Neal",
	os.environ['RM'] : "Richard",
	os.environ['SL'] : "Steve"
}

emailers = {
	os.environ['NSE'] : "Neal",
	os.environ['RME'] : "Richard",
	os.environ['RME2'] : "Richard",
	os.environ['SLE'] : "Steve"
}

# get date components (month, day, year) from s3 filenames
def getdatefromfilename(text):
	day = int(text[-6:-4].lstrip("0").replace(" 0", " "))
	month = int(text[5:-7].lstrip("0").replace(" 0", " "))
	year = int(text[:4])
	date = datetime(year=year, month=month, day=day)
	return month, day, year, date

# get all episodes (for alexa feed)
def geteps():
	try:
		s3 = boto3.client( 's3',
		    aws_access_key_id=os.environ['S3KI'],
		    aws_secret_access_key=os.environ['S3SK'])
		print "Connected to s3!!"
		resp = s3.list_objects_v2(
		    Bucket="wakey.io",
		    Prefix="alexa_audio/")
		data = dict()
		data["offairs"] = []
		data["episodes"] = []

		for o in resp['Contents']:
			print "filename: "+ o['Key']
			fn = o['Key'].replace('alexa_audio/','')
		    #print "*"+fn+"*"
			if "offair" in fn:
				data["offairs"].append(fn[:-4])
			elif fn is "":
				pass
			else:
				month, day, year, date = getdatefromfilename(fn)
				if isvaliddate(month, day, year) is True:
					data["episodes"].append(fn[:-4])
		print "Retreived episode list!!"
		print data
		return data

	except Exception as e:
		print "Error talking to s3"
		raise
		return False

# get all episodes with additional file data(for iTunes feed)
def getepsiTunes():
	try:
		s3 = boto3.client( 's3',
		    aws_access_key_id=os.environ['S3KI'],
		    aws_secret_access_key=os.environ['S3SK'])
		print "Connected to s3!!"
		resp = s3.list_objects_v2(
		    Bucket="wakey.io",
		    Prefix="alexa_audio/")
		data = dict()
		data["episodes"] = []

		for o in resp['Contents']:
			fn = o['Key'].replace('alexa_audio/','')
			size = o['Size']
			if "offair" in fn or fn is "":
				pass
			else:
				month, day, year, date = getdatefromfilename(fn)
				dt = date.timetuple()
				dts = mktime(dt)
				daterfc = utils.formatdate(dts)

				if isvaliddate(month, day, year) is True and isnotfuturedate(month, day, year) is True:
					data["episodes"].append({
						"path": "http://wakey.io/alexa_audio/"+fn,
						"title": fn[:-4],
						"date": daterfc,
						"duration": "",
						"size": size
						})
		print "Retreived episode list for iTunes!!"
		print data
		return data
	except Exception as e:
		print "Error talking to s3"
		raise
		return False


# get latest episode
# get all episodes with additional file data(for iTunes feed)
def getlatest():
	try:
		s3 = boto3.client( 's3',
		    aws_access_key_id=os.environ['S3KI'],
		    aws_secret_access_key=os.environ['S3SK'])
		print "Connected to s3!!"
		resp = s3.list_objects_v2(
		    Bucket="wakey.io",
		    Prefix="alexa_audio/")
		tmp = []

		for o in resp['Contents']:
			fn = o['Key'].replace('alexa_audio/','')
			if "offair" in fn or fn is "":
				pass
			else:
				#print fn
				month, day, year, date = getdatefromfilename(fn)
				if isvaliddate(month, day, year) is True and isnotfuturedate(month, day, year) is True:
					tmp.append(fn)

			print tmp

		print "latest episode is: "+ tmp[-1]
		return tmp[-1]
	except Exception as e:
		print "Error talking to s3"
		raise
		return False

# save file to s3
def s3save(filename, fileobj):
	try:
		s3 = boto3.client( 's3', aws_access_key_id=os.environ['S3KI'], aws_secret_access_key=os.environ['S3SK'])
		print "Connected to s3!!"

		s3.put_object(Bucket="wakey.io", Key="alexa_audio/"+filename, Body=fileobj)
		print "uploaded " + filename+ " to s3!"
		return True
	except Exception as e:
		print "Error saving to s3"
		raise
		return False


# download audio file from twilio and return file object
def getaudio(audiourl):
	try:
		# get file stream
		req_for_image = requests.get(audiourl, stream=True)
		file_object_from_req = req_for_image.raw
		req_data = file_object_from_req.read()
		print "Retreived audio stream!!"
		return req_data
	except Exception as e:
		print "Error retreiving audio stream"
		raise
		#return False


# amplify audio file using streams & ffmpeg
def amplify(audio):
	try:
		ff = FFmpeg(
		inputs={"pipe:0":None},
		outputs={"pipe:1": "-y -af \"highpass=f=200,  lowpass=f=3000, loudnorm=I=-14:TP=-2.0:LRA=11\" -b:a 256k -f mp3"} )
		print ff.cmd

		stdout, stderr = ff.run(
			input_data=audio,
			stdout=subprocess.PIPE)
		#print stdout
		#print stderr
		print "Amplified audio!!"
		return stdout
	except Exception as e:
		print "Error amplifying audio stream"
		raise
		#return False


# validate date (assumes current year, unless specified)
def isvaliddate(month, day, year=(datetime.now().year)):
    correctDate = None
    try:
        newDate = datetime(year, month, day)
        correctDate = True
    except ValueError:
        correctDate = False
    return correctDate


# make sure date is not in the future & also a valid date
def isnotfuturedate(month, day, year):
	qdate = datetime(year, month, day, tzinfo=pytz.UTC)
	now = datetime.now(pytz.UTC)
	if qdate <= now:
		return True
	else:
		return False


def save_to_s3_CLASSIC():
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

		#AMPLIFY!!!!
		ff = FFmpeg(
		    inputs={"pipe:0":None},
		    outputs={"pipe:1": "-y -af \"highpass=f=200,  lowpass=f=3000, loudnorm=I=-14:TP=-2.0:LRA=11\" -b:a 256k -f mp3"} )
		print ff.cmd

		stdout, stderr = ff.run(
		    input_data=req_data,
		    stdout=subprocess.PIPE)

		#print stdout
		#print stderr
		print "normalized audio"

		# Upload to s3
		s3.put_object(Bucket="wakey.io", Key="alexa_audio/"+filename, Body=stdout)
		print "uploaded " + filename+ " to s3"
		return True

	except Exception as e:
		print "Error uploading " + filename+ " to s3"
		raise
		return False


def save_to_s3_twilio():
	print "recording url: " + session['mp3url']
	filename = session['airdate'].strftime("%Y-%m-%d")+".mp3"
	print "filename: " + filename

	# download, process, and save url to s3
	try:
		# get audio file stream
		audio = getaudio(session['mp3url'])

		# amplify audio
		amped_audio = amplify(audio)

		# upload to s3
		return s3save(filename, amped_audio)

	except Exception as e:
		print "Error getting, processing, or saving " + filename
		raise
		return False


def save_to_s3_email(date, file_obj):
	filename = date.strftime("%Y-%m-%d")+".mp3"
	print "filename: " + filename

	# download, process, and save url to s3
	try:
		# get audio file stream
		#audio = getaudio(session['mp3url'])

		# amplify audio
		amped_audio = amplify(file_obj)

		# upload to s3
		return s3save(filename, amped_audio)

	except Exception as e:
		print "Error getting, processing, or saving " + filename
		raise
		return False


def url_check(url):
	ping = requests.get(url)
	print(ping.status_code)
	if ping.status_code == 200:
		print "OK, we found that file"
		return True
	else:
		print "NOPE, we did not find that file"
		return False


def emailback(email, subject, body):
	try:
		resp = requests.post(
        os.environ['MAILGUNDOMAIN']+"/messages",
        auth=("api", os.environ['MAILGUNKEY']),
        data={"from": "AlexaFeed <alexa@neal.rs>",
              "to": [email],
              "subject": subject,
              "text": body})
	except Exception as e:
		print "Error sending email"
		raise
		return False

# establish current date in PT timezone
def getTime():
	tz = pytz.timezone('America/Los_Angeles')
	today = datetime.now(tz)
	today_utc = today.astimezone(pytz.UTC)
	date = today.strftime("%Y-%m-%d")
	date_locale = today.strftime("%a, %B %d").lstrip("0").replace(" 0", " ")

	# debug lines for date info #
	#print date
	#print date_locale
	#print today
	#print today_utc
	return date, date_locale, today, today_utc


# Generate feed based on day of week
@app.route('/', methods=['GET'])
def index():
	# get current date in PT timezone
	date, date_locale, today, today_utc = getTime()

	feed = {}
	feed['uid'] = str(uuid.uuid4())
	feed['updateDate'] = today_utc.strftime('%Y-%m-%dT%H:%M:%S.0Z')
	feed['mainText'] = ''

	url = "https://wakey.io/alexa_audio/" +date+ ".mp3"
	print "checking for: " + url
	if url_check(url):
		print "on-air"
		feed['titleText'] = 'Wakey Wakey ~ '+ date_locale
		feed['streamUrl'] = url
	else:
		print "off-air" # no content found
		feed['titleText'] = 'Wakey Wakey is off-air right now, check back again soon!'
		feed['streamUrl'] = "https://wakey.io/alexa_audio/offair_"+str(randint(0, 4))+".mp3"

	feed_json = json.dumps(feed)
	print feed_json
	return feed_json


# return list of episodes & offairs w/ html5 audio players (kind of like an admin dashboard, but unprotected right now)
@app.route('/episodes', methods=['GET'])
def episodes():
	data = geteps()
	if data:
		return render_template(
			'episodes.html',
			phone=os.environ['PHONE'],
			email=os.environ['EMAIL'],
            data=data)
	else:
		return render_template('error.html')


# return latest episode filename (with prefix)
@app.route('/latest', methods=['GET'])
def latest():

	fn = getlatest()
	date = fn[:-4]

	latest = {"date": date, "filename": "https://wakey.io/"+ fn}

	feed_json = json.dumps(latest)
	print feed_json
	return feed_json

# return iTunes podcast feed xml (does not include -future- episodes)
@app.route('/podcast', methods=['GET'])
def podcast():
	data = getepsiTunes()
	date, date_locale, today, today_utc = getTime()
	dt = today.timetuple()
	dts = mktime(dt)
	daterfc = utils.formatdate(dts)
	if data:
		for ep in data['episodes']:
			xml = render_template(
			'feed.xml',
			date=daterfc,
            data=data)
		feed = make_response(xml)
		feed.headers["Content-Type"] = "application/xml"
		return feed
	else:
		return render_template('error.html')


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
		gather = Gather(input='dtmf speech', timeout=5, num_digits=4, action='/set_date', method='GET')
		gather.say("Let's record a new Wakey Wakey!\n First, when will this episode air?\n Say the air date or punch it in using a Month Month Day Day format.\n For example, you could say October 31st or punch in 10 31.")
		resp.append(gather)
		resp.say("You didn't give me a date. Bye!")
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
	speech = request.values.get('SpeechResult', None)
	print "dtmf digits: "+ str(digits)
	#print "speech recognition: " + speech
	#month=0
	#digits=0
	year=datetime.now().year

	if speech:
		cal = pdt.Calendar()
		time, status = cal.parse(speech)
		spoken_date = datetime(*time[:6])
		print "spoken date: "+ spoken_date.strftime("%A, %B %-d, %Y")
		month = spoken_date.month
		day = spoken_date.day
		year = spoken_date.year
	else:
		month = int(str(digits[:2]).lstrip("0").replace(" 0", " "))
		day = int(str(digits[-2:]).lstrip("0").replace(" 0", " "))

	if isvaliddate(month, day, year) is True:
		session['airdate'] = datetime(year,month,day)
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
	gather = Gather(input='dtmf', timeout=15, num_digits=1, action='/save_finish', method='GET')
	gather.say('To schedule this episode, press 1. Otherwise, hang up.')
	resp.append(gather)
	resp.say("Uhm, ok, hanging up now.")
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
		if save_to_s3_twilio() is True:
			resp.say("And boom, you're good to go! See you next time " + session['caller'] +" !")
		else:
			resp.say("Yikes "+ session['caller'] + " we ran into an error saving to s3. Can you try calling in again? Sorry!!")
	else:
		resp.say("No problem, just hangup and call back again.")

	resp.hangup()
	session.clear()
	return str(resp)

# process incoming email via mailgun routes (SUPER HACKY!!!)
@app.route("/email", methods=["GET", "POST"])
def email():
	sender = request.form['sender']
	date = request.form['subject']
	month = int(date[5:-3].lstrip("0").replace(" 0", " "))
	day = int(date[-2:].lstrip("0").replace(" 0", " "))
	year = int(date[:4])
	print "From: "+ sender
	print "subject: "+ date

	if sender in emailers:
		print "It's an email from "+ emailers[sender]

		if isvaliddate(month, day, year) is True:
			fndate = datetime(year,month,day)
			print "airdate: "+ fndate.strftime("%A, %B %-d, %Y")

			print "audio file: "+ request.files.values()[0].filename
			data = request.files.values()[0].stream.read()

			if save_to_s3_email(fndate, data) is True:
				print request.files.values()[0].filename+" saved!"
				emailback(sender, "Your WW airs "+ fndate.strftime("%A, %B %-d, %Y"), emailers[sender]+ ", we successfully scheduled your episode.\n\nDon't reply to this email.")
				return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
			else:
				print "error saving "+attachment.filename
				emailback(sender, "Error saving your WW ep to S3", "Try again? \n\nDon't reply to this email.")
				return json.dumps({'file_saved':False}), 200, {'ContentType':'application/json'}
		else:
			print "incorrectly formatted date "+date
			emailback(sender, "Error in your WW airdate", "Try again - and remember - your subject line should be 'YYYY-MM-DD', and that's it.\n\nDon't reply to this email.")
			return json.dumps({'date_correct':False}), 200, {'ContentType':'application/json'}
	else:
		return json.dumps({'good_email':False}), 200, {'ContentType':'application/json'}

if __name__ == "__main__":
	app.run(debug=False)
