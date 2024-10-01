#!/usr/bin/env python
import asyncio
from dotenv import load_dotenv
import logging
from openai import OpenAI
import os
import re
from sys import stdout
from twikit import Client

logger = logging.getLogger("sedcontraest")
handler = logging.StreamHandler(stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d %(funcName)s] %(message)s', datefmt='%Y-%m-%d:%H:%M:%S'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

load_dotenv(os.getenv('HOME') + "/.env")  # contains OPENAI_API_KEY
AI = OpenAI()

_HISTORY = os.path.expanduser("~/.sedcontraest_history")

def add_to_list_of_processed_tweets(tweet_id):
    history_filename = f"{_HISTORY}"
    try:
        file = open(history_filename, "a")
        file.write(f"{tweet_id}\n")
        file.close()
        logger.info(f"Added '{tweet_id}' to '{history_filename}'")
    except Exception as e:
        logger.error(f"Error adding '{tweet_id}' to '{history_filename}': {e}")

def list_processed_tweets():
    filename = f"{_HISTORY}"
    try:
        file = open(filename)
        lines = file.read().splitlines()
        file.close()
    except FileNotFoundError:
        file = open(filename, "w")
        logger.warning(f"Created empty file: '{filename}'")
        lines = []
        file.close()
    logger.info(f"Number of tweets ever processed: {str(len(lines))}")
    return lines

def answer(statement):
    messages = [
        {"role": "system", "content": "I want you to act as a catholic theology scholar. I will provide you with a statement and you will answer with a quote from a work of any preconciliar catholic theologian, pope or church father. Your quote contains a theological truth that is closely related to the statement. Your quote can be contradicting the statement if it is not aligning with the truth of the deposit of faith. You prefer to quote from sources that are not very popular. You just return the quote and its author. Your answer is in the same language as the statement."}
    ] 
    messages.append({"role": "user", "content": statement})
    while True:
        completion = AI.chat.completions.create(
          model="gpt-3.5-turbo",
          messages=messages
        )
        response = completion.choices[0].message.content
        if len(response) < 240:
            break       
        else:
            logger.info(f"Find shorter quote i.o. '{response}'")
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": "This is too long. Please find a shorter quote."})
    return response

def clean_tweet(tweet):
    # Remove Twitter handles (@user)
    tweet = re.sub(r'@[A-Za-z0-9_]+', '', tweet)
    # Remove hashtags (#hashtag)
    tweet = re.sub(r'#\w+', '', tweet)
    # Remove URLs (http:// or https:// links)
    tweet = re.sub(r'http\S+|www\S+|https\S+', '', tweet)
    # Remove excess whitespace
    tweet = tweet.strip()
    return tweet

async def main():
    # Authenticate to Twitter scraper for user 'catechismus'
    catechismus_twikit_client = Client('en-US')
    catechismus_cookies_file = 'catechismus-twikit-cookies.json'
    if os.path.isfile(catechismus_cookies_file):
        catechismus_twikit_client.load_cookies(catechismus_cookies_file)
    else:
        await catechismus_twikit_client.login(
            auth_info_1=os.environ["X2_USERNAME"],
            auth_info_2=os.environ["X2_EMAIL"],
            password=os.environ["X2_PASSWORD"]
        )
        catechismus_twikit_client.save_cookies(catechismus_cookies_file)

    # Authenticate to Twitter scraper for user 'sedcontraest'
    sedcontraest_twikit_client = Client('en-US')
    sedcontraest_cookies_file = 'sedcontraest-twikit-cookies.json'
    if os.path.isfile(sedcontraest_cookies_file):
        sedcontraest_twikit_client.load_cookies(sedcontraest_cookies_file)
    else:
        await sedcontraest_twikit_client.login(
            auth_info_1=os.environ["X_USERNAME"],
            auth_info_2=os.environ["X_EMAIL"],
            password=os.environ["X_PASSWORD"]
        )
        sedcontraest_twikit_client.save_cookies(sedcontraest_cookies_file)

    # Fetch mentions of 'sedcontraest' and post replies
    processed_tweet_ids = list_processed_tweets()
    tweets = await catechismus_twikit_client.search_tweet('@sedcontraest', 'Latest')
    for tweet in tweets:
        if tweet.id in processed_tweet_ids:
            logger.info(f"Tweet already replied to with text '{tweet.text}'")
            continue
        statement = clean_tweet(tweet.text)
        if len(statement) < 10:
            logger.warning(f"No sensible quote in tweet with text '{tweet.text}'")
            add_to_list_of_processed_tweets(tweet.id)
            continue
        reply = answer(statement)
        logger.info(f"Replying to tweet '{tweet.id}' with text '{tweet.text}' containing quote '{statement}' with '{reply}'")
        add_to_list_of_processed_tweets(tweet.id)
        # add to list first, because following command tends to keep causing errors 
        response = await sedcontraest_twikit_client.create_tweet(text=reply, reply_to=str(tweet.id))
        logger.info(f"Twikit response '{response}'")


asyncio.run(main())
