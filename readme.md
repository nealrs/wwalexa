# AlexaFeed

**TL;DR: Record a phone-call & use it to dynamically generate a JSON audio Alexa Flash Briefing feed.** [Watch a demo on YouTube](https://youtu.be/SfQLD24O7zY)

[![video thumbnail](https://img.youtube.com/vi/SfQLD24O7zY/mqdefault.jpg)](https://youtu.be/SfQLD24O7zY)

## In more detail

This Flask app creates audio Flash Briefings for Alexa by doing 2 things:

1. Allowing you to call in and record audio clips, saving them to s3 using date-based filename.

2. Generating a dynamic Alexa Flash Briefing JSON feed based on the current date.

[Live demo of the feed](https://wakeyio-alexa.herokuapp.com/).

[Listen a recording from June 16th](https://wakey.io/alexa_audio/2017-06-16.mp3).

I haven't certified my skill yet, so that's why you can't subscribe to it -- but trust the video demo.

## Motivation

AlexaFeed was an itch I had to scratch, motivated by a few things:

1. My video project, Wakey Wakey](http://wakey.io), wasn't getting enough traction and required too much production time for each episode. It was time to explore different formats

2. Blogging is boring, RSS is basically dead, and it seems like nobody reads beyond the headlines anymore.

3. Podcasts are having a moment (again?), but producing &amp; distributing them is this endless chain of steps.

4. Alexa has big market penetration among my friends & family. It's an excellent distribution platform for content, but most people use it for setting timers, listening to music, and checking the weather.

5. Alexa's Flash Briefings are a first class feature, and support both text & audio briefings. And yet, there are very few orgs & content creators targeting this platform.

6. I previously wrote a [Jekyll -> Flash Briefing plugin](https://gist.github.com/nealrs/e6985003ca56cc6f8c980efbb0d0e670), so you can _listen_ to your blog.

7. Amazon recently introduced metrics for Flash Briefings.

8. I noticed the upcoming Echo Show will support _video_ Flash Briefings...

So, after ruminating on all that, I thought: what if me, Steve, and Richard (my other Wakey Wakey collaborators) could produce new content on our own, and then publish it to Alexa without ever having to touch a computer?

Well, it used to be (and probably still is?) common practice for field reporters to call in their stories to the newsroom.

You've probably you've seen it in _The Wire_ and similar journalism driven movies. Some super excited dude in a bar calls a grizzled newsman in the bullpen and tells him to take all this down. Then, after hanging up, the newsman cranks out a story and submits it before deadline. Neat, right?

So, I created a digital newsroom, where approved reporters can call in stories, set an air date, and schedule them. And  then, on the appropriate day, content is published automatically to Alexa, where subscribers can "read" the news by asking for their flash briefing.

So I guess it's like an audio newspaper? And with some code tweaks, you could support multiple news items a day, or replace the audio midway through the day for a "late edition."


## Calling in Updates

If you are an authorized caller, the app greets and prompts you to set an air date as a 4 digit DTMF input, (so `1031` would be Halloween).

Next, it'll ask you to record up to 3 minutes of audio and replay it for you.

If you are satisfied with your recording, you press `1` and the app will upload the audio (as an mp3) to s3 using the current day `2017-10-31` as the filename.

Once confirmed, the app will tell you to rock on and hangup. And boom, you've recorded a new episode for your flash briefing!!

_FYI_: The [official Alexa Feed spec](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/flash-briefing-skill-api-feed-reference) specifies a particular loudness for audio content and Twilio's recording quality isn't perfect.

Alexa isn't super forgiving when it comes to audio loudness. It's pretty common for audio briefings to play softly because the engineer, didn't you know, _engineer_ it. So I went down the rabbit hole and incorporated an FFmpeg pipeline to adjust the loudness do some hi/lo pass filtering. It means you'll need to install ffmpeg as a separate buildpack on Heroku - but it also works SUPER WELL.

## The Feed

When you load the feed url, the server will look for an mp3 file based on the current date: `YYYY-MM-DD.mp3`.

```
{
  streamUrl: "https://wakey.io/public/mp3/2017-06-14.mp3",
  mainText: "",
  uid: "82a75e11-8ed2-4035-99ac-aeaa20062158",
  titleText: "Wakey Wakey ~ Wed, June 14",
  updateDate: "2017-06-14T05:56:33.0Z"
}
```

If it can't find a file for that day, it'll play a canned "we're off the air today" message.

```
{
  streamUrl: "https://wakey.io/public/mp3/offair.mp3",
  mainText: "",
  uid: "090b085e-f208-4431-9459-0bfd5d323888",
  titleText: "Wakey Wakey is off-air right now, check back again soon!",
  updateDate: "2017-06-15T06:05:02.0Z"
}
```

Since Alexa is primarily a US thing, the app uses Pacific time to determine what day/time it is.

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

3. Deploy this hot mess to Heroku and install this [buildpack](https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest) for FFmpeg.

4. Point your Twilio number to `http://yourapp/begin_call`

5. Call yourself and record a test message for today.

6. Log in to s3 and verify the file is publicly accessible.

7. [Follow these steps]( https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/steps-to-create-a-flash-briefing-skill) to setup your Flash Briefing on Alexa using your app's root URL.

8. If it works, submit it for certification and tell all your friends to subscribe.

9. Keep publishing new content!!
