import collections
import json
import math
import matplotlib.pyplot as plt
import nltk
import numpy as np

from blingfire import text_to_sentences
from datetime import datetime
from nltk.sentiment import SentimentIntensityAnalyzer
from praw import Reddit
from praw.models import MoreComments
from typing import Dict

nltk.download(["averaged_perceptron_tagger",
               "vader_lexicon",
               "punkt",
               ])


def connect_to_reddit(client_id, client_secret):
    return Reddit(client_id=client_id,
                  client_secret=client_secret,
                  user_agent="Match-Thread-Analysis")


def iter_top_level(comments):
    for top_level_comment in comments:
        if isinstance(top_level_comment, MoreComments):
            yield from iter_top_level(top_level_comment.comments())
        else:
            yield top_level_comment


def get_index(event_time: int) -> int:
    if event_time <= 0:
        return 0
    elif 1 <= event_time <= 50:
        return (event_time - 1) // 5 + 1
    elif 51 <= event_time <= 65:
        return 11
    elif 66 <= event_time <= 115:
        return (event_time - 1) // 5 - 1
    else:
        return 22


def get_mode(label: Dict) -> str:
    ans, val = "neg", label["neg"]
    for key in ["neu", "pos"]:
        if label[key] > val:
            val = label[key]
            ans = key
    return ans


def collect_comments(client_id, client_secret, submission_id: str, day: int, month: int, year: int, hour: int,
                     minute: int):
    reddit = connect_to_reddit(client_id, client_secret)
    submission = reddit.submission(id=submission_id)
    user_comments = collections.defaultdict(list)
    kick_off_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    for comment in iter_top_level(submission.comments):
        event_time = math.ceil((datetime.utcfromtimestamp(comment.created_utc) - kick_off_time).total_seconds() / 60)
        key = get_index(event_time)
        val = text_to_sentences(comment.body)
        user_comments[key].append(val)

    with open("match_thread.json", "w") as f:
        json.dump(user_comments, f)


def sentiment_analysis():
    with open("match_thread.json", mode="r") as f:
        user_comments = json.load(f)
        sia = SentimentIntensityAnalyzer()
        X = ["pre", "1-5", "6-10", "11-15", "16-20", "21-25", "26-30", "31-35", "36-40", "41-45",
             "stop-1", "half", "46-50", "51-55", "56-60", "61-65", "66-70", "71-75", "76-80", "81-85",
             "86-90", "stop-2", "post"]
        Y_positive = [0] * 23
        Y_negative = [0] * 23
        Y_neutral = [0] * 23

        for key in user_comments.keys():
            for comment in user_comments[key]:
                label = get_mode(sia.polarity_scores(comment))
                if label == "pos":
                    Y_positive[int(key)] += 1
                elif label == "neg":
                    Y_negative[int(key)] += 1
                else:
                    Y_neutral[int(key)] += 1

        X_axis = np.arange(len(X))
        f = plt.figure()
        f.set_figwidth(18)
        f.set_figheight(9)
        plt.bar(X_axis - 0.2, Y_positive, 0.2, label="Positive")
        plt.bar(X_axis, Y_negative, 0.2, label='Negative')
        # plt.bar(X_axis + 0.2, Y_neutral, 0.2, label='Neutral')
        plt.xticks(X_axis, X)
        plt.xlabel("Intervals")
        plt.ylabel("Number of Comments")
        plt.title("Sentiment of Comments throughout a football match")
        plt.legend()
        plt.show()


if __name__ == "__main__":
    # Reddit account info
    client_id = ""
    client_secret = ""

    # Match-thread info
    submission_id = "100mpme"
    day = 1
    month = 1
    year = 2023
    hour = 16
    minute = 30

    # Collect all comments from match-thread (~Takes 5-10 minutes)
    collect_comments(client_id=client_id, client_secret=client_secret, submission_id="100mpme", day=1, month=1,
                     year=2023, hour=16, minute=30)

    # Perform sentiment analysis on collected comments
    sentiment_analysis()
