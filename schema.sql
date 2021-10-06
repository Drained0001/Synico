SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE SCHEMA public;

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

CREATE TABLE public.blacklist (
    guild bigint,
    "user" bigint
);

CREATE TABLE public.guilds (
    guild bigint NOT NULL,
    prefix text,
    log bigint,
    timezone text,
    mute bigint,
    admin bigint,
    mod bigint,
    "join" bigint,
    leave bigint,
    welcome text,
    goodbye text,
    twitter bigint,
    tweet text
);

CREATE TABLE public.mutes (
    guild bigint,
    "user" bigint,
    ends timestamp with time zone,
    starts timestamp with time zone,
    reason text
);

CREATE TABLE public.reminders (
    guild bigint,
    "user" bigint,
    "end" timestamp with time zone,
    reminder text,
    channel bigint,
    created timestamp with time zone,
    reminds bigint
);

CREATE TABLE public.tags (
    guild bigint,
    "user" bigint,
    created timestamp with time zone,
    used bigint,
    content text,
    tag text
);

CREATE TABLE public.tempbans (
    guild bigint,
    "user" bigint,
    "end" timestamp with time zone
);

CREATE TABLE public.twitch (
    guild bigint,
    channel bigint,
    streamer text,
    live boolean,
    "message" text,
    title text,
    notified boolean
);

CREATE TABLE public.twitter (
    guild bigint,
    "user" bigint
);


CREATE TABLE public.warns (
    guild bigint,
    "user" bigint,
    author bigint,
    warn text,
    warned bigint,
    created timestamp with time zone
);