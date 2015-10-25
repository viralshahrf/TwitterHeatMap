from tweepy.streaming import StreamListener
import json
from pymongo.mongo_client import MongoClient

# Some user defined keywords for filtering
keywords = ["love","football","tech","trump","india"]

class StreamTweetListener(StreamListener):
    max_size = 100000000
    max_length = None

    def __init__(self):
        self.client = MongoClient()
        self.db = self.client.tweetDB
        self.tweets = self.init_collection('tweets')

    def init_collection(self, collection_name):
        if collection_name not in self.db.collection_names():
            collection = self.db.create_collection(collection_name,
                                                    capped=True,
                                                    size=self.max_size,
                                                    max=self.max_length)
        else:
            collection = self.db[collection_name]
            if not collection.options().get('capped'):
                raise TypeError(
                    'Collection "{0}" is not capped'.format(collection_name))
        return collection

    def on_data(self, tweet):
        json_tweet = json.loads(tweet)
        if "coordinates" in json_tweet:
            coordinates =  json_tweet['coordinates']
            if coordinates is not None:
                # Finding and Storing keywords
                for keyword in keywords:
                    if keyword in json_tweet['text'].lower():
                        json_tweet["keyword"] = keyword;
                # Store it in MongoDB
                count = self.tweets.find().count()
                count = count + 1
                print "Inserting into DB" , count
                self.tweets.insert_one(json_tweet)
        return True

    def on_error(self, status):
        print "Error: "+ status + "\n"
        return False

    def on_status(self, status):
        print "Status: ", status
