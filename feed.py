from flask import Flask
from datetime import datetime
import uuid
import pytz
import json

app = Flask(__name__)

@app.route('/')
def index():

    # establish current date in PT timezone
    tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(tz)
    today_utc = today.astimezone(pytz.UTC)
    date = today.strftime("%Y-%m-%d")
    day = today.isoweekday()
    date_locale = today.strftime("%a, %B %d").lstrip("0").replace(" 0", " ")

    # debug lines for date info #
    #print date
    #print day
    #print date_locale
    #print today_utc
    #print '\n'
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

if __name__ == '__main__':
    app.run()
