## FLASK AUDIO FEED FOR ALEXA

This app dynamically generates an audio JSON Alexa Flash Briefing feed, based on the day of the week. [Here's a live demo](https://09kp4l2utc.execute-api.us-east-1.amazonaws.com/dev).

As configured, on Monday, Wednesday, and Friday, it plays an audio file based on the current date (YYYY-MM-DD.mp3).

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

To get this up & running for yourself, you'll need to:

1. Host your audio files in a public bucket on s3
2. Configure the code to use your s3 bucket (just change the domain).
3. [Deploy the Flask app as an AWS Lambda](https://developer.amazon.com/blogs/post/8e8ad73a-99e9-4c0f-a7b3-60f92287b0bf/new-alexa-tutorial-deploy-flask-ask-skills-to-aws-lambda-with-zappa) function using [Zappa](https://github.com/Miserlou/Zappa).
4. [Follow these steps](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/steps-to-create-a-flash-briefing-skill) to setup your Flash Briefing & submit it for certification.
