"""
Endpoints
"""
__author__ = ['Enis Simsar', 'Kemal Berk Kocabagli']

import tornado.web

from settings import settings
from handlers.main import MainHandler
from handlers.auth import LoginHandler, LogoutHandler, ProfileHandler, RegisterHandler, TwitterAuthHandler # , FacebookAuthHandler

from handlers.topic import TopicHandler, TopicsHandler, CreateEditTopicHandler, PagesHandler
from handlers.topic import ThemesHandler, ThemesV11Handler, TopicsV12Handler

from handlers.conversation import PreviewConversationHandler, ConversationHandler, ConversationPageHandler
from handlers.conversation import ConversationV12Handler

from handlers.event import PreviewEventHandler, EventPageHandler, EventHandler, HideEventHandler
from handlers.event import EventV12Handler, EventV13Handler

from handlers.news import PreviewNewsHandler, NewsHandler, SearchHandler, SearchNewsHandler, FeedHandler, SentimentHandler, BookmarkHandler, DomainHandler
from handlers.news import NewsV12Handler, NewsV13Handler, FeedsHandler, FeedsV11Handler, NewsFeedsV12Handler, NewsFeedsV13Handler, HashtagsV12Handler

from handlers.audience import AudienceHandler, RateAudienceHandler
from handlers.audience import AudienceV12Handler, AudienceSampleV13Handler

from handlers.influencer import LocalInfluencersHandler, HideInfluencerHandler, FetchFollowersHandler
from handlers.influencer import InfluencersHandler, InfluencersV11Handler, LocalInfluencersV13Handler

from handlers.challenge import ChallengeV13Handler

from handlers.crons_log import CronsLogHandler

from handlers.hashtag import HashtagHandler, HashtagChartHandler

from handlers.mention import MentionChartHandler

from handlers.tweet import RedirectHandler, NewTweetsHandler, TweetsHandler
from handlers.recommendation import RecommendationsHandler
from handlers.location import LocationHandler
from handlers.documentation import DocumentationHandler, Documentationv11Handler, Documentationv12Handler, Documentationv13Handler

url_patterns = [
    # MAIN
    (r"/", MainHandler),

    # AUTH
    (r"/login", LoginHandler),
    (r"/logout", LogoutHandler),
    (r"/profile", ProfileHandler),
    (r"/register", RegisterHandler),
    (r"/twitter_auth", TwitterAuthHandler),
    #(r"/facebook_auth", FacebookAuthHandler),

    # TOPIC
    (r"/saveTopicId", TopicHandler),
    (r"/Topics", TopicsHandler),
    (r"/topicinfo", CreateEditTopicHandler),
    (r"/topicinfo/([0-9]*)", CreateEditTopicHandler),
    (r"/getPages", PagesHandler),

    # CONVERSATION
    (r"/previewConversations", PreviewConversationHandler),
    (r"/Conversations/(.*)", ConversationPageHandler),
    (r"/Conversations", ConversationPageHandler),
    (r"/Comments/(.*)", ConversationHandler),
    (r"/Comments", ConversationHandler),

    # EVENT
    (r"/previewEvents", PreviewEventHandler),
    (r"/Events/(.*)", EventPageHandler),
    (r"/Events", EventPageHandler),
    (r"/get_events/(.*)", EventHandler),
    (r"/get_events", EventHandler),
    (r"/hide_event", HideEventHandler),

    # NEWS
    (r"/previewNews", PreviewNewsHandler),
    (r"/News/(.*)", NewsHandler),
    (r"/News", NewsHandler),
    (r"/Search", SearchHandler),
    (r"/get_news", SearchNewsHandler),
    (r"/get_news/(.*)", SearchNewsHandler),
    (r"/Feed/(.*)", FeedHandler),
    (r"/Feed", FeedHandler),
    (r"/sentiment", SentimentHandler),
    (r"/bookmark", BookmarkHandler),
    (r"/domain", DomainHandler),

    # AUDIENCE
    (r"/Audience/(.*)", AudienceHandler),
    (r"/Audience", AudienceHandler),
    (r"/rate_audience", RateAudienceHandler),

    # INFLUENCER
    (r"/Influencers/(.*)", LocalInfluencersHandler),  # added for influencers
    (r"/Influencers", LocalInfluencersHandler),
    (r"/hide_influencer", HideInfluencerHandler),
    (r"/fetch_followers", FetchFollowersHandler),

    # TWEET
    (r"/Tweets/(.*)", TweetsHandler),
    (r"/Tweets", TweetsHandler),
    (r"/newTweets", NewTweetsHandler),
    (r"/newTweets/(.*)", NewTweetsHandler),
    (r"/redirect", RedirectHandler),


    # RECOMMENDATION
    (r"/Recommendations/(.*)", RecommendationsHandler),  # added for recommendations
    (r"/Recommendations", RecommendationsHandler),

    # LOCATION
    (r"/saveLocation", LocationHandler),

    # CRONS MANAGEMENT
    (r"/crons-logs", CronsLogHandler),

    # HASHTAG
    (r"/hashtag", HashtagHandler),
    (r"/Hashtags", HashtagChartHandler),

    # MENTION
    (r"/Mentions", MentionChartHandler),

    # DOCUMENTATION
    (r"/api", DocumentationHandler),
    (r"/api/v1\.1", Documentationv11Handler),
    (r"/api/v1\.2", Documentationv12Handler),
    (r"/api/v1\.3", Documentationv13Handler),

    # API V1
    (r"/api/get_themes", ThemesHandler),
    (r"/api/get_influencers/(.*)/(.*)", InfluencersHandler),
    (r"/api/get_feeds/(.*)/(.*)", FeedsHandler),
    (r"/api/get_influencers/(.*)", InfluencersHandler),
    (r"/api/get_feeds/(.*)", FeedsHandler),

    # API V1.1
    (r"/api/v1.1/get_themes", ThemesV11Handler),
    (r"/api/v1.1/get_feeds", FeedsV11Handler),
    (r"/api/v1.1/get_influencers", InfluencersV11Handler),

    # API V1.2
    (r"/api/v1.2/get_topics", TopicsV12Handler),
    (r"/api/v1.2/get_news", NewsFeedsV12Handler),
    (r"/api/v1.2/get_audiences", AudienceV12Handler),
    (r"/api/v1.2/search_news", NewsV12Handler),
    (r"/api/v1.2/get_events", EventV12Handler),
    (r"/api/v1.2/get_conversations", ConversationV12Handler),
    (r"/api/v1.2/get_hashtags", HashtagsV12Handler),

    # API V1.3
    # get_audiences deprecated
    (r"/api/v1.3/get_topics", TopicsV12Handler),
    (r"/api/v1.3/get_audience_sample", AudienceSampleV13Handler),  # new
    (r"/api/v1.3/get_local_influencers", LocalInfluencersV13Handler),  # new
    (r"/api/v1.3/get_news", NewsFeedsV13Handler),  # changed
    (r"/api/v1.3/search_news", NewsV13Handler),  # changed
    (r"/api/v1.3/get_events", EventV13Handler),  # changed
    (r"/api/v1.3/get_conversations", ConversationV12Handler),
    (r"/api/v1.3/get_hashtags", HashtagsV12Handler),
    (r"/api/v1.3/get_challenges", ChallengeV13Handler),  # new

    (r"/(.*)", tornado.web.StaticFileHandler, {'path': settings['static_path']}),
]
