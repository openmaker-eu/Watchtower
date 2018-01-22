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

SET search_path = public, pg_catalog;

ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
ALTER TABLE ONLY public.topics DROP CONSTRAINT topics_pkey;
DROP VIEW public.users_and_topics;
DROP TABLE public.users;
DROP TABLE public.user_topic_subscribe;
DROP TABLE public.user_topic;
DROP TABLE public.user_news_rating;
DROP SEQUENCE public.user_id_seq;
DROP TABLE public.user_domain;
DROP TABLE public.user_bookmark;
DROP TABLE public.user_audience_rating;
DROP TABLE public.topics;
DROP TABLE public.topic_subreddit;
DROP SEQUENCE public.topic_id_seq;
DROP TABLE public.topic_facebook_page;
DROP TABLE public.signal_strenghts;
DROP TABLE public.relevant_locations;
DROP TABLE public.country_code;
DROP TABLE public.archived_topics;
DROP EXTENSION adminpack;
DROP EXTENSION plpgsql;
DROP SCHEMA public;
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


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
-- Name: country_code; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE country_code (
    country_name text,
    country_code text
);


ALTER TABLE country_code OWNER TO openmakerpsql;

--
-- Name: relevant_locations; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE relevant_locations (
    location_name text,
    location_code text
);


ALTER TABLE relevant_locations OWNER TO openmakerpsql;

--
-- Name: signal_strenghts; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE signal_strenghts (
    topic_id bigint,
    location text,
    signal_strength bigint DEFAULT 3
);


ALTER TABLE signal_strenghts OWNER TO openmakerpsql;

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
-- Name: users; Type: TABLE; Schema: public; Owner: openmakerpsql
--

CREATE TABLE users (
    user_id bigint DEFAULT nextval('user_id_seq'::regclass) NOT NULL,
    username text,
    password text,
    alertlimit integer,
    current_topic_id integer,
    country_code text,
    current_location text
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
-- Name: topics topics_pkey; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY topics
    ADD CONSTRAINT topics_pkey PRIMARY KEY (topic_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: openmakerpsql
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

