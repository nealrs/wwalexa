# AlexaFeed

[![video thumbnail](https://img.youtube.com/vi/SfQLD24O7zY/mqdefault.jpg)](https://youtu.be/SfQLD24O7zY)

[Watch a demo on YouTube](https://youtu.be/SfQLD24O7zY)

This Flask app creates audio Flash Briefings for Alexa by doing 2 things:

1. Allowing you to call in and record audio clips, saving them to s3 using date-based filename.

2. Generating a dynamic Alexa Flash Briefing JSON feed based on the current date.

[Live demo of the feed](https://wakeyio-alexa.herokuapp.com/).

[Listen a recording from June 16th](https://wakey.io/alexa_audio/2017-06-16.mp3).

I haven't certified my skill yet, so that's why you can't subscribe to it -- but trust the video demo.

## Calling in Updates

If you are an authorized caller, the app greets and prompts you to set an air date as a 4 digit DTMF input, (so `1031` would be Halloween).

Next, it'll ask you to record up to 3 minutes of audio and replay it for you.

If you are satisfied with your recording, you press `1` and the app will upload the audio (as an mp3) to s3 using the current day `2017-10-31` as the filename.

Once confirmed, the app will tell you to rock on and hangup. And boom, you've recorded a new episode for your flash briefing!!

## The Feed

As configured, on Monday, Wednesday, and Friday, your briefing will play an audio file based on the current date (YYYY-MM-DD.mp3).

```
{
  streamUrl: "https://wakey.io/public/mp3/2017-06-14.mp3",
  mainText: "",
  uid: "82a75e11-8ed2-4035-99ac-aeaa20062158",
  titleText: "Wakey Wakey ~ Wed, June 14",
  updateDate: "2017-06-14T05:56:33.0Z"
}
```

All other days, the feed will play a canned "we're off the air today" message.

```
{
  streamUrl: "https://wakey.io/public/mp3/offair.mp3",
  mainText: "",
  uid: "090b085e-f208-4431-9459-0bfd5d323888",
  titleText: "Wakey Wakey airs Monday, Wednesday, and Friday.",
  updateDate: "2017-06-15T06:05:02.0Z"
}
```

Since Alexa is primarily a US thing, the app uses Pacific time to determine what day it is / what to show.

## How to Use

1. Create a public s3 bucket for your audio files & configure the code to use your bucket.

2. Set environment variables for s3 access & authorized numbers:

```
S3KI=derppppp
S3SK=derpppppppppp

NS=+1XXXXXXXXX
RM=+1XXXXXXXXX
SL=+1XXXXXXXXX

SESSKEY=rand0mstr1ng
```

3. Deploy this hot mess to Heroku (or wherever - I originally deployed the feed code as an AWS Lambda).

4. Point your Twilio number to `http://yourapp/begin_call`

5. Call yourself and record a test message for today.

6. Log in to s3 and verify the file is publicly accessible.

7. [Follow these steps]( https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/steps-to-create-a-flash-briefing-skill) to setup your Flash Briefing on Alexa using your app's root URL.

8. If it works, submit it for certification and tell all your friends to subscribe.
