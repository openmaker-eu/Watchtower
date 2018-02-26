--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.6
-- Dumped by pg_dump version 9.6.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


--
-- Name: adminpack; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS adminpack WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION adminpack; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION adminpack IS 'administrative functions for PostgreSQL';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: added_influencers; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE added_influencers (
    topic_id bigint NOT NULL,
    location text NOT NULL,
    screen_name text
);


ALTER TABLE added_influencers OWNER TO openmakerpsql;

--
-- Name: archived_topics; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE archived_topics (
    topic_id bigint,
    topic_name text,
    topic_description text,
    keywords text,
    languages text,
    creation_time text DEFAULT ('now'::text)::date,
    keyword_limit integer,
    last_tweet_date date,
    is_running boolean DEFAULT true,
    is_publish boolean DEFAULT false,
    user_id bigint,
    audience_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE archived_topics OWNER TO openmakerpsql;

--
-- Name: COLUMN archived_topics.audience_deleted; Type: COMMENT; Schema: public; Owner: openmakerpsql
--

COMMENT ON COLUMN archived_topics.audience_deleted IS 'if this topic''s audience has been deleted before, this field will be True';


--
-- Name: audience_parameters; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE audience_parameters (
    topic_id bigint NOT NULL,
    location text NOT NULL,
    signal_strength bigint
);


ALTER TABLE audience_parameters OWNER TO openmakerpsql;

--
-- Name: audience_samples_last_executed; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE audience_samples_last_executed (
    topic_id bigint NOT NULL,
    location text NOT NULL,
    execution_duration interval,
    last_executed timestamp without time zone,
    from_predicted_location bigint,
    from_regex bigint
);


ALTER TABLE audience_samples_last_executed OWNER TO openmakerpsql;

--
-- Name: country_code; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE country_code (
    location_name text,
    country_code text
);


ALTER TABLE country_code OWNER TO openmakerpsql;

--
-- Name: hidden_events; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE hidden_events (
    topic_id bigint NOT NULL,
    event_link text NOT NULL,
    description text
);


ALTER TABLE hidden_events OWNER TO openmakerpsql;

--
-- Name: hidden_influencers; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE hidden_influencers (
    topic_id bigint NOT NULL,
    country_code text NOT NULL,
    influencer_id text NOT NULL,
    description text
);


ALTER TABLE hidden_influencers OWNER TO openmakerpsql;

--
-- Name: influencer_parameters; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE influencer_parameters (
    topic_id bigint NOT NULL,
    location text NOT NULL,
    signal_strength bigint DEFAULT 3,
    following_limit bigint
);


ALTER TABLE influencer_parameters OWNER TO openmakerpsql;

--
-- Name: location_country_codes; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE location_country_codes (
    location text,
    country_codes json
);


ALTER TABLE location_country_codes OWNER TO openmakerpsql;

--
-- Name: relevant_locations; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE relevant_locations (
    location_name text,
    location_code text
);


ALTER TABLE relevant_locations OWNER TO openmakerpsql;

--
-- Name: topic_facebook_page; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE topic_facebook_page (
    topic_id bigint,
    facebook_page_id text
);


ALTER TABLE topic_facebook_page OWNER TO openmakerpsql;

--
-- Name: topic_id_seq; Type: SEQUENCE; Schema: public; Owner: openmakerpsql
--

CREATE SEQUENCE topic_id_seq
    START WITH 40
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE topic_id_seq OWNER TO openmakerpsql;

--
-- Name: topic_subreddit; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE topic_subreddit (
    topic_id bigint,
    subreddit text
);


ALTER TABLE topic_subreddit OWNER TO openmakerpsql;

--
-- Name: topics; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE topics (
    topic_id bigint DEFAULT nextval('topic_id_seq'::regclass) NOT NULL,
    topic_name text,
    topic_description text,
    keywords text,
    languages text,
    creation_time text DEFAULT ('now'::text)::date,
    keyword_limit integer,
    last_tweet_date date,
    is_running boolean DEFAULT true,
    is_publish boolean DEFAULT false
);


ALTER TABLE topics OWNER TO openmakerpsql;

--
-- Name: user_audience_rating; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_audience_rating (
    user_id bigint,
    audience_id bigint,
    topic_id bigint,
    rating double precision
);


ALTER TABLE user_audience_rating OWNER TO openmakerpsql;

--
-- Name: user_bookmark; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_bookmark (
    user_id bigint,
    bookmark_link_id bigint
);


ALTER TABLE user_bookmark OWNER TO openmakerpsql;

--
-- Name: user_domain; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_domain (
    domain text,
    user_id bigint
);


ALTER TABLE user_domain OWNER TO openmakerpsql;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: openmakerpsql
--

CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_id_seq OWNER TO openmakerpsql;

--
-- Name: user_news_rating; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_news_rating (
    user_id bigint,
    news_id bigint,
    topic_id bigint,
    rating double precision
);


ALTER TABLE user_news_rating OWNER TO openmakerpsql;

--
-- Name: user_topic; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_topic (
    user_id bigint,
    topic_id bigint
);


ALTER TABLE user_topic OWNER TO openmakerpsql;

--
-- Name: user_topic_subscribe; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_topic_subscribe (
    user_id bigint,
    topic_id bigint
);


ALTER TABLE user_topic_subscribe OWNER TO openmakerpsql;

--
-- Name: user_tweet; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_tweet (
    user_id bigint,
    topic_id bigint,
    tweet_id bigint
);


ALTER TABLE user_tweet OWNER TO openmakerpsql;

--
-- Name: user_twitter; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE user_twitter (
    user_id bigint,
    access_token text,
    access_token_secret text,
    profile_image_url text,
    user_name text,
    screen_name text
);


ALTER TABLE user_twitter OWNER TO openmakerpsql;

--
-- Name: users; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE users (
    user_id bigint DEFAULT nextval('user_id_seq'::regclass) NOT NULL,
    username text,
    password text,
    alertlimit integer,
    current_topic_id integer,
    country_code text,
    current_location text,
    twitter_access_token text,
    twitter_access_secret text
);


ALTER TABLE users OWNER TO openmakerpsql;

--
-- Name: users_and_topics; Type: VIEW; Schema: public; Owner: openmakerpsql
--

CREATE VIEW users_and_topics AS
 SELECT user_topic.user_id,
    user_topic.topic_id
   FROM user_topic
UNION
 SELECT user_topic_subscribe.user_id,
    user_topic_subscribe.topic_id
   FROM user_topic_subscribe;


ALTER TABLE users_and_topics OWNER TO openmakerpsql;

--
-- Name: VIEW users_and_topics; Type: COMMENT; Schema: public; Owner: openmakerpsql
--

COMMENT ON VIEW users_and_topics IS 'users and topics (including subscribed ones)';


--
-- Name: added_influencers added_inf_pk; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY added_influencers
    ADD CONSTRAINT added_inf_pk PRIMARY KEY (topic_id, location);


--
-- Name: audience_parameters audience_id; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY audience_parameters
    ADD CONSTRAINT audience_id PRIMARY KEY (topic_id, location);


--
-- Name: hidden_events hidden_events_pkey; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY hidden_events
    ADD CONSTRAINT hidden_events_pkey PRIMARY KEY (topic_id, event_link);


--
-- Name: hidden_influencers hidden_influencers_pkey; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY hidden_influencers
    ADD CONSTRAINT hidden_influencers_pkey PRIMARY KEY (topic_id, country_code, influencer_id);


--
-- Name: influencer_parameters id; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY influencer_parameters
    ADD CONSTRAINT id PRIMARY KEY (topic_id, location);


--
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (topic_id);


--
-- Name: audience_samples_last_executed unique_audience; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY audience_samples_last_executed
    ADD CONSTRAINT unique_audience PRIMARY KEY (topic_id, location);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- PostgreSQL database dump complete
--

