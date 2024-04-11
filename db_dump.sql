--
-- PostgreSQL database dump
--

-- Dumped from database version 15.6 (Debian 15.6-1.pgdg120+2)
-- Dumped by pg_dump version 15.6 (Debian 15.6-1.pgdg120+2)

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: crawl_item; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.crawl_item (
    id integer NOT NULL,
    link character varying(2048) NOT NULL,
    pscore numeric(8,7),
    lscore numeric(8,7),
    time_queued timestamp with time zone,
    time_crawled timestamp with time zone,
    batch_id integer
);


ALTER TABLE public.crawl_item OWNER TO postgres;

--
-- Name: crawl_item_batch; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.crawl_item_batch (
    id integer NOT NULL,
    time_batched timestamp with time zone
);


ALTER TABLE public.crawl_item_batch OWNER TO postgres;

--
-- Name: crawl_item_batch_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.crawl_item_batch_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.crawl_item_batch_id_seq OWNER TO postgres;

--
-- Name: crawl_item_batch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.crawl_item_batch_id_seq OWNED BY public.crawl_item_batch.id;


--
-- Name: crawl_item_tag; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.crawl_item_tag (
    item_id integer NOT NULL,
    tag character varying(128) NOT NULL
);


ALTER TABLE public.crawl_item_tag OWNER TO postgres;

--
-- Name: crawlitem_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.crawlitem_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.crawlitem_id_seq OWNER TO postgres;

--
-- Name: crawlitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.crawlitem_id_seq OWNED BY public.crawl_item.id;


--
-- Name: view_crawl_item_summary; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.view_crawl_item_summary AS
SELECT
    NULL::character varying(2048) AS link,
    NULL::numeric(8,7) AS pscore,
    NULL::timestamp with time zone AS time_crawled,
    NULL::text AS tags;


ALTER TABLE public.view_crawl_item_summary OWNER TO postgres;

--
-- Name: view_crawl_fld; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.view_crawl_fld AS
 SELECT DISTINCT "substring"((view_crawl_item_summary.link)::text, '(?:https?://)?(?:www\.)?([^/]*)'::text) AS fld
   FROM public.view_crawl_item_summary;


ALTER TABLE public.view_crawl_fld OWNER TO postgres;

--
-- Name: crawl_item id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item ALTER COLUMN id SET DEFAULT nextval('public.crawlitem_id_seq'::regclass);


--
-- Name: crawl_item_batch id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item_batch ALTER COLUMN id SET DEFAULT nextval('public.crawl_item_batch_id_seq'::regclass);


--
-- Name: crawl_item_batch crawl_item_batch_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item_batch
    ADD CONSTRAINT crawl_item_batch_pkey PRIMARY KEY (id);


--
-- Name: crawl_item crawl_item_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item
    ADD CONSTRAINT crawl_item_pkey PRIMARY KEY (id);


--
-- Name: crawl_item_tag crawl_item_tag_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item_tag
    ADD CONSTRAINT crawl_item_tag_pkey PRIMARY KEY (item_id, tag);


--
-- Name: view_crawl_item_summary _RETURN; Type: RULE; Schema: public; Owner: postgres
--

CREATE OR REPLACE VIEW public.view_crawl_item_summary AS
 SELECT i.link,
    i.pscore,
    i.time_crawled,
    string_agg((t.tag)::text, ','::text) AS tags
   FROM ((public.crawl_item i
     LEFT JOIN public.crawl_item_batch b ON ((i.batch_id = b.id)))
     LEFT JOIN public.crawl_item_tag t ON ((i.id = t.item_id)))
  GROUP BY i.id;


--
-- Name: crawl_item crawl_item_batch_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item
    ADD CONSTRAINT crawl_item_batch_id_fk FOREIGN KEY (batch_id) REFERENCES public.crawl_item_batch(id) NOT VALID;


--
-- Name: crawl_item_tag crawl_item_tag_item_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.crawl_item_tag
    ADD CONSTRAINT crawl_item_tag_item_id_fk FOREIGN KEY (item_id) REFERENCES public.crawl_item(id);


--
-- PostgreSQL database dump complete
--