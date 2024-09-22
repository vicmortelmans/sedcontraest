#!/usr/bin/env python
from sys import stdout
from dotenv import load_dotenv
import logging
from openai import OpenAI
import os
import tweepy

logger = logging.getLogger("sedcontraest")
handler = logging.StreamHandler(stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d %(funcName)s] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

load_dotenv(os.getenv('HOME') + "/.env")  # contains OPENAI_API_KEY
AI = OpenAI()

# Authenticate to Twitter
key = ""
keySecret = " "
accessToken = " "
accessTokenSecret = " "
bearer_token=None
client = tweepy.Client(None,os.environ["X_API_KEY"],os.environ["X_API_KEY_SECRET"],os.environ["X_ACCESS_TOKEN"],os.environ["X_ACCESS_TOKEN_SECRET"])
client.get_me() 

def answer(statement):
    messages = [
        {"role": "system", "content": "I want you to act as a catholic theology scholar. I will provide you with a statement and you will return a quote from some work of a preconciliar catholic theologian, pope or church father that offers a theological view on the statement, opposing it if it is not aligning with the truth of the deposit of faith."}
    ] 
    messages.append({"role": "user", "content": statement})
    completion = AI.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=messages
    )
    return completion.choices[0].message.content


#print(answer("life is short"))
client.create_tweet(text=answer("life is short"))
