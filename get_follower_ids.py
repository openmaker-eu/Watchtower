import tweepy  # Twitter API helper package
from tweepy import OAuthHandler
import pprint # to print human readable dictionary
import pymongo

import json
from datetime import datetime

import sys

from application.Connections import Connection

consumer_key = "utTM4qfuhmzeLUxRkBb1xb12P"  # API key
consumer_secret = "XteCQjAZCVAu7Tk5ftgcjv0jJlII2o7b8BqZc3sfEdwn1R6Ic7"  # API secret
access_token = "821415961467228161-iB85g0Lm8c4jLqIqxWcryWjE8nm6CPq"
access_secret = "BrNaqN0BP2K3rYzIurlaTIaJeOk4MBP6mzBtR73ay5ulU"

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

def get_follower_ids_by_influencer(influencer):
	'''
	get the follower ids for a specific influencer from Twitter from the last page where we left off.
	for new topics, followers are copied from the first topic of the influencer.
	save the follower ids to MongoDB for each topic of the influencer.
	'''
	print("Getting follower ids for influencer " + str(influencer['screen_name']))

	if (influencer['protected'] ==True):
		print("The account of this influencer is protected at the moment.")
		return 0

	if 	'last_cursor' in influencer:
		start_cursor=influencer['last_cursor']
	else:
		start_cursor = -1
	print("Start cursor value: " + str(start_cursor))

	# get all the follower ids page by page starting from the last page where we left off.

	# ATTENTION (!): the influencer might have lost some followers and gained others,
	# in which case we have a possibility of ignoring some of his new followers.

	# Another problem is that the last cursor value could be invalid if that page no longer exists.
	# We could keep track of the followers count, but since each influencer is updated on a weekly basis, it would not be
	# very accurate.

	cursor = tweepy.Cursor(api.followers_ids, screen_name=influencer['screen_name'], cursor=start_cursor)

	last_cursor = start_cursor
	page_count = 0
	followers_count = 0

	try:
		for page in cursor.pages():
			if (cursor.iterator.next_cursor!=0):
				last_cursor= cursor.iterator.next_cursor
			#pprint.pprint(api.rate_limit_status()['resources']['followers'])
			print("Page length: " + str(len(page)))

			first_topic_follower_id_count = Connection.Instance().audienceDB[str(influencer['topics'][0])].count({'influencers':influencer['id']})
			new_topics = []
			for topicID in influencer['topics']:
				if(Connection.Instance().audienceDB[str(topicID)].count({'influencers':influencer['id']}) < first_topic_follower_id_count):
					new_topics.append(topicID)

			if len(new_topics)!=0:
				print("New topics added to this influencer!")
			for topicID in new_topics:
				# for all topics that have been newly added to the infuencer,
				# insert all the follower ids to the table of that topic using the first topic of the influencer.
				print("Copying follower ids to topic: " + str(topicID))
				Connection.Instance().audienceDB[str(topicID)].create_index("id", unique=True)
				try:
					Connection.Instance().audienceDB[str(topicID)].insert_many(list(Connection.Instance().audienceDB[str(influencer['topics'][0])].find({'influencers': influencer['id']})),ordered=False)
				except:
					print("Exception in insert_many.")

			for topicID in influencer['topics']:
				# add follower ids under each topicID collection in MongoDB
				# Follower ids should be unique within a topic collection
				Connection.Instance().audienceDB[str(topicID)].create_index("id", unique=True)
				# upsert many
				print("UPSERTING")
				operations = []
				for follower_id in page:
					followers_count +=1
					operations.append(
			            pymongo.UpdateOne(
			            { 'id': follower_id},
			            { '$setOnInsert':{'processed': False}, # if the follower already exists, do not touch the 'processed' field
						'$addToSet': {'influencers': influencer['id']}
			            }, upsert=True)
			        )
				# max size of operations will be 5000 (page size).
				Connection.Instance().audienceDB[str(topicID)].bulk_write(operations,ordered=False)

			Connection.Instance().influencerDB['all_influencers'].update(
				{ 'id': influencer['id'] },
				{ '$set':{'last_cursor':last_cursor}} # update last cursor of this influencer
			)

			page_count +=1 # increment page count


	except tweepy.TweepError as twperr:
		print(twperr) # in case of errors due to protected accounts or if the page of the last cursor doesnt exist
		pass

	print("Processed " + str(page_count) + " pages.")

	Connection.Instance().influencerDB['all_influencers'].update(
		{ 'id': influencer['id'] },
		{ '$set':{'last_processed': datetime.now()} # update last processed time of this influencer
		}
	)

	print("Processed influencer: " + influencer['screen_name'] + " : " + str(followers_count) + " followers." ) # Processing DONE.
	print("========================================")
	return 1

def get_follower_ids():
	'''
	gets the follower ids for all topics. Will be run periodically.
	'''
	INFLUENCER_COUNT = 0
	N=5
	for influencer in Connection.Instance().influencerDB['all_influencers'].find({}):
		if influencer['followers_count'] > 10000: continue
		# if the influencer has been processed before, wait for at least a day to process him again.
		# get_influencers will be run once per week. Therefore, no new topic can be added to the influencer throughout a day.
		if 'last_processed' in influencer:
			if ((datetime.today()- influencer['last_processed']).days > 1):
				result = get_follower_ids_by_influencer(influencer)
				if result == 1: INFLUENCER_COUNT+=1 # successfully processed the influencer
			else:
				print(influencer['screen_name'] + " HAS ALREADY BEEN PROCESSED TODAY.")
		else:
			result = get_follower_ids_by_influencer(influencer)
			if result == 1: INFLUENCER_COUNT+=1 # successfully processed the influencer
		if(INFLUENCER_COUNT==N):break

def main():
	get_follower_ids()

if __name__ == "__main__":
    main()
