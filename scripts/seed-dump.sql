--
-- PostgreSQL database dump
--

\restrict BuRBpJr0XfYjmzMngiZfMPHJVu0rtQ9rSahBeGWUVGfUxduFJLEJZfZCa5sxjhS

-- Dumped from database version 16.14
-- Dumped by pg_dump version 16.14

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: instagram_posts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.instagram_posts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    stop_id character varying(100) NOT NULL,
    instagram_id character varying(100) NOT NULL,
    shortcode character varying(100) NOT NULL,
    media_url character varying(500) NOT NULL,
    caption text DEFAULT ''::text NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: regions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.regions (
    iata_code character varying(10) NOT NULL,
    name character varying(255) NOT NULL,
    airport_name character varying(500) NOT NULL,
    country character varying(255) NOT NULL,
    lat numeric(10,7) NOT NULL,
    lng numeric(10,7) NOT NULL
);


--
-- Name: stops; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.stops (
    id character varying(100) NOT NULL,
    trip_id character varying(100) NOT NULL,
    date date NOT NULL,
    location character varying(500) NOT NULL,
    lat numeric(10,7),
    lng numeric(10,7),
    status character varying(20) NOT NULL,
    region_code character varying(10),
    post_type character varying(20) NOT NULL,
    caption text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_stops_post_type CHECK (((post_type)::text = ANY ((ARRAY['instagram'::character varying, 'substack'::character varying, 'planned'::character varying])::text[]))),
    CONSTRAINT ck_stops_status CHECK (((status)::text = ANY ((ARRAY['visited'::character varying, 'planned'::character varying])::text[])))
);


--
-- Name: substack_posts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.substack_posts (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    stop_id character varying(100),
    substack_id character varying(500) NOT NULL,
    title character varying(500) NOT NULL,
    subtitle text,
    body text NOT NULL,
    published_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: trips; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trips (
    id character varying(100) NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
76fd9e24de78
\.


--
-- Data for Name: instagram_posts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.instagram_posts (id, stop_id, instagram_id, shortcode, media_url, caption, "timestamp", created_at) FROM stdin;
d98731cf-2c4f-4b2c-899d-77a32391ebd7	23	18001223977200451	BxZ6Y-Zh1jC	/media/23.jpg	700 steps up a vertical monolith. They thoughtfully built a second set of stairs so that the descending traffic wouldn't demotivate the upward climbers	2019-05-13 00:00:00+00	2026-05-29 02:11:18.929346+00
9b7adbfe-5f66-47d8-91e6-afa860306b34	22	17954371129278385	BxaGGFohpKw	/media/22.jpg	Only got to overlap a couple days with my bro. Parents baton is yours now, good luck!	2019-05-13 00:00:00+00	2026-05-29 02:11:18.929346+00
2f7ac1d0-3028-45ca-b4b9-f75491333a13	21	18048308524101320	BxbL5AoBPfV	/media/21.jpg	That is some admirably succinct visual symbolgy	2019-05-14 00:00:00+00	2026-05-29 02:11:18.929346+00
d901adef-2213-4b59-b494-8bf0916736b3	20	18049782940100653	BxbM1kQBraE	/media/20.jpg	Mom being casually fabulous	2019-05-14 00:00:00+00	2026-05-29 02:11:18.929346+00
f5ebe758-9973-4f01-b771-328e06fd7e5c	19	18023902987174262	BxbPatKBeTk	/media/19.jpg	Botched translation or profound truth, I genuinely cannot say.	2019-05-14 00:00:00+00	2026-05-29 02:11:18.929346+00
1ec341a6-1498-4fd6-b68d-e16d498b0c10	18	17927644093321881	B2paAgIh_Pv	/media/18.jpg	Thanks for the memories 540. Onward and upward!	2019-09-20 00:00:00+00	2026-05-29 02:11:18.929346+00
31152266-6fcd-409b-87ca-21100337cdec	17	18104787694036950	B3T7cNwjiCd	/media/17.jpg	Soft serve and plywood. Our pilgrimage to the OG temple of Swedish culture is truly complete.	2019-10-07 00:00:00+00	2026-05-29 02:11:18.929346+00
e469e244-7cda-42e7-88ce-f055ff1845a0	16	18078166936187059	B4BrPSyDgSn	/media/16.jpg	Courtesy of the most passionate volunteer iphone photographer ever. Really brought the levity to an evening with adolf	2019-10-25 00:00:00+00	2026-05-29 02:11:18.929346+00
5ac92156-2e99-40b7-ad01-da86104b2255	15	17860734715562956	B4Y42VQDVCO	/media/15.jpg	Feliz Dia de los Muertos!	2019-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
4bfd2ba6-44c1-4c0a-9204-3c71d0f4347b	14	18112431550007109	B4akEkeBpI_	/media/14.jpg	Enjoy your coffee, Cthulhu watches over you	2019-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
9335d57e-c453-4bfb-b9e9-a6d75f41b26a	13	18079018615093695	B4eJItyjLl4	/media/13.jpg	The magical floating stacks blur a library visit with a trip through the Matrix	2019-11-05 00:00:00+00	2026-05-29 02:11:18.929346+00
7de31ec4-d175-4063-8d8e-360de2061193	12	18037151035217175	B4gp4YxDDJP	/media/12.jpg	In Mexico, Beijing duck roasts with all the fiery drama of a ritual fit for Montezuma	2019-11-06 00:00:00+00	2026-05-29 02:11:18.929346+00
2c9fa73c-35d5-4a3a-98b3-35113bb6b446	11	18063726055196282	B4jSd1mDW2H	/media/11.jpg	Sometimes, someone hands you a poncho and some props, and all your thoughtful cultural appreciation goes out the window	2019-11-07 00:00:00+00	2026-05-29 02:11:18.929346+00
0f6370eb-35d8-446a-9fd5-8bf177b1bbef	10	18079533163086659	B4lJJw-DDKt	/media/10.jpg	On top of everything else, an exhibit of Asian ivories more spectacular than anything I've seen in China or Taiwan. This city should be said in the same breath as London or LA	2019-11-07 00:00:00+00	2026-05-29 02:11:18.929346+00
65ea0630-9063-42e3-8320-e9f14230c101	9	18069544879160606	B4ofJptjTsA	/media/9.jpg	High brow vandalism	2019-11-09 00:00:00+00	2026-05-29 02:11:18.929346+00
6a2165f6-9308-4a58-8fc7-0feb463b28ef	8	17858594914588653	B4rDVUQjQby	/media/8.jpg	Fun fact from Lucha arena: Spanish for little person is "enano"	2019-11-10 00:00:00+00	2026-05-29 02:11:18.929346+00
2bc972a5-84b5-44b3-a9e1-5b4f68a775eb	7	18132090181071254	B_c4XQiDMy3	/media/7.jpg	Essential	2020-04-26 00:00:00+00	2026-05-29 02:11:18.929346+00
594cf5ca-a44f-465d-b329-64481674806a	6	18055230940493455	C3dp3LnPeQ1	/media/6.jpg	Where even a cooking school is beautiful.	2024-02-17 00:00:00+00	2026-05-29 02:11:18.929346+00
29aa5bb3-6222-474a-9e39-313e243a38e2	5	17999829707411635	C3dqXOPvNKQ	/media/5.jpg	Some places can find the joy in anything	2024-02-17 00:00:00+00	2026-05-29 02:11:18.929346+00
8f41c08c-c5ae-4d01-bca1-7ddab8db3cd6	4	17987675498404883	C3g2CZGMyYy	/media/4.jpg	Cthulhu in tree form. Reaching through the millennia.	2024-02-19 00:00:00+00	2026-05-29 02:11:18.929346+00
ffcbfb6f-f245-43b5-8870-e48c24d11b64	3	18025886506939141	C3g2YOHMR-r	/media/3.jpg	"For your safety, do not approach the abyss."	2024-02-19 00:00:00+00	2026-05-29 02:11:18.929346+00
36fd3a9a-c063-4eee-a55a-5db061aff510	2	17996821559305682	C3jJxkzMGvi	/media/2.jpg	Never a wrong time or place for hot chocolate	2024-02-20 00:00:00+00	2026-05-29 02:11:18.929346+00
001406fb-34ee-467c-83f7-e9a970f3029f	1	17990443415376031	C3jXFRlMZoJ	/media/1.jpg	East meets Southwest	2024-02-20 00:00:00+00	2026-05-29 02:11:18.929346+00
0cfc4f20-6063-49e3-9267-2ebea808e980	es2015-ig-74	17857579060038514	BGsJV0PlnJc	/media/74.jpg	All we really needed #ourearthsandwich	2016-06-15 00:00:00+00	2026-05-29 02:11:18.929346+00
ee4ee44b-cde7-4908-b8e3-931813b06a25	es2015-ig-75	17857643959054487	BGsB0KRFnGC	/media/75.jpg	The Czechs are the original Bohemians, and their hipster descendants flourish in the bosom of the earth mother	2016-06-15 00:00:00+00	2026-05-29 02:11:18.929346+00
64dea50f-d65f-42a8-9632-8a589d56a745	es2015-ig-76	17848468447124117	BGo9Dl7lnCR	/media/76.jpg	The decoratively arranged remains of 40,000 souls make a haunting hell-scape, but the company of field-tripping school children helps fortify the courage	2016-06-14 00:00:00+00	2026-05-29 02:11:18.929346+00
24f49101-b314-4536-bde0-d340abf8c4a7	es2015-ig-77	17849722585075649	BGh-AxAFnLs	/media/77.jpg	I wonder how many people have dropped their phone taking this exact picture	2016-06-11 00:00:00+00	2026-05-29 02:11:18.929346+00
663bcce0-171e-41c3-a6a6-808ac4977695	es2015-ig-78	17856928993029128	BGh9bBSlnKI	/media/78.jpg	Winter is coming	2016-06-11 00:00:00+00	2026-05-29 02:11:18.929346+00
49b3d5af-eb0d-426b-8ebd-dabf11311238	es2015-ig-79	17848276447096151	BGbP9N6FnGa	/media/79.jpg	I thought I caught an opera singer on a surreptitious cigarette break, turns out it was just a flamboyant ticket scalper	2016-06-09 00:00:00+00	2026-05-29 02:11:18.929346+00
a8040906-1d1a-4c11-80ef-acb9a01420ea	es2015-ig-81	17850873469065313	BGQCWNplnGb	/media/81.jpg	This bridge is where WWI began. Prince Franz Ferdinand of Austria was assassinated here by a teenager, setting in motion the events that ended the age of empires and created almost all the modern political nations and boundaries as we know them.	2016-06-04 00:00:00+00	2026-05-29 02:11:18.929346+00
a1bf0461-0c2d-45f4-ae2a-039bd6f2cd96	es2015-ig-82	17848040506108168	BGKaWx0lnLO	/media/82.jpg	Nothing lasts forever, except for stone arches. It is now on my life to-do's to build at least one on this earth	2016-06-02 00:00:00+00	2026-05-29 02:11:18.929346+00
2e11fb36-b858-4092-a48d-cf8083255dee	es2015-ig-83	17848712908076832	BGHLPwKlnF4	/media/83.jpg	Ah, romance...	2016-06-01 00:00:00+00	2026-05-29 02:11:18.929346+00
60515162-709b-4291-84c5-4d2dfcec3316	es2015-ig-84	17857211344056932	BGGiHiblnN1	/media/84.jpg	I had thought there was nothing more lovely in life than having a beer by the sea, then a pirate ship showed up	2016-06-01 00:00:00+00	2026-05-29 02:11:18.929346+00
406d70cc-e6d8-4407-956f-e3c9a4568e7f	es2015-ig-85	17847844552091932	BF92a0iFnBw	/media/85.jpg	Really hoping I get to throw a Molotov or flip a car before we leave Greece. That's a centaur btw.	2016-05-28 00:00:00+00	2026-05-29 02:11:18.929346+00
a0a33e6b-3ff2-48f9-9bb8-c1eb0de584f6	es2015-ig-86	17847802783089117	BF3tRL3lnLE	/media/86.jpg	Welcome to Greece	2016-05-26 00:00:00+00	2026-05-29 02:11:18.929346+00
d3f1d50b-5aa4-4044-bb2a-69fadae91a75	es2015-ig-87	17857721230026150	BF2-KC3FnEJ	/media/87.jpg	If we ever achieve world peace through global cultural homogenization, it will be the Selfie that blazes the path	2016-05-26 00:00:00+00	2026-05-29 02:11:18.929346+00
19c2c4db-5f86-469d-8a8e-00947c409d70	es2015-ig-88	17856992914054703	BF273hSFnAq	/media/88.jpg	Turkey spells borrowed words like a precocious three-year-old. This has been a continuous source of joy for us and a reminder of how arbitrary English's phonetic rules are.	2016-05-26 00:00:00+00	2026-05-29 02:11:18.929346+00
fc76981d-ff82-4ca8-a48d-b31422b231a0	es2015-ig-89	17847889960094001	BF1x3C7FnHe	/media/89.jpg	Bold, very bold.	2016-05-25 00:00:00+00	2026-05-29 02:11:18.929346+00
ec6c3741-0cd7-4f26-b918-a2d88268e59d	es2015-ig-91	17847895447117568	BFzY7ggFnN-	/media/91.jpg	Baklava is just a gateway to the hard stuff	2016-05-24 00:00:00+00	2026-05-29 02:11:18.929346+00
df561fc9-c53a-4d09-a026-49ccf1e5b432	es2015-ig-92	17856791818001514	BFtSJJYFnMT	/media/92.jpg	Some things we know about Turkey: 1. They love their country 2. Phenomenal horticulturalists	2016-05-22 00:00:00+00	2026-05-29 02:11:18.929346+00
6d8a68f5-24d1-4f93-8e10-8a30ac0ffdc6	es2015-ig-93	17856539566028875	BFtQVuDFnH_	/media/93.jpg	Any journey in Turkey exceeding 90 minutes requires at least one stop for a cup of apple tea and a thorough cleaning of the vehicle. We are not barbarians.	2016-05-22 00:00:00+00	2026-05-29 02:11:18.929346+00
39be214e-c7a0-4974-a803-9e3c99670ac5	es2015-ig-94	17855702398024402	BFk8lUclnF0	/media/94.jpg	I wonder if it's a rough neighborhood	2016-05-19 00:00:00+00	2026-05-29 02:11:18.929346+00
c6bfc2ba-725f-4a5c-bbda-0629a51e9fe7	es2015-ig-95	17857176352062063	BFk67c3FnDY	/media/95.jpg	Troglodyte castle	2016-05-19 00:00:00+00	2026-05-29 02:11:18.929346+00
d4679873-3689-4a53-9e9d-0dd2145029be	es2015-ig-96	17857049914017425	BFgrsuwlnEz	/media/96.jpg	Put a helmet on her and Wela has no fear, taunting the 7th story of a canyon-side dwelling like a Eyrie sky cell	2016-05-17 00:00:00+00	2026-05-29 02:11:18.929346+00
84304a3b-52f1-4000-8361-5d6eb94181e2	es2015-ig-97	17856796867025882	BFgoDnNlnLu	/media/97.jpg	Jordan had some crazy rocks, but Turkey is giving it a run	2016-05-17 00:00:00+00	2026-05-29 02:11:18.929346+00
c7b29725-5c68-4f10-b133-22d753228394	es2015-ig-98	17850667522064656	BFgmAFmFnG-	/media/98.jpg	This ventilation shaft descends 85 meters into a Tolkien-esque underground city that could once shelter 30,000 people. Not a very photogenic place but mind-blowing	2016-05-17 00:00:00+00	2026-05-29 02:11:18.929346+00
12fffbd3-d6ac-467f-bf26-bf3b3defe648	es2015-ig-99	17850333787068558	BFUFgmklnPJ	/media/99.jpg	Saying hello to the locals	2016-05-12 00:00:00+00	2026-05-29 02:11:18.929346+00
20963201-e43f-49ac-afd8-fe0685582699	es2015-ig-102	17848078849076509	BE_gbGSFnNl	/media/102.jpg	In commemoration for Ted Cruz's valiant last stand, L'chaim.	2016-05-04 00:00:00+00	2026-05-29 02:11:18.929346+00
e3a695df-0959-473f-b54d-2e043edf4191	es2015-ig-103	17847146626080468	BE_eyHyFnJQ	/media/103.jpg	A rebellious Israeli teenager chose to express his angst and deface the boardwalk by drawing this kitty, shittily.	2016-05-04 00:00:00+00	2026-05-29 02:11:18.929346+00
2a944732-df87-4f3d-b886-3610a413bded	es2015-ig-104	17847885544078535	BE31dU0lnAU	/media/104.jpg	This undercover IDF officer and I are about equally skilled at being inconspicuos. #nailedit	2016-05-01 00:00:00+00	2026-05-29 02:11:18.929346+00
1ecce4b5-6aee-4319-b8c5-78c0b229a24a	es2015-ig-105	17847878359075335	BExyAP_lnAP	/media/105.jpg	Just like in the movie!	2016-04-29 00:00:00+00	2026-05-29 02:11:18.929346+00
a3597fc4-95c1-4053-a397-78bf4089fe5d	es2015-ig-106	17855472355029527	BEohmBYFnE8	/media/106.jpg	Grumpy grumps	2016-04-25 00:00:00+00	2026-05-29 02:11:18.929346+00
b2ae2893-70c0-4e16-9732-e8c224383f40	es2015-ig-107	17855354293025101	BEmGJ16lnJq	/media/107.jpg	OSHA is for pussies	2016-04-24 00:00:00+00	2026-05-29 02:11:18.929346+00
6318b0f4-9ee9-424b-b7be-025b0648251f	es2015-ig-108	17849620600070079	BEmEvnOFnGN	/media/108.jpg	Eat hearty my friend, tonight we dine in hell!	2016-04-24 00:00:00+00	2026-05-29 02:11:18.929346+00
37fe45b8-c9da-4fb8-b08d-509328139089	es2015-ig-109	17855365486032193	BEl_V0cFnHz	/media/109.jpg	Fun with buoyancy at 34% salinity. Don't let it touch your eyes or mouth or you will start to die immediately.	2016-04-24 00:00:00+00	2026-05-29 02:11:18.929346+00
30b5eacd-7ae5-40ff-8d12-efdac229c222	es2015-ig-110	17846940433109582	BEi0g9pFnGq	/media/110.jpg	American cheese whiz, Mexican themed, manufactured in Greece, sold in Jordan	2016-04-23 00:00:00+00	2026-05-29 02:11:18.929346+00
3fb95282-4b39-49d8-bef8-ea72aad9a2b9	es2015-ig-111	17846863882080189	BEhEUy4FnGs	/media/111.jpg	Grazing in a lost city	2016-04-22 00:00:00+00	2026-05-29 02:11:18.929346+00
b3d3ec5c-5e9c-438e-a90b-5bda4730941b	es2015-ig-112	17856451831033618	BEg8C31lnGU	/media/112.jpg	I like Jordan's version of the Middle East. Same same, but different, but still same!	2016-04-22 00:00:00+00	2026-05-29 02:11:18.929346+00
64d09c86-c8b0-4d86-afff-58688c3ed161	es2015-ig-113	17856147592043504	BETC9sOFnEQ	/media/113.jpg	It's comforting to know that there were also pudgy pharaohs	2016-04-17 00:00:00+00	2026-05-29 02:11:18.929346+00
1a379d21-8d7b-4930-87d1-b7043ef4aa8b	es2015-ig-114	17855970868059237	BEImhc8FnEq	/media/114.jpg	We just got scolded for hanging out our laundry line at a classy resort. It's nice to take a break from hostel deprivations, but damned if I'm paying hotel laundry prices ever.	2016-04-13 00:00:00+00	2026-05-29 02:11:18.929346+00
6db15f2a-15b6-479c-b131-c68a1949e2fc	es2015-ig-115	17847358624074933	BEGsqnzFnIv	/media/115.jpg	The sailors on our river cruise had some pretty hardcore Pirates of the Caribbean moves	2016-04-12 00:00:00+00	2026-05-29 02:11:18.929346+00
62b47c24-236b-43d3-96f0-afdc2b90bf1c	es2015-ig-116	17846595700098605	BD_AUkzFnHY	/media/116.jpg	#thefifthelement	2016-04-09 00:00:00+00	2026-05-29 02:11:18.929346+00
535f4de0-0cfb-4b5d-85a8-4959b9cf608c	es2015-ig-117	17855473153043414	BD7MxxtlnG9	/media/117.jpg	Fun with multicuturalism	2016-04-08 00:00:00+00	2026-05-29 02:11:18.929346+00
2d4835d4-6c59-41cf-ba9a-5bd2cf409670	es2015-ig-118	17847258136073666	BD6QLYKFnKi	/media/118.jpg	Hope and resourcefulness in Mansheya Nasir, minority Christian neighborhood where all of Cairo's garbage is collected and processed by manual pickers	2016-04-07 00:00:00+00	2026-05-29 02:11:18.929346+00
2f13d4d8-1a50-4f0d-bbc7-79085369e931	es2015-ig-119	17846494801088235	BD2h3_ulnPC	/media/119.jpg	Mosques of Cairo invite casual loungers to relax in cool airy halls among the more devout	2016-04-06 00:00:00+00	2026-05-29 02:11:18.929346+00
4ef1d182-4809-4276-9ad0-2856adf2b414	es2015-ig-120	17846523664104920	BD1YMKvFnEu	/media/120.jpg	Pretty colors	2016-04-05 00:00:00+00	2026-05-29 02:11:18.929346+00
38ace0d0-912a-4a20-9f5e-9a23be8fa4c1	es2015-ig-121	17857653982058092	BDzs6dvlnHv	/media/121.jpg	Those ancients knew how to party	2016-04-05 00:00:00+00	2026-05-29 02:11:18.929346+00
feeb9424-524d-4767-9cc6-93e33860b236	es2015-ig-122	17856523312031162	BDyfOxzFnAi	/media/122.jpg	Welcome to Egypt	2016-04-04 00:00:00+00	2026-05-29 02:11:18.929346+00
10ab8ecf-6670-4a08-9ce0-950fcaff2b67	es2015-ig-123	17856054124063959	BDyec8OFnPA	/media/123.jpg	A young family teaches me how to cross streets in Cairo	2016-04-04 00:00:00+00	2026-05-29 02:11:18.929346+00
e39563cc-02ff-4457-be6c-249d4155b322	es2015-ig-124	17846373844112638	BDvcYJ_lnH7	/media/124.jpg	Waterfall so majestic it has a rainbow boner	2016-04-03 00:00:00+00	2026-05-29 02:11:18.929346+00
caa1d3a5-c7cc-4bcf-bcb8-92d5cbf9b7f7	es2015-ig-125	17846374750083276	BDuP1hoFnKN	/media/125.jpg	Beware of dismemberment by squid	2016-04-03 00:00:00+00	2026-05-29 02:11:18.929346+00
9c58386b-0d65-495a-9580-262dfc248775	es2015-ig-126	17846360998118486	BDuPbYWFnJg	/media/126.jpg	Mighty Atlas	2016-04-03 00:00:00+00	2026-05-29 02:11:18.929346+00
6ba26c47-52ad-424d-bdd4-b822ef502804	es2015-ig-127	17849339593069444	BDss2u6FnN4	/media/127.jpg	Up up and away! Nice flying dad!	2016-04-02 00:00:00+00	2026-05-29 02:11:18.929346+00
8d9f8d08-b514-4935-95a8-febf76942890	es2015-ig-128	17855414146032158	BDsozuFFnFe	/media/128.jpg	Protected from jelly fish and enemy ninjas	2016-04-02 00:00:00+00	2026-05-29 02:11:18.929346+00
43e8b62f-ab26-47d6-acc5-8e74686cfc5d	es2015-ig-129	17856258676008841	BDiXi4hFnLn	/media/129.jpg	The taste of victory is sweet	2016-03-29 00:00:00+00	2026-05-29 02:11:18.929346+00
c428625e-e075-43d3-ab0f-3b10c0af9483	es2015-ig-130	17857902703051080	BDiVNA2lnGx	/media/130.jpg	Sunrise at Sydney's beaches. Aussies play hard, 6:30am on a weekday and folks are out surfing	2016-03-29 00:00:00+00	2026-05-29 02:11:18.929346+00
73a9b29d-0a54-4e87-ab8c-d5dec5753d23	es2015-ig-131	17846289007103049	BDiT1KdlnDv	/media/131.jpg	Uncertain if this wallaby is having an much fun as us... Welcome to Australia bro!	2016-03-29 00:00:00+00	2026-05-29 02:11:18.929346+00
1083581c-3517-4b79-aa88-dbfa93afa87c	es2015-ig-132	17847023473078403	BDgy1jjlnMz	/media/132.jpg	Helmet = safe	2016-03-28 00:00:00+00	2026-05-29 02:11:18.929346+00
d49437d2-a7e2-4c3b-9959-b46bde2ac8eb	es2015-ig-133	17855077864035983	BDapWGnlnKw	/media/133.jpg	Practicing for the real deal	2016-03-26 00:00:00+00	2026-05-29 02:11:18.929346+00
4adb9147-d998-49f2-9d65-40ceaa4addaa	es2015-ig-134	17854202461003647	BDOus1_FnGc	/media/134.jpg	That about sums up my tenuous connection to the real world	2016-03-21 00:00:00+00	2026-05-29 02:11:18.929346+00
d790470d-2bfd-43dc-b5bb-4614a61cc3e3	es2015-ig-135	17854878133050032	BDIIek_FnEA	/media/135.jpg	I've never seen such a perfect caricature of an apple. All its missing is a cartoon worm wearing reading glasses sticking out the side	2016-03-19 00:00:00+00	2026-05-29 02:11:18.929346+00
51071df9-2295-444d-ad85-800357ebfc98	es2015-ig-136	17845824817081810	BDG1exzFnJH	/media/136.jpg	Second biggest pigeon species in the world, tiniest head	2016-03-18 00:00:00+00	2026-05-29 02:11:18.929346+00
878195fd-f8b3-414e-995f-2419b61e07b0	es2015-ig-137	17855552305037425	BDDGZH5lnAv	/media/137.jpg	Airplane mode	2016-03-17 00:00:00+00	2026-05-29 02:11:18.929346+00
c67dc734-7260-4eea-ac96-26be1d41e211	es2015-ig-140	17845801633083438	BC9ILeElnIA	/media/140.jpg	Jabba the Hut and his bodyguards	2016-03-15 00:00:00+00	2026-05-29 02:11:18.929346+00
929f82a1-26fb-4408-a76a-5754882bb6c0	es2015-ig-141	17845727443102801	BC9GHZVFnE9	/media/141.jpg	No predators on this island so the sheep here are beyond indifferent	2016-03-15 00:00:00+00	2026-05-29 02:11:18.929346+00
2617cf6c-7f60-4c7b-a6a1-6ab2bae4698e	es2015-ig-142	17846285596078879	BC9FzR0FnEg	/media/142.jpg	Adventure awaits	2016-03-15 00:00:00+00	2026-05-29 02:11:18.929346+00
a49d5b7e-b89c-4f4a-8115-293a4e6157fd	es2015-ig-182	17854310356049606	BAMw0balnBU	/media/182.jpg	It's not called the Death Road for nothin'	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
5440ebec-a267-45dc-ad2e-9f7d9562e549	es2015-ig-143	17845524184128569	BC9CveQFnPm	/media/143.jpg	Serenely peaceful even though it looks like the vox of a badass dub step	2016-03-15 00:00:00+00	2026-05-29 02:11:18.929346+00
43725ef7-649c-49ec-ada4-8f96b4137daa	es2015-ig-144	17854964749028233	BC9BeL3FnM-	/media/144.jpg	Tricked by metric eggs	2016-03-15 00:00:00+00	2026-05-29 02:11:18.929346+00
a03ac1cc-40fc-4283-b15c-5e768c072d4e	es2015-ig-80	17858135377041516	BGRhG3AlnEe	/media/80.jpg	Excellent recycling	2016-06-05 00:00:00+00	2026-05-29 02:11:18.929346+00
8686c718-0267-4118-b5d6-121ddf23ea66	es2015-ig-90	17850986311065455	BFzfRBlFnNq	/media/90.jpg	Faraway place, faraway look	2016-05-24 00:00:00+00	2026-05-29 02:11:18.929346+00
830c3697-fa79-4137-a430-45760432475d	es2015-ig-100	17857251190002804	BFJu2Y8lnBK	/media/100.jpg	Standing in for some absentee statues	2016-05-08 00:00:00+00	2026-05-29 02:11:18.929346+00
da97273f-2cc4-4afc-a770-a26b9ed7a829	es2015-ig-101	17856392107061919	BE_ilZHlnCk	/media/101.jpg	Third holiest site in Islam, vigilantly policed by volunteers who dinged us for holding hands	2016-05-04 00:00:00+00	2026-05-29 02:11:18.929346+00
2107042e-c59e-4f56-ab63-ba4dc5ee6e7e	es2015-ig-138	17854382950055643	BDAVzMklnKI	/media/138.jpg	Ground zero for #ourearthsandwich	2016-03-16 00:00:00+00	2026-05-29 02:11:18.929346+00
d9e1c692-5dc7-4db3-8bd2-246286df408f	es2015-ig-139	17855441224009700	BDAUJNoFnIs	/media/139.jpg	Through the looking glass at the wonderland garden	2016-03-16 00:00:00+00	2026-05-29 02:11:18.929346+00
919c6acc-d4b0-4a78-ac6d-7c32d3f33bb8	es2015-ig-145	17845603714079409	BChkf3kFnEA	/media/145.jpg	Close but no cigar	2016-03-04 00:00:00+00	2026-05-29 02:11:18.929346+00
469b4b28-2764-4936-ab55-1b614821b33e	es2015-ig-146	17853647512011797	BChkQ6tlnDx	/media/146.jpg	High five bro!	2016-03-04 00:00:00+00	2026-05-29 02:11:18.929346+00
a8c986fa-8bb5-44a7-bb9c-92fb7efb6902	es2015-ig-147	17844849784100988	BCg0NZxlnEl	/media/147.jpg	Suddenly being a black sheep doesn't sound so bad...	2016-03-04 00:00:00+00	2026-05-29 02:11:18.929346+00
c7c27ff2-1564-4c8f-85fe-007cf545dbd8	es2015-ig-148	17844884827087766	BCgzSa7lnDd	/media/148.jpg	I'm going to wager that exactly zero black people have ever stayed at this bed & breakfast	2016-03-04 00:00:00+00	2026-05-29 02:11:18.929346+00
2ce4c772-c71a-4180-8ba2-cc614875b2cb	es2015-ig-149	17845547590077738	BCgxyUClnBV	/media/149.jpg	A bit of geology porn at the top of Mt Doom	2016-03-04 00:00:00+00	2026-05-29 02:11:18.929346+00
b83987d5-04c5-480d-91a2-b9cab143c041	es2015-ig-150	17844707533115207	BCPotg3FnPM	/media/150.jpg	Embracing cultural nuance	2016-02-26 00:00:00+00	2026-05-29 02:11:18.929346+00
be22821e-c2e2-4a00-99bb-a90c9f43ebe5	es2015-ig-151	17854353184008220	BCPoLdOFnOl	/media/151.jpg	I'm confident only good things can come of this	2016-02-26 00:00:00+00	2026-05-29 02:11:18.929346+00
7dc22f1d-1bde-446b-a787-05289502ac48	es2015-ig-152	17853683359020200	BCPnnQmFnN9	/media/152.jpg	Kiwis are very trusting about leaving their things around	2016-02-26 00:00:00+00	2026-05-29 02:11:18.929346+00
cbaf3f6a-0618-456c-ab36-50309c3ae1bc	es2015-ig-153	17853274732042302	BCIK3K9FnG5	/media/153.jpg	An old friend shows up to see us off. Thanks big J!	2016-02-23 00:00:00+00	2026-05-29 02:11:18.929346+00
eeb13fb5-3730-44a3-aaa3-ecfea955ab76	es2015-ig-154	17853926197039229	BBy08ZNlnC1	/media/154.jpg	In Argentina, they call this a municipal water pumping station	2016-02-15 00:00:00+00	2026-05-29 02:11:18.929346+00
bf7b3283-76ce-4fbb-8575-d78ce480ffff	es2015-ig-155	17849325040075543	BBvtN0qlnK7	/media/155.jpg	I wonder if she was actually this haunting in life or if they amped it up for the cemetery so she wouldn't get picked on by the other ghouls	2016-02-13 00:00:00+00	2026-05-29 02:11:18.929346+00
132cf3c0-29f6-4380-9fd5-7067db5c887b	es2015-ig-156	17853589381025349	BBkTiCdlnKY	/media/156.jpg	Close enough	2016-02-09 00:00:00+00	2026-05-29 02:11:18.929346+00
692bb3ec-dac0-4381-893e-b90707ee5a34	es2015-ig-157	17844259963093660	BBkTHzMFnJd	/media/157.jpg	Protesting human right violations and Attaining enlightenment, #stuffwhitepeoplelike is the same everywhere	2016-02-09 00:00:00+00	2026-05-29 02:11:18.929346+00
83a9cc00-f760-4034-bd16-3b9d42d17140	es2015-ig-158	17852778934061514	BBjUXaxlnDq	/media/158.jpg	Warming up for a good old fashioned game of father-daughter polo	2016-02-09 00:00:00+00	2026-05-29 02:11:18.929346+00
5625d821-4a14-4515-b88f-5e78d00582e4	es2015-ig-159	17856125623059604	BBVxP7ZFnMZ	/media/159.jpg	I always wondered what it would look like if Jesus gave Alec Baldwin's brass balls speech dressed as a pirate	2016-02-03 00:00:00+00	2026-05-29 02:11:18.929346+00
daf41fc5-8e4a-42a9-a8ab-3a1fe29326d6	es2015-ig-160	17844223978090747	BBVwC2alnKZ	/media/160.jpg	Now that's what I call an idyllic country cottage	2016-02-03 00:00:00+00	2026-05-29 02:11:18.929346+00
11282f34-0a86-4370-a4b1-46350e12fc44	es2015-ig-161	17853413674003723	BBOuBTvlnKH	/media/161.jpg	Travel tip no. 42: When crossing mountains by land, the changing air pressure may or may not implode your bus like a sinking submarine	2016-02-01 00:00:00+00	2026-05-29 02:11:18.929346+00
ffc387d7-0d1e-41f3-800f-b4ca8877be67	es2015-ig-162	17844218560114470	BBOtF1QFnIm	/media/162.jpg	The Supreme Leader inspects another bountiful harvest	2016-02-01 00:00:00+00	2026-05-29 02:11:18.929346+00
4f396f9d-4cfa-4b8b-b5e0-2c38f42e8a03	es2015-ig-163	17844875899075185	BBOsiIMlnHr	/media/163.jpg	I wonder what this button does...	2016-02-01 00:00:00+00	2026-05-29 02:11:18.929346+00
bfcae5a2-f240-4b93-919d-a9bbd53c79fa	es2015-ig-164	17844155383108194	BBOrulpFnGI	/media/164.jpg	Discovered by the Germans in 1904, they named it Santiago, which of course in German means ‘a whale’s vagina'.	2016-02-01 00:00:00+00	2026-05-29 02:11:18.929346+00
2e3efa6e-6e86-45b9-95a9-39afc820e6aa	es2015-ig-165	17844086338121492	BBBhww9lnNE	/media/165.jpg	It's a bird! It's a plane!	2016-01-27 00:00:00+00	2026-05-29 02:11:18.929346+00
2fa8ba8b-057c-48ed-b21e-c236b73e4a4b	es2015-ig-166	17852760409010689	BBBgI_YFnJv	/media/166.jpg	Sometimes nothing makes me happier than seeing little affirmations of America's all-pervasive cultural dominance #americafuckyeah	2016-01-27 00:00:00+00	2026-05-29 02:11:18.929346+00
65c502cc-017a-4b2c-a272-4df55db3f8dd	es2015-ig-167	17844117046105614	BBBfS74lnIK	/media/167.jpg	Now it's a party!	2016-01-27 00:00:00+00	2026-05-29 02:11:18.929346+00
0cdc3afc-37a6-4a4b-9cb2-2b84e927e1e4	es2015-ig-168	17847018424064841	BBBeVJulnGl	/media/168.jpg	The imperial accounting system of the Incans recorded in knots	2016-01-27 00:00:00+00	2026-05-29 02:11:18.929346+00
7393ed35-f34c-4e3f-b221-591df2a8d72c	es2015-ig-169	17844020167105373	BAxP7OxlnGu	/media/169.jpg	I'm Hans, unt I'm Frans. And vee are goona Pump! You Aup!	2016-01-20 00:00:00+00	2026-05-29 02:11:18.929346+00
80a45172-9381-4089-893f-e996cc92193d	es2015-ig-170	17853153064044785	BAeiPA4FnC0	/media/170.jpg	Adios Bolivia, you magnificently weird duck	2016-01-13 00:00:00+00	2026-05-29 02:11:18.929346+00
52174fe8-09de-4f21-8381-5ed61d59c287	es2015-ig-172	17843909839106927	BAYeCuSFnBs	/media/172.jpg	The Temptation of Christ	2016-01-11 00:00:00+00	2026-05-29 02:11:18.929346+00
1d6ed64d-7d60-4fad-b7dc-a21d46c86490	es2015-ig-173	17843916694086207	BAYdU8zFnAH	/media/173.jpg	Can there be too much of a good thing? Answer is no.	2016-01-11 00:00:00+00	2026-05-29 02:11:18.929346+00
8a3dcaab-01be-4496-85be-885095952596	es2015-ig-174	17852936779011226	BAXMWQjFnNq	/media/174.jpg	The Rock is going to look so bad ass power drifting these in Fast and Furious 8	2016-01-10 00:00:00+00	2026-05-29 02:11:18.929346+00
e6df9931-794d-4009-87d0-e0a3a269bd7e	es2015-ig-175	17853446587048078	BAXKqr9FnKQ	/media/175.jpg	Bolivia has some bumpy-ass roads. This was by far the most comfortable part of our journey to Lake Titicaca	2016-01-10 00:00:00+00	2026-05-29 02:11:18.929346+00
107ff574-acd9-4568-b252-ae62c3fe64aa	es2015-ig-176	17852580307038419	BAXICkWFnE9	/media/176.jpg	There is no corner on earth where people don't love Korean soaps	2016-01-10 00:00:00+00	2026-05-29 02:11:18.929346+00
28f5dff2-1356-481a-a14c-5535ea845e10	es2015-ig-177	17843893009085176	BAM5rTYFnCy	/media/177.jpg	3000 miles to end up right back in Brooklyn #nycisthenewrome	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
2903048e-6451-4e89-9122-3dbab2236604	es2015-ig-178	17843892214123295	BAM4Rm5FnP3	/media/178.jpg	Brazilian water-heating shower head. Sounds like an amazing innovation until you realize it's a wet 220 volt appliance plugged in right above your naked body	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
60e760e8-6d60-4290-80c1-d68c5df130fb	es2015-ig-179	17852542504049639	BAM2VCIFnMe	/media/179.jpg	Our kickass Bolivian Spanish teacher, Shirley	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
24f2da69-f5d9-4eec-b5fa-34d9687dc05f	es2015-ig-180	17844101635126933	BAM1A7CFnJ4	/media/180.jpg	In my book, train cemetery comes in solidly above 'pet' and just a little below 'haunted'	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
9d58cd94-ed7d-4145-8cc5-5e05bdf00f18	es2015-ig-181	17843897125126457	BAMxmiDlnC2	/media/181.jpg	Wela's surrealist interpretation of the Dali Desert	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
d6a197ec-17b8-4d7b-93cb-e25c80796587	es2015-ig-183	17852594608048272	BALfnv7FnBG	/media/183.jpg	Watch out X-Games, your new star has arrived	2016-01-06 00:00:00+00	2026-05-29 02:11:18.929346+00
033b3f75-526b-43d6-a969-487d2fe40ce3	es2015-ig-184	17843859973103377	BAH7keKlnGc	/media/184.jpg	I don't have to outrun the dinosaur...	2016-01-04 00:00:00+00	2026-05-29 02:11:18.929346+00
6f62a271-e0e5-409b-8857-3dd73f3b7852	es2015-ig-185	17846442787070700	BAH7i4gFnGZ	/media/185.jpg	Come to me llamas, I only want to love you	2016-01-04 00:00:00+00	2026-05-29 02:11:18.929346+00
8b3ee58a-18c6-4042-9f10-5fb599d64661	es2015-ig-186	17846824885065812	_75XEMFnKx	/media/186.jpg	Onward to victory brave patriot	2015-12-31 00:00:00+00	2026-05-29 02:11:18.929346+00
9e5c8523-191d-4de5-8a25-3edab5aeb61b	es2015-ig-187	17852944534057279	_75Dn1FnKO	/media/187.jpg	My window buddy enroute to the Salt Flats	2015-12-31 00:00:00+00	2026-05-29 02:11:18.929346+00
b948d805-bc3c-4e99-87b7-bf7fc6089dfd	es2015-ig-188	17853312478019075	_nfyScFnBX	/media/188.jpg	Wayward Amish clan contemplate taking the airport escalator because, fuck it, they're about to board a sky-buggy of damnation anyways	2015-12-23 00:00:00+00	2026-05-29 02:11:18.929346+00
64acdb60-7768-4788-8a32-158a5f87916e	es2015-ig-189	17844157597077804	_DY8DslnF2	/media/189.jpg	Hey little buddy, whatcha doin' down there?	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
40280712-9441-4395-96f9-3ce68d8a1d10	es2015-ig-190	17850917368044068	_DWDIOlnBH	/media/190.jpg	Practicing for our inevitable encounter with giant tarantulas, river sharks, and Farc guerrillas	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
c8b435d8-33ad-46f6-9fd3-8a1858250bd7	es2015-ig-191	17843579293105595	_DU5XpFnPQ	/media/191.jpg	Oh piranhas, how quickly the tables turn	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
d1bf3374-c4a5-4255-9460-279efe50c379	es2015-ig-192	17850285760063735	_DUk6ZFnOx	/media/192.jpg	Thanks team! For not letting us die in the jungle	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
220918c2-5cf7-40a0-9a49-e9389c8c1802	es2015-ig-193	17843525428113747	_DS3iZlnL-	/media/193.jpg	Peruvian side of the Amazon river is rather less developed, as attested by the the logs lashed together as a dock gang plank	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
65ed789e-68af-4042-83db-bffde3f136d8	es2015-ig-194	17851314046046723	_DRpzAlnJr	/media/194.jpg	OK, so maybe don't go right then...	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
a681c87c-41d2-48ca-be04-85ef3343fa3a	es2015-ig-195	17850834646015734	_DQ2LxFnIH	/media/195.jpg	For some reason there's a vending machine selling impotence pills behind the grumpy cashier at this fancy coffee shop	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
73c06402-caa5-4d46-a3e6-007621f11f3d	es2015-ig-196	17843531455129604	_DP7A4FnGf	/media/196.jpg	Each of those tiles is from some city/state/country in the world. Didn't find Texas so I'll have to send one in when I get home	2015-12-09 00:00:00+00	2026-05-29 02:11:18.929346+00
55164270-8468-4a3c-ad7c-851171b9b8f4	es2015-ig-197	17844464305066168	-XbXXalnLE	/media/197.jpg	Corn hole + Explosives = Tejo. Playing a few rounds with my taxi driver. This game is coming home with me	2015-11-21 00:00:00+00	2026-05-29 02:11:18.929346+00
0a8d63da-98d1-476f-918e-28d4e75abcd1	es2015-ig-198	17843421703074779	-Xaa6sFnJO	/media/198.jpg	A random Russian bar in the Caribbean, complete with bartenders dressed like Xenia Onatopp	2015-11-21 00:00:00+00	2026-05-29 02:11:18.929346+00
57ddb52e-5446-4e37-b49a-62c44f2e495f	es2015-ig-199	17842666129105122	-RMFY8FnOQ	/media/199.jpg	You don't fool me banana tree, I know what I'm looking at...	2015-11-19 00:00:00+00	2026-05-29 02:11:18.929346+00
882c8a09-784b-40af-b9de-d29f14c1bee1	es2015-ig-200	17847831604019879	-RLt1zlnNk	/media/200.jpg	Not a bad way to check email	2015-11-19 00:00:00+00	2026-05-29 02:11:18.929346+00
011db978-4db9-488c-88de-b05a9f2f6acd	es2015-ig-201	17847500632048089	-RLZjwFnNE	/media/201.jpg	Cloud forest! A great view in many ways	2015-11-19 00:00:00+00	2026-05-29 02:11:18.929346+00
e45e860e-3e95-4a6a-9dbd-03a9dbc5bd66	es2015-ig-202	17842374907081961	-FxdjNFnEK	/media/202.jpg	Hi ho! Hi ho! It's off to work we go!	2015-11-15 00:00:00+00	2026-05-29 02:11:18.929346+00
d2961332-0742-42e9-a5bc-05b804c4e03f	es2015-ig-203	17845831912047607	9-IKirFnCv	/media/203.jpg	Internet is not allowed in homes so people congregate in parks where Wi-Fi is dealt out like crack. Cuba is a weird place and outside the resorts it's short on a lot of material comforts. I wanted to see what a place outside the global consensus looks like and Cuba delivered in spades. Its not always sweet, but this place has flavor.	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
158327a6-0e69-4bdb-aad5-3da4805c534c	es2015-ig-204	17845378867026200	9-G9ECFnBD	/media/204.jpg	Stumbled on a qualifier match for the provincial championships. Apparently Cubans love boxing and ballet because of the Soviets. Ivan would be proud	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
30a8b0dc-3239-40f6-a8fc-8779044e78ec	es2015-ig-205	17842166767091705	9-EpyIlnNN	/media/205.jpg	In Cuba, even Jesus is smoking a cigar and holding a martini	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
2952c1b3-82e8-4509-ab6f-855a9dda1370	es2015-ig-206	17846043265037240	9-EK7ulnMV	/media/206.jpg	'Fidel' by Banksy	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
2ab7389c-fde4-44f1-b6d5-1a9d96dbd722	es2015-ig-207	17845432549032110	9-DvX0FnLe	/media/207.jpg	Leg room in these old Chevys was insane. Now I finally get why losing your virginity in a car is an American thing	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
b0868e90-5a0f-40a0-9045-9fe24740deba	es2015-ig-208	17846235196007265	9-DGlLlnKR	/media/208.jpg	No matter what corner of the world you go, there will always be a Chinatown	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
742388f4-0722-4a1c-9180-e223eaf126a7	es2015-ig-209	17846448709007959	9-CrGulnJR	/media/209.jpg	Our first 10 minutes in Havana and we couldn't have found a more Cubano character if we were casting a movie	2015-11-12 00:00:00+00	2026-05-29 02:11:18.929346+00
61f33340-2d19-457d-9acf-68a51aa830f8	es2015-ig-210	17843500477064436	9o20UHFnI8	/media/210.jpg	Edible Arrangements have been trying to branch out lately	2015-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
2d2982ee-078e-44f2-88ba-410a34a43c06	es2015-ig-211	17843500342064436	9o1sA3FnHK	/media/211.jpg	Yay adventure, Yay friendship, Yay good feeling!	2015-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
b86d0778-dbd6-4519-a4b8-443360459e8c	es2015-ig-212	17843500201064436	9o1A7EFnGD	/media/212.jpg	Rock out buddy, how do I get your confidence?	2015-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
ad9ced53-780d-410c-a767-330bf9b8cd80	es2015-ig-213	17843500072064436	9o0RRNlnFD	/media/213.jpg	Late night shrimpin'	2015-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
3be370ee-afa2-4d6a-bcf2-82f835c5e924	es2015-ig-214	17843500018064436	9oz7qEFnEl	/media/214.jpg	Fabulous lady of mystery contemplates her next adventure	2015-11-03 00:00:00+00	2026-05-29 02:11:18.929346+00
b3e76384-0985-43fa-8244-47e533cb3c32	es2015-ig-215	17843304730064436	9Q1Lf9lnOV	/media/215.jpg	For 3 bucks, you get a bunch of fragile tissue paper nets, and every fish you catch is yours. I didn't need new pets so I ate mine.	2015-10-25 00:00:00+00	2026-05-29 02:11:18.929346+00
a412a7ff-0e91-4b8d-a7d3-2c42a40c805b	es2015-ig-216	17843294104064436	9Pid74FnI6	/media/216.jpg	You don't fool me cubism, I know what I'm looking at	2015-10-25 00:00:00+00	2026-05-29 02:11:18.929346+00
0ad45615-e8bd-435f-a164-7b529b3a638f	es2015-ig-217	17843294056064436	9PhvblFnHo	/media/217.jpg	Joined a political rally yesterday because I love chanting mobs. Also they had free ice cream	2015-10-25 00:00:00+00	2026-05-29 02:11:18.929346+00
ad00a88b-e6d6-4bfe-b474-f4a032f29207	es2015-ig-218	17843293963064436	9Pgq_hFnFq	/media/218.jpg	Blatant copyright infringement and careless appropriation of religious symbology all to sell some fried chicken. I like it.	2015-10-25 00:00:00+00	2026-05-29 02:11:18.929346+00
7da54b6e-4888-47b2-b822-0cf4b2fdbb90	es2015-ig-219	17843234383064436	9H6fIqlnIR	/media/219.jpg	I want this jolly windswept fellow for my living room. Wela said "We'll see..."	2015-10-22 00:00:00+00	2026-05-29 02:11:18.929346+00
b32830fc-0dbb-4df6-850c-50b97c1ca32e	es2015-ig-220	17843208961064436	9FIn05lnNh	/media/220.jpg	Steak restaurant with authentic cowboy!	2015-10-21 00:00:00+00	2026-05-29 02:11:18.929346+00
3140f9bf-4a06-40a1-9835-782cc1275fb2	es2015-ig-221	17843127322064436	9Ckqx1FnGb	/media/221.jpg	Paying for a wedding in China is like prepping for a drug deal, my Glock is just off-camera	2015-10-20 00:00:00+00	2026-05-29 02:11:18.929346+00
3dd8a121-c501-4fb3-a7de-67a7e1d9a5ac	es2015-ig-222	17843126758064436	9Cj6H8FnFJ	/media/222.jpg	Disability access ramp in China, "A" for effort	2015-10-20 00:00:00+00	2026-05-29 02:11:18.929346+00
cc43a685-1790-4ed3-b001-fc2aa72e5370	es2015-ig-268	17841966490064436	6bArkrlnCr	/media/268.jpg	"Closed for vacation, back in September. Happy summer!" - your move France...	2015-08-15 00:00:00+00	2026-05-29 02:11:18.929346+00
fbe96873-a968-4d11-ade5-c1e00e3192e3	es2015-ig-223	17843125684064436	9CiXJGlnCw	/media/223.jpg	Caption reads: You may live like a pig, but you won't achieve a pig's happiness. Inspiration from the back of a Chinese beer bottle	2015-10-20 00:00:00+00	2026-05-29 02:11:18.929346+00
c0806cf0-7294-4c9e-a3c0-658d506b0fff	es2015-ig-224	17842644322064436	8RJyChFnOD	/media/224.jpg	Though in all seriousness, no one does awe-inspiring like Catholics. Sometimes gaudy, sometimes overwhelming beautiful.	2015-09-30 00:00:00+00	2026-05-29 02:11:18.929346+00
192c4340-f6b1-4942-b94e-6737e7b7a266	es2015-ig-225	17842644043064436	8RIA48lnKW	/media/225.jpg	Are you not entertained!?!	2015-09-30 00:00:00+00	2026-05-29 02:11:18.929346+00
4ab1d772-b284-4fef-a7e7-6913a8450e0e	es2015-ig-226	17842643989064436	8RHwTOlnJ1	/media/226.jpg	I believe this panel depicts how God escapes awkward situations	2015-09-30 00:00:00+00	2026-05-29 02:11:18.929346+00
2e425025-9933-4da5-a53f-870ec54bf1af	es2015-ig-227	17842643794064436	8RGkcWlnHW	/media/227.jpg	I forgot maps had this function. St. Peter looks over Rome, and so do Sergie and Larry.	2015-09-30 00:00:00+00	2026-05-29 02:11:18.929346+00
edccf4d1-c30b-4a4e-afef-663604c84872	es2015-ig-228	17842643461064436	8RE38RFnDx	/media/228.jpg	Yes to all of those things.	2015-09-30 00:00:00+00	2026-05-29 02:11:18.929346+00
2a641a43-5f87-4261-8f60-3533e5d78bfd	es2015-ig-229	17842547719064436	8HGzZZFnDm	/media/229.jpg	Architectural drawings from ancient times. Somehow it never occurred to me that they didn't just grab a chisel and go at it	2015-09-26 00:00:00+00	2026-05-29 02:11:18.929346+00
191c93c9-2d31-479d-81ab-50b9a47042af	es2015-ig-230	17842547629064436	8HFm5ulnBV	/media/230.jpg	Inspired by Michelangelo's David...	2015-09-26 00:00:00+00	2026-05-29 02:11:18.929346+00
7407ae1e-47ea-4326-9393-8c7876dc4366	es2015-ig-231	17842466359064436	78uIebFnGN	/media/231.jpg	Sometimes there's no reason to resist indulging in a classic	2015-09-22 00:00:00+00	2026-05-29 02:11:18.929346+00
3b8543b6-05f6-4460-9fb5-355da5f057a2	es2015-ig-232	17842466089064436	78s_fBlnEU	/media/232.jpg	An escapee from the little shop of horrors	2015-09-22 00:00:00+00	2026-05-29 02:11:18.929346+00
56bde1f7-84fe-4cb5-85e3-8d2a62c76f37	es2015-ig-233	17842428487064436	73aLrBFnM6	/media/233.jpg	Dave's really been trying to find himself	2015-09-20 00:00:00+00	2026-05-29 02:11:18.929346+00
005ef11f-28be-4b24-933f-f2f99ea8623b	es2015-ig-234	17842428373064436	73Zpu-lnLq	/media/234.jpg	It looks like Leonardo was the original #leanstartup	2015-09-20 00:00:00+00	2026-05-29 02:11:18.929346+00
7623d660-4cc2-4410-a394-9d43c2a5aa23	es2015-ig-235	17842408936064436	70s_qoFnFh	/media/235.jpg	This smile is from before climbing the 500 steps to the top.	2015-09-19 00:00:00+00	2026-05-29 02:11:18.929346+00
3783d755-b996-4b9e-8e50-6d1b95639e32	es2015-ig-236	17842408774064436	70r2T-lnDG	/media/236.jpg	She handles her business like a lady, dat ass tho!	2015-09-19 00:00:00+00	2026-05-29 02:11:18.929346+00
edc55f23-cb3e-46c5-a8dc-783273970c0f	es2015-ig-237	17842407436064436	70hwVvlnHL	/media/237.jpg	The Pope is not impressed by your little Basilica	2015-09-19 00:00:00+00	2026-05-29 02:11:18.929346+00
256ee8f2-b018-4af1-b101-aad221d73ce6	es2015-ig-238	17842403734064436	70DXlclnPZ	/media/238.jpg	This is, without question, the greatest nativity scene ever	2015-09-19 00:00:00+00	2026-05-29 02:11:18.929346+00
deb1ec24-c6d9-4b5f-bf3c-4db4d96a5800	es2015-ig-239	17842340515064436	7p03X2lnIW	/media/239.jpg	I've learned that Pisa is only the best known of hundreds of leaning towers in Italy. Evidently, they are just bad at this particular task	2015-09-15 00:00:00+00	2026-05-29 02:11:18.929346+00
b5b658a9-9410-4ec1-9257-f6ce1c71fe66	es2015-ig-240	17842338745064436	7plyT5FnPS	/media/240.jpg	It's nice that some things transcend all cultural boundaries	2015-09-15 00:00:00+00	2026-05-29 02:11:18.929346+00
7b4ea624-4ee8-4cbe-a27e-4592ad3d1038	es2015-ig-241	17842307590064436	7lZA2MFnPn	/media/241.jpg	What does the fox say?	2015-09-13 00:00:00+00	2026-05-29 02:11:18.929346+00
7dbc2632-a7c3-47d9-89ad-4653af92e41b	es2015-ig-242	17842285489064436	7i6CtNFnKv	/media/242.jpg	This is where Redbull keeps all their toys. In the top right corner is a badass glass conference room suspended above the hanger	2015-09-12 00:00:00+00	2026-05-29 02:11:18.929346+00
0dffe7e8-e47b-49c2-9093-41102209e455	es2015-ig-243	17842285366064436	7i5Kr6lnIp	/media/243.jpg	Do, a deer a female deer. Re, a drop of golden sun!	2015-09-12 00:00:00+00	2026-05-29 02:11:18.929346+00
80a634b2-2ba2-4d8a-8c97-82b6dc7f65ae	es2015-ig-244	17842250362064436	7cQxgLlnPy	/media/244.jpg	Clearly, I love rowboats	2015-09-10 00:00:00+00	2026-05-29 02:11:18.929346+00
8811a84c-d0b4-4276-b23b-e2fc4c44064e	es2015-ig-245	17842250323064436	7cP1hcFnOx	/media/245.jpg	Not usually into filters, but Cinderella's castle deserves a little magic	2015-09-10 00:00:00+00	2026-05-29 02:11:18.929346+00
6f6792db-9f18-4e83-a46b-cadba55ed1d4	es2015-ig-246	17842250293064436	7cO6OIFnNy	/media/246.jpg	This just got added to my list of things to do in life. Now I just have to learn to surf (and speak German and move to Munich)	2015-09-10 00:00:00+00	2026-05-29 02:11:18.929346+00
bf552504-5e20-48e2-9967-b9a92010c307	es2015-ig-247	17842217641064436	7ShPyYFnD2	/media/247.jpg	Now that's what I call biscuits and gravy!	2015-09-06 00:00:00+00	2026-05-29 02:11:18.929346+00
3f1e4b83-e551-4854-bffd-6c1ad790bd89	es2015-ig-248	17842217485064436	7SdtbVFnMS	/media/248.jpg	I spent 20 minutes trying to get mugged so I could see them spring into action	2015-09-06 00:00:00+00	2026-05-29 02:11:18.929346+00
79ae4606-574f-4720-adb7-94dd06355b9a	es2015-ig-249	17842217461064436	7SdN4UFnLk	/media/249.jpg	Hold on! You have so much to live for!	2015-09-06 00:00:00+00	2026-05-29 02:11:18.929346+00
27eb8675-0036-48b6-9f1f-8a9e7515b281	es2015-ig-250	17842217449064436	7Sc8sclnLF	/media/250.jpg	Good old fashioned fun at a 600 year old carnival	2015-09-06 00:00:00+00	2026-05-29 02:11:18.929346+00
60b964fb-ba58-47a1-9788-ff00bafbb858	es2015-ig-251	17842217398064436	7ScG0MlnJ1	/media/251.jpg	Tower ripped asunder	2015-09-06 00:00:00+00	2026-05-29 02:11:18.929346+00
f4f377dc-4e15-49d6-aeb5-2ca1f5875cc9	es2015-ig-252	17842217320064436	7Sa-ONFnH8	/media/252.jpg	Foreign languages are a total scam	2015-09-06 00:00:00+00	2026-05-29 02:11:18.929346+00
1a6eb40e-67d1-46a8-b40d-193e77d7e65a	es2015-ig-253	17842086382064436	68W2JvlnLo	/media/253.jpg	Oh please do tell	2015-08-28 00:00:00+00	2026-05-29 02:11:18.929346+00
16f61182-6a63-4052-b97a-0fabad71f559	es2015-ig-254	17842086352064436	68WgY3FnK_	/media/254.jpg	Oh Holland, have you learned nothing?	2015-08-28 00:00:00+00	2026-05-29 02:11:18.929346+00
ad279065-d5c9-4efa-8ded-3628afcc15d0	es2015-ig-255	17842061335064436	62g1tGFnJG	/media/255.jpg	Motherfucka lunged me	2015-08-26 00:00:00+00	2026-05-29 02:11:18.929346+00
215eb19a-721e-4bda-a25e-732085688cca	es2015-ig-256	17842055791064436	60yLk7FnOn	/media/256.jpg	The ruthless Khaleesi, leading her hoard to its next plunder	2015-08-25 00:00:00+00	2026-05-29 02:11:18.929346+00
2c279b72-005a-4974-a547-6d75b8eb1811	es2015-ig-257	17842044238064436	6x8KBBFnKW	/media/257.jpg	Partaking in the ancient and long revered Berber tradition of sandboarding	2015-08-24 00:00:00+00	2026-05-29 02:11:18.929346+00
718702ad-18fa-4195-a2a9-c248b70e558b	es2015-ig-258	17842026724064436	6txb7VlnPN	/media/258.jpg	Chaos and sublime in the winding bazaars	2015-08-23 00:00:00+00	2026-05-29 02:11:18.929346+00
8135973e-c179-4e62-998d-01d55a5b708a	es2015-ig-259	17842014331064436	6pmrY9FnFa	/media/259.jpg	Iron chef Morocco	2015-08-21 00:00:00+00	2026-05-29 02:11:18.929346+00
b87780d8-e501-4045-94e2-72c1f1754fed	es2015-ig-260	17842008022064436	6nubLTlnAf	/media/260.jpg	Moroccan chutes and ladders is serious business	2015-08-20 00:00:00+00	2026-05-29 02:11:18.929346+00
a030fe08-ba5b-4ac7-81a2-2e5eb614e14b	es2015-ig-261	17841999703064436	6k61ISFnBy	/media/261.jpg	@demianfaulkner I have this amazing place for you to try	2015-08-19 00:00:00+00	2026-05-29 02:11:18.929346+00
b2577559-e921-4d4e-831d-74c4256e21f9	es2015-ig-262	17841992557064436	6io-7FFnOi	/media/262.jpg	Good afternoon, Africa	2015-08-18 00:00:00+00	2026-05-29 02:11:18.929346+00
efd57baf-98ab-48d5-87b0-fb32792529a8	es2015-ig-263	17841992536064436	6iorSelnON	/media/263.jpg	Lose your remote? It's here in Morocco	2015-08-18 00:00:00+00	2026-05-29 02:11:18.929346+00
c094f863-8146-4d8d-924e-d9b18eab0312	es2015-ig-264	17841988345064436	6hcMk9lnK-	/media/264.jpg	See you later Europe, I'll catch you on the flip side.	2015-08-18 00:00:00+00	2026-05-29 02:11:18.929346+00
981ad641-c8fa-492e-bb95-8de0395debe9	es2015-ig-265	17841981940064436	6fSguQlnAl	/media/265.jpg	Granada as seen by the Moorish sultans of old	2015-08-17 00:00:00+00	2026-05-29 02:11:18.929346+00
62b8d9e3-4a48-4208-b1ea-49b1bbb3fa8e	es2015-ig-266	17841981871064436	6fRKqGlnNs	/media/266.jpg	Spain's Duck-alope, ancestor to our Jackalope	2015-08-17 00:00:00+00	2026-05-29 02:11:18.929346+00
39df7d08-3c7b-446a-b514-894d1a7bb82c	es2015-ig-267	17841970108064436	6cWDFlFnM4	/media/267.jpg	They take cockoo for cocoa puffs to the next level here	2015-08-16 00:00:00+00	2026-05-29 02:11:18.929346+00
449aee42-acb8-4a6c-9fe3-991443636cfd	es2015-ig-269	17841962050064436	6Zu6UrFnNO	/media/269.jpg	One of these was less than a dollar	2015-08-15 00:00:00+00	2026-05-29 02:11:18.929346+00
1ff16967-d826-4842-8958-d0af57000314	es2015-ig-270	17841951118064436	6WD06KlnM5	/media/270.jpg	I'm fighting a bull, obviously. #nailedit	2015-08-14 00:00:00+00	2026-05-29 02:11:18.929346+00
9e0dce52-66a1-4178-ab5c-38ad7a85a6f9	es2015-ig-271	17841951064064436	6WC7_yFnLF	/media/271.jpg	I think you never really get away until you're on a boat	2015-08-14 00:00:00+00	2026-05-29 02:11:18.929346+00
b8efe969-d0a6-4a07-b518-b63728cb37ab	es2015-ig-272	17841935890064436	6QtCK7FnDN	/media/272.jpg	The Spanish have style, these canopied daybeds are just part of a municipal park	2015-08-11 00:00:00+00	2026-05-29 02:11:18.929346+00
53db8433-c2d0-40d7-a799-4f3bfd510abc	es2015-ig-273	17841935833064436	6QrzP8lnA-	/media/273.jpg	Yes, that is an ice cream cone of meat	2015-08-11 00:00:00+00	2026-05-29 02:11:18.929346+00
270cb7d3-75e9-4dac-9c27-2cff34afd4c5	es2015-ig-274	17841935812064436	6QrTtRFnAM	/media/274.jpg	The largest Gothic cathedral in the world so I'm told	2015-08-11 00:00:00+00	2026-05-29 02:11:18.929346+00
00083f5b-d650-45db-b418-1d18744d8279	es2015-ig-275	17841924409064436	6NgZgjFnCm	/media/275.jpg	Always sit on the left side of an eastbound bus, because science. (reversed for southern hemisphere)	2015-08-10 00:00:00+00	2026-05-29 02:11:18.929346+00
89c1b9c8-13f7-4778-8613-e01f8133c913	es2015-ig-276	17841924172064436	6Ndp8DFnOI	/media/276.jpg	This blows my mind everytime. Put me in a polka dot dress, I'll shill for them any day #tmobile #productplacement	2015-08-10 00:00:00+00	2026-05-29 02:11:18.929346+00
4cb1cd6b-7b93-4767-8a84-06565184c1c7	es2015-ig-277	17841914938064436	6KLD-XlnEC	/media/277.jpg	Excuse me while I go fetch my Millennium Falcon	2015-08-09 00:00:00+00	2026-05-29 02:11:18.929346+00
0b21acd0-bf76-4f84-bbd9-18c5522388b2	es2015-ig-278	17841894166064436	6DlaPzFnDj	/media/278.jpg	The most adorable volunteer fire station ever	2015-08-06 00:00:00+00	2026-05-29 02:11:18.929346+00
d3680087-c4cf-4f6e-90cd-921a83b4a48b	es2015-ig-279	17841887479064436	6BDYzLFnMv	/media/279.jpg	The manliest picnic table ever made	2015-08-05 00:00:00+00	2026-05-29 02:11:18.929346+00
89bde851-c207-4d1b-9713-cc5ba6745e5f	es2015-ig-280	17841887467064436	6BC2zyFnLg	/media/280.jpg	It's nice, but how about more thorns?	2015-08-05 00:00:00+00	2026-05-29 02:11:18.929346+00
a7b009a5-98ec-477a-9a36-b4ea6a5fa708	es2015-ig-281	17841887416064436	6BBVdKlnIh	/media/281.jpg	Oh that old thing? Just a Moorish castle left over from the Reconquista #nbd	2015-08-05 00:00:00+00	2026-05-29 02:11:18.929346+00
42f54845-e098-45bd-b34b-856207a859d4	es2015-ig-282	17841886474064436	6AwZefFnGJ	/media/282.jpg	Posiden smash!	2015-08-05 00:00:00+00	2026-05-29 02:11:18.929346+00
6bc7b990-52f0-46f0-a559-3b5ecef89fe1	es2015-ig-283	17841886426064436	6AvJSglnEB	/media/283.jpg	No food, no flash, and no f'in selfie stick	2015-08-05 00:00:00+00	2026-05-29 02:11:18.929346+00
892cfb1a-926b-4bae-a373-cfedad1631d5	es2015-ig-284	17841880240064436	5-tEZAFnJI	/media/284.jpg	Welcome to the labyrinth. Dance magic, dance! #ourearthsandwich	2015-08-04 00:00:00+00	2026-05-29 02:11:18.929346+00
210c0afa-1b70-42f7-8dc8-86461845905b	es2015-ig-285	17841880189064436	5-rW2KlnF7	/media/285.jpg	I'd be offended, but they just seem to be getting along so well #multiculturalism	2015-08-04 00:00:00+00	2026-05-29 02:11:18.929346+00
8bfb397f-6b9a-4059-8f90-1e8344916630	es2015-ig-286	17841880138064436	5-qW_7lnEh	/media/286.jpg	Heading home for siesta after a morning of exploring. I assume they do that here too.	2015-08-04 00:00:00+00	2026-05-29 02:11:18.929346+00
85d3db7c-d7f0-45e6-8c69-4a55a1a46203	es2015-ig-287	17841874300064436	58Dx3vlnHK	/media/287.jpg	Mind the gap	2015-08-03 00:00:00+00	2026-05-29 02:11:18.929346+00
b3a27520-a06d-4723-838f-13dc46a6ad4a	es2015-ig-288	17841863338064436	548ERElnEY	/media/288.jpg	My fairest damsel, let down your hair!	2015-08-02 00:00:00+00	2026-05-29 02:11:18.929346+00
d561454e-c0cb-4005-b33e-80f852b83b8d	es2015-ig-289	17841862795064436	547dePlnC7	/media/289.jpg	Irish Cinnabun	2015-08-02 00:00:00+00	2026-05-29 02:11:18.929346+00
550274db-13b7-4f0d-96d2-8e5eeab34702	es2015-ig-290	17841854506064436	51XnncFnD1	/media/290.jpg	It's a matter of principle really	2015-08-01 00:00:00+00	2026-05-29 02:11:18.929346+00
4fb1d09f-d350-4927-a57b-de8b2419f884	es2015-ig-291	17841852844064436	50dqxiFnIq	/media/291.jpg	Irish people suck at walking	2015-07-31 00:00:00+00	2026-05-29 02:11:18.929346+00
23fdabad-8d21-4f4e-a6f2-f6605f45067f	es2015-ig-292	17841852754064436	50acq0lnDR	/media/292.jpg	Even in 8th century manuscripts, there are still poems about cats #pangurban #bookofkells	2015-07-31 00:00:00+00	2026-05-29 02:11:18.929346+00
dbaf3f90-97a1-42bb-8fa9-95265fd55ced	es2015-ig-293	17841844747064436	5x58KzlnLa	/media/293.jpg	While they threw in an authentic Irish jig every few sets, these folks were predominantly an One Direction cover band	2015-07-31 00:00:00+00	2026-05-29 02:11:18.929346+00
0ec34f76-429a-4ca9-b612-a050992bd9f5	es2015-ig-294	17841841987064436	5xcgVKFnP9	/media/294.jpg	Kiss me under the light of a thousand stars...	2015-07-30 00:00:00+00	2026-05-29 02:11:18.929346+00
73a715fe-fb71-4ec1-a0ff-c4abe78cb615	es2015-ig-295	17841841933064436	5xbqoxlnOJ	/media/295.jpg	I like Ireland's binary approach to banking: Money is Yes	2015-07-30 00:00:00+00	2026-05-29 02:11:18.929346+00
fe7e38e5-1d76-4415-b19b-3131a4f0aaa5	es2015-ig-296	17841833605064436	5t7qpalnJj	/media/296.jpg	I'm gonna guess 2 Michelin stars	2015-07-29 00:00:00+00	2026-05-29 02:11:18.929346+00
6272cefd-bdcc-494e-b4f3-33bac96ba9f5	es2015-ig-297	17841833278064436	5tvsUJlnIg	/media/297.jpg	There was a lot controversy when St. Patrick's Cathedral selected Dr Suess as their landscaper, nonetheless the archdiocese has stood steadfast by their choice	2015-07-29 00:00:00+00	2026-05-29 02:11:18.929346+00
ff984ff1-11aa-47d3-bceb-db7bdb1687ad	es2015-ig-298	17841833260064436	5tu_ZOlnHf	/media/298.jpg	A cobblestone passage through a medieval city wall, complete with a bar and a drunk stumbling home on a Wednesday morning, everything I ever hoped Ireland would be	2015-07-29 00:00:00+00	2026-05-29 02:11:18.929346+00
e00fe5fd-b900-45bb-8132-c0c78d5d02b0	es2015-ig-299	17841833236064436	5tuSCulnGh	/media/299.jpg	Some street art and political commentary in a Dublin back alley, right outside a bar of course	2015-07-29 00:00:00+00	2026-05-29 02:11:18.929346+00
fde25055-ade2-433b-9360-e2fcf81f087a	es2015-ig-300	17841819085064436	5osaSrFnA5	/media/300.jpg	After an aborted attempt to break into the particle physics game, Toronto cleverly refit their Hadron Collider into an efficient transit solution	2015-07-27 00:00:00+00	2026-05-29 02:11:18.929346+00
bcece5d1-f732-4e9e-b1ea-a7cd3443ce5d	es2015-ig-301	17841816202064436	5nM0rkFnGg	/media/301.jpg	Let there be no doubt which table was the most rocking last night	2015-07-26 00:00:00+00	2026-05-29 02:11:18.929346+00
f52e88b6-f61d-4d4b-adf4-7bef57edcd00	es2015-ig-302	17841814108064436	5mctThFnIX	/media/302.jpg	Congrats to the beautiful new Mr. and Mrs. Wissman	2015-07-26 00:00:00+00	2026-05-29 02:11:18.929346+00
7155da45-55e7-48b1-a3ce-83c5c5b24904	es2015-ig-303	17841798058064436	5fuI_0FnCe	/media/303.jpg	Open bar and sharks, a winning combination	2015-07-23 00:00:00+00	2026-05-29 02:11:18.929346+00
84414634-c142-49a0-baa0-0df4a400163c	es2015-ig-304	17841757846064436	5Ot-OTFnMy	/media/304.jpg	2015 finalists in the western conference tree pose championships	2015-07-17 00:00:00+00	2026-05-29 02:11:18.929346+00
26e65594-294d-4af4-b662-4c7d03f2be15	es2015-ig-305	17841757828064436	5OtXvIFnME	/media/305.jpg	Next stop, Atlantis	2015-07-17 00:00:00+00	2026-05-29 02:11:18.929346+00
698ed2b4-874f-4b98-82ac-357e12d27c21	es2015-ig-306	17841757816064436	5OtGZYlnLm	/media/306.jpg	The green wizard's neighborhood is really getting gentrified	2015-07-17 00:00:00+00	2026-05-29 02:11:18.929346+00
f509c056-058d-4f10-b5ba-bab24761f73a	es2015-ig-307	17841757804064436	5OssbxFnLD	/media/307.jpg	Reservoir Dogs on holiday	2015-07-17 00:00:00+00	2026-05-29 02:11:18.929346+00
b5e9f226-d806-4069-92c0-22f2c7d9612c	es2015-ig-308	17841745525064436	5IzQD2FnNR	/media/308.jpg	I always feel like a rock star when I walk out on the tarmac, even though this is also how refugees board planes	2015-07-15 00:00:00+00	2026-05-29 02:11:18.929346+00
ca0cd3a1-f187-4caa-8975-a9f4b6f0bc28	es2015-ig-309	17841727267064436	5A0VYXlnIW	/media/309.jpg	You win this round, child's plaything	2015-07-11 00:00:00+00	2026-05-29 02:11:18.929346+00
fcad7452-2b1c-40b0-880d-8b811161e38f	es2015-ig-310	17841723541064436	4-vKLiFnHN	/media/310.jpg	I'm so glad there are still restaurants that give you crayons #idontwannagrowup	2015-07-11 00:00:00+00	2026-05-29 02:11:18.929346+00
de4ae213-d240-4173-852f-2e6838f9ffc3	es2015-ig-311	17841712021064436	45EA90FnDO	/media/311.jpg	Ah Costco, where else could I get two liters of ranch dressing, a diamond ring, and agoraphobia all in one stop? #capitalism	2015-07-08 00:00:00+00	2026-05-29 02:11:18.929346+00
41f6934e-2f6a-4958-8bb8-8387da3b4f55	es2015-ig-312	17841707071064436	42c_5ClnEN	/media/312.jpg	This is also how I hug Wela #lennypetting	2015-07-07 00:00:00+00	2026-05-29 02:11:18.929346+00
540d0bd1-dbb2-49b3-b753-6b494ac4401d	es2015-ig-313	17841685192064436	4sf-_dlnMv	/media/313.jpg	Impressive, Canada. The student has become the teacher #americafuckyeah #imlovinit	2015-07-04 00:00:00+00	2026-05-29 02:11:18.929346+00
57d07848-b477-42b4-ba10-52f194066974	es2015-ig-315	17841658441064436	4gN0y0lnII	/media/315.jpg	Maybe the wine cellars at the Bellagio, or maybe a strip mall Thai joint with a killer duck panang for $10, #vegas has no rules	2015-06-29 00:00:00+00	2026-05-29 02:11:18.929346+00
2b38fad8-6f64-4561-ae71-6c7409e20c47	es2015-ig-316	17841650464064436	4cKiSglnJf	/media/316.jpg	Wtf kind of bruise is this? Either I got kicked by a pony or I clotheslined an octopus last night #animalcontrol #vegas	2015-06-27 00:00:00+00	2026-05-29 02:11:18.929346+00
255d5151-8fa7-4a7d-bd38-c633fef9cfd6	es2015-ig-317	17841645937064436	4aCGbhlnDv	/media/317.jpg	Virgin airlines is all about fun. That's why we played chicken at SFO for the right to land and live #radical	2015-06-26 00:00:00+00	2026-05-29 02:11:18.929346+00
c6562a79-28eb-47a5-ac98-b281a107c50f	es2015-ig-318	17841643114064436	4ZTJ3DFnDY	/media/318.jpg	Guess I won't be needing this anymore #adiosamigos	2015-06-26 00:00:00+00	2026-05-29 02:11:18.929346+00
57dc353b-5d97-4bb5-a36d-33aada919415	es2015-ig-319	17841641542064436	4YTqPjlnFf	/media/319.jpg	All you really need	2015-06-26 00:00:00+00	2026-05-29 02:11:18.929346+00
a22162c6-94f1-41eb-9c6e-460b8b8e38e3	es2015-ig-320	17841639481064436	4XH8OvFnGe	/media/320.jpg	There's now a voodoo doll of me getting jabbed somewhere in the upper west side #craigslist #grrmondays	2015-06-25 00:00:00+00	2026-05-29 02:11:18.929346+00
532bcf74-7e0f-4fdf-b578-1730e8562fd7	es2015-ig-321	17841638716064436	4WuYp6lnF0	/media/321.jpg	We've been staring at this map on our wall for 4 years	2015-06-25 00:00:00+00	2026-05-29 02:11:18.929346+00
0fc9ff9f-6e2d-482a-b77f-41cd2dbb1953	es2015-ig-322	17841609787064436	4MgtN7FnOe	/media/322.jpg	Avast me mateys, thar yonder port be a ripe for the taking!	2015-06-21 00:00:00+00	2026-05-29 02:11:18.929346+00
\.


--
-- Data for Name: regions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.regions (iata_code, name, airport_name, country, lat, lng) FROM stdin;
MDE	Medellín	José María Córdova International Airport	Colombia	6.1645000	-75.4231000
JFK	New York	John F. Kennedy International Airport	USA	40.6413000	-73.7781000
ARN	Stockholm	Stockholm Arlanda Airport	Sweden	59.6519000	17.9186000
MEX	Mexico City	Benito Juárez International Airport	Mexico	19.4363000	-99.0721000
OAX	Oaxaca	Xoxocotlán International Airport	Mexico	17.0517000	-96.7264000
DUB	Dublin	Dublin Airport	Ireland	53.4213000	-6.2701000
LIS	Lisbon	Humberto Delgado Airport	Portugal	38.7756000	-9.1354000
FAO	Faro (Algarve)	Faro Airport	Portugal	37.0144000	-7.9659000
SVQ	Seville	Seville Airport	Spain	37.4180000	-5.8931000
GRX	Granada	Federico García Lorca Granada-Jaén Airport	Spain	37.1887000	-3.7774000
AGP	Málaga (Costa del Sol)	Málaga-Costa del Sol Airport	Spain	36.6749000	-4.4991000
AMS	Amsterdam	Amsterdam Airport Schiphol	Netherlands	52.3086000	4.7639000
BRU	Brussels	Brussels Airport	Belgium	50.9010000	4.4844000
LUX	Luxembourg	Luxembourg Findel Airport	Luxembourg	49.6233000	6.2044000
FRA	Frankfurt (Rhine-Neckar)	Frankfurt Airport	Germany	50.0379000	8.5622000
MUC	Munich	Munich Airport	Germany	48.3537000	11.7750000
DRS	Dresden	Dresden Airport	Germany	51.1328000	13.7672000
BER	Berlin	Berlin Brandenburg Airport	Germany	52.3667000	13.5033000
SZG	Salzburg	Salzburg Airport	Austria	47.7933000	13.0043000
VIE	Vienna	Vienna International Airport	Austria	48.1103000	16.5697000
VCE	Venice	Venice Marco Polo Airport	Italy	45.5053000	12.3519000
BLQ	Bologna	Bologna Guglielmo Marconi Airport	Italy	44.5354000	11.2887000
FLR	Florence	Florence Peretola Airport	Italy	43.8100000	11.2051000
FCO	Rome	Leonardo da Vinci–Fiumicino Airport	Italy	41.8003000	12.2389000
PRG	Prague	Václav Havel Airport Prague	Czech Republic	50.1008000	14.2600000
BUD	Budapest	Budapest Ferenc Liszt International Airport	Hungary	47.4298000	19.2611000
WAW	Warsaw	Warsaw Chopin Airport	Poland	52.1657000	20.9671000
KRK	Kraków	John Paul II International Airport Kraków-Balice	Poland	50.0777000	19.7848000
RIX	Riga	Riga International Airport	Latvia	56.9236000	23.9711000
TNG	Tangier (Northern Morocco)	Tangier Ibn Battouta Airport	Morocco	35.7269000	-5.9169000
FEZ	Fez	Fès–Saïss Airport	Morocco	33.9273000	-4.9779000
RAK	Marrakech	Marrakech Menara Airport	Morocco	31.6069000	-8.0363000
CAI	Cairo	Cairo International Airport	Egypt	30.1219000	31.4056000
ASW	Aswan	Aswan International Airport	Egypt	23.9644000	32.8199000
LXR	Luxor	Luxor International Airport	Egypt	25.6710000	32.7066000
BEY	Beirut	Beirut Rafic Hariri International Airport	Lebanon	33.8209000	35.4884000
AMM	Amman	Queen Alia International Airport	Jordan	31.7226000	35.9932000
TLV	Tel Aviv (Israel)	Ben Gurion Airport	Israel	32.0055000	34.8706000
DXB	Dubai	Dubai International Airport	UAE	25.2532000	55.3657000
DOH	Doha	Hamad International Airport	Qatar	25.2609000	51.6138000
BAH	Bahrain	Bahrain International Airport	Bahrain	26.2708000	50.6336000
RUH	Riyadh	King Khalid International Airport	Saudi Arabia	24.9576000	46.6988000
IST	Istanbul	Istanbul Airport	Turkey	41.2753000	28.7519000
ADB	Izmir (Aegean Coast)	Adnan Menderes Airport	Turkey	38.2924000	27.1570000
DNZ	Pamukkale (Denizli)	Çardak Airport	Turkey	37.7856000	29.7013000
AYT	Antalya (Mediterranean Coast)	Antalya Airport	Turkey	36.8987000	30.8005000
ASR	Cappadocia (Kayseri)	Kayseri Erkilet International Airport	Turkey	38.7704000	35.4954000
JTR	Santorini (Greek Islands)	Santorini (Thira) National Airport	Greece	36.3992000	25.4793000
ATH	Athens	Athens International Airport Eleftherios Venizelos	Greece	37.9364000	23.9445000
KGS	Kos (Greek Islands)	Kos Island International Airport	Greece	36.7931000	27.0914000
SOF	Sofia	Sofia Airport	Bulgaria	42.6952000	23.4114000
VAR	Varna	Varna Airport	Bulgaria	43.2321000	27.8251000
OTP	Bucharest	Henri Coandă International Airport	Romania	44.5722000	26.1022000
BEG	Belgrade	Belgrade Nikola Tesla Airport	Serbia	44.8184000	20.3091000
SJJ	Sarajevo	Sarajevo International Airport	Bosnia and Herzegovina	43.8246000	18.3315000
DBV	Dubrovnik	Dubrovnik Airport	Croatia	42.5614000	18.2682000
SPU	Split	Split Airport	Croatia	43.5389000	16.2998000
ZAG	Zagreb	Zagreb Airport	Croatia	45.7429000	16.0688000
EVN	Yerevan	Zvartnots International Airport	Armenia	40.1473000	44.3959000
TAS	Tashkent	Tashkent International Airport	Uzbekistan	41.2579000	69.2811000
ALA	Almaty	Almaty International Airport	Kazakhstan	43.3521000	77.0405000
FRU	Bishkek	Manas International Airport	Kyrgyzstan	43.0613000	74.4777000
PVG	Shanghai	Shanghai Pudong International Airport	China	31.1443000	121.8083000
PEK	Beijing	Beijing Capital International Airport	China	40.0799000	116.6031000
KWL	Guilin (Yangshuo)	Guilin Liangjiang International Airport	China	25.2181000	110.0390000
URC	Ürümqi	Ürümqi Diwopu International Airport	China	43.9071000	87.4742000
TPE	Taipei	Taiwan Taoyuan International Airport	Taiwan	25.0777000	121.2328000
NRT	Tokyo	Narita International Airport	Japan	35.7647000	140.3864000
KTM	Kathmandu	Tribhuvan International Airport	Nepal	27.6966000	85.3591000
PBH	Paro (Bhutan)	Paro International Airport	Bhutan	27.4033000	89.4246000
SIN	Singapore	Singapore Changi Airport	Singapore	1.3644000	103.9915000
DPS	Bali	Ngurah Rai International Airport	Indonesia	-8.7482000	115.1670000
MNL	Manila	Ninoy Aquino International Airport	Philippines	14.5086000	121.0197000
GUM	Guam	Antonio B. Won Pat International Airport	USA	13.4834000	144.7959000
PNI	Pohnpei (Micronesia)	Pohnpei International Airport	Micronesia	6.9851000	158.2090000
HNL	Honolulu (Hawaii)	Daniel K. Inouye International Airport	USA	21.3187000	-157.9224000
IAH	Houston	George Bush Intercontinental Airport	USA	29.9902000	-95.3368000
MSY	New Orleans	Louis Armstrong New Orleans International Airport	USA	29.9934000	-90.2580000
HAV	Havana	José Martí International Airport	Cuba	22.9892000	-82.4091000
YYZ	Toronto	Toronto Pearson International Airport	Canada	43.6777000	-79.6248000
NAS	Nassau (Bahamas)	Lynden Pindling International Airport	Bahamas	25.0390000	-77.4660000
SEA	Seattle	Seattle–Tacoma International Airport	USA	47.4502000	-122.3088000
YVR	Vancouver	Vancouver International Airport	Canada	49.1939000	-123.1844000
LAS	Las Vegas	Harry Reid International Airport	USA	36.0840000	-115.1537000
SFO	San Francisco	San Francisco International Airport	USA	37.6213000	-122.3790000
BOG	Bogotá	El Dorado International Airport	Colombia	4.7016000	-74.1469000
PEI	Pereira	Matecaña International Airport	Colombia	4.8127000	-75.7395000
CTG	Cartagena	Rafael Núñez International Airport	Colombia	10.4424000	-75.5130000
SMR	Santa Marta	Simón Bolívar International Airport	Colombia	11.1196000	-74.2306000
LET	Leticia	Alfredo Vásquez Cobo International Airport	Colombia	-4.1933000	-69.9432000
MAO	Manaus	Eduardo Gomes International Airport	Brazil	-3.0386000	-60.0497000
GIG	Rio de Janeiro	Rio de Janeiro Galeão International Airport	Brazil	-22.8099000	-43.2505000
GRU	São Paulo	São Paulo/Guarulhos International Airport	Brazil	-23.4356000	-46.4731000
SRE	Sucre (Southern Bolivia)	Alcantarí International Airport	Bolivia	-19.2470000	-65.1549000
LPB	La Paz	El Alto International Airport	Bolivia	-16.5133000	-68.1922000
IQQ	Iquique	Diego Aracena International Airport	Chile	-20.5353000	-70.1812000
PMC	Puerto Montt	El Tepual International Airport	Chile	-41.4389000	-73.0940000
SCL	Santiago	Arturo Merino Benítez International Airport	Chile	-33.3930000	-70.7858000
MDZ	Mendoza	Governor Francisco Gabrielli International Airport	Argentina	-32.8317000	-68.7929000
EZE	Buenos Aires	Ministro Pistarini International Airport	Argentina	-34.8222000	-58.5358000
GPS	Galápagos Islands	Seymour Airport	Ecuador	-0.4538000	-90.2659000
FTE	El Calafate (Patagonia)	Comandante Armando Tola International Airport	Argentina	-50.2803000	-72.0531000
AKL	Auckland	Auckland Airport	New Zealand	-37.0082000	174.7850000
TRG	Tauranga	Tauranga Airport	New Zealand	-37.6719000	176.1961000
WLG	Wellington	Wellington International Airport	New Zealand	-41.3272000	174.8050000
CHC	Christchurch	Christchurch Airport	New Zealand	-43.4894000	172.5322000
NSN	Nelson	Nelson Airport	New Zealand	-41.2983000	173.2211000
ZQN	Queenstown	Queenstown Airport	New Zealand	-45.0211000	168.7392000
SYD	Sydney	Sydney Kingsford Smith Airport	Australia	-33.9399000	151.1753000
CNS	Cairns	Cairns Airport	Australia	-16.8858000	145.7552000
CPT	Cape Town	Cape Town International Airport	South Africa	-33.9715000	18.6021000
GBE	Gaborone	Sir Seretse Khama International Airport	Botswana	-24.5552000	25.9182000
KGL	Kigali	Kigali International Airport	Rwanda	-1.9686000	30.1395000
WDH	Windhoek	Hosea Kutako International Airport	Namibia	-22.4799000	17.4709000
\.


--
-- Data for Name: stops; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.stops (id, trip_id, date, location, lat, lng, status, region_code, post_type, caption, created_at) FROM stdin;
23	miscellaneous-adventures	2019-05-13	La Piedra del Peñol, Colombia	6.2000000	-75.0667000	visited	MDE	instagram	\N	2026-05-29 02:11:18.902214+00
22	miscellaneous-adventures	2019-05-13	La Piedra del Peñol, Colombia	6.2002000	-75.0670000	visited	MDE	instagram	\N	2026-05-29 02:11:18.902214+00
21	miscellaneous-adventures	2019-05-14	Medellín, Antioquia, Colombia	6.2518000	-75.5636000	visited	MDE	instagram	\N	2026-05-29 02:11:18.902214+00
20	miscellaneous-adventures	2019-05-14	Plaza Botero, Medellín, Colombia	6.2529000	-75.5644000	visited	MDE	instagram	\N	2026-05-29 02:11:18.902214+00
19	miscellaneous-adventures	2019-05-14	Aeropuerto Jose Maria Cordova, Medellín	6.1645000	-75.4231000	visited	MDE	instagram	\N	2026-05-29 02:11:18.902214+00
18	miscellaneous-adventures	2019-09-20	Hell's Kitchen, New York, USA	40.7638000	-73.9918000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
17	miscellaneous-adventures	2019-10-07	IKEA, Stockholm, Sweden	59.2743000	17.9166000	visited	ARN	instagram	\N	2026-05-29 02:11:18.902214+00
16	miscellaneous-adventures	2019-10-25	Hell's Kitchen, New York, USA	40.7640000	-73.9920000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
15	miscellaneous-adventures	2019-11-03	Ciudad de México, CDMX, Mexico	19.4326000	-99.1332000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
14	miscellaneous-adventures	2019-11-03	El 123, Mexico City, Mexico	19.4320000	-99.1335000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
13	miscellaneous-adventures	2019-11-05	Biblioteca José Vasconcelos, Mexico City, Mexico	19.4366000	-99.1381000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
12	miscellaneous-adventures	2019-11-06	El Dragón Restaurante Chino, Mexico City, Mexico	19.4284000	-99.1601000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
11	miscellaneous-adventures	2019-11-07	Las Pirámides de Teotihuacán, Mexico	19.6925000	-98.8438000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
10	miscellaneous-adventures	2019-11-07	Museo Soumaya, Mexico City, Mexico	19.4401000	-99.2023000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
9	miscellaneous-adventures	2019-11-09	Coyoacán, Mexico City, Mexico	19.3467000	-99.1617000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
8	miscellaneous-adventures	2019-11-10	Arena México, Mexico City, Mexico	19.4220000	-99.1570000	visited	MEX	instagram	\N	2026-05-29 02:11:18.902214+00
7	miscellaneous-adventures	2020-04-26	Times Square, New York, USA	40.7580000	-73.9855000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
6	miscellaneous-adventures	2024-02-17	Centro Académico y Cultural San Pablo, Oaxaca, Mexico	17.0612000	-96.7193000	visited	OAX	instagram	\N	2026-05-29 02:11:18.902214+00
5	miscellaneous-adventures	2024-02-17	Oaxaca Centro, Mexico	17.0600000	-96.7200000	visited	OAX	instagram	\N	2026-05-29 02:11:18.902214+00
4	miscellaneous-adventures	2024-02-19	El Árbol del Tule, Santa María del Tule, Oaxaca, Mexico	17.0462000	-96.6354000	visited	OAX	instagram	\N	2026-05-29 02:11:18.902214+00
3	miscellaneous-adventures	2024-02-19	Hierve el Agua, Oaxaca, Mexico	16.8654000	-96.2757000	visited	OAX	instagram	\N	2026-05-29 02:11:18.902214+00
2	miscellaneous-adventures	2024-02-20	Oaxaca Centro, Mexico	17.0604000	-96.7204000	visited	OAX	instagram	\N	2026-05-29 02:11:18.902214+00
1	miscellaneous-adventures	2024-02-20	Oaxaca Centro, Mexico	17.0608000	-96.7208000	visited	OAX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-01	earth-sandwich-2015	2015-07-28	Dublin, Ireland	53.3498000	-6.2603000	planned	DUB	planned	\N	2026-05-29 02:11:18.902214+00
es2015-02	earth-sandwich-2015	2015-08-03	Lisbon, Portugal	38.7169000	-9.1399000	planned	LIS	planned	\N	2026-05-29 02:11:18.902214+00
es2015-03	earth-sandwich-2015	2015-08-07	Lagos, Portugal	37.1017000	-8.6731000	planned	FAO	planned	\N	2026-05-29 02:11:18.902214+00
es2015-04	earth-sandwich-2015	2015-08-10	Seville, Spain	37.3886000	-5.9823000	planned	SVQ	planned	\N	2026-05-29 02:11:18.902214+00
es2015-05	earth-sandwich-2015	2015-08-13	Granada, Spain	37.1773000	-3.5986000	planned	GRX	planned	\N	2026-05-29 02:11:18.902214+00
es2015-06	earth-sandwich-2015	2015-08-18	Chefchaouen, Morocco	35.1714000	-5.2697000	planned	TNG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-07	earth-sandwich-2015	2015-08-20	Fez, Morocco	34.0181000	-5.0078000	planned	FEZ	planned	\N	2026-05-29 02:11:18.902214+00
es2015-08	earth-sandwich-2015	2015-08-24	Marrakesh, Morocco	31.6295000	-7.9811000	planned	RAK	planned	\N	2026-05-29 02:11:18.902214+00
es2015-09	earth-sandwich-2015	2015-08-27	Amsterdam, Netherlands	52.3676000	4.9041000	planned	AMS	planned	\N	2026-05-29 02:11:18.902214+00
es2015-10	earth-sandwich-2015	2015-08-31	Brussels, Belgium	50.8503000	4.3517000	planned	BRU	planned	\N	2026-05-29 02:11:18.902214+00
es2015-11	earth-sandwich-2015	2015-09-03	Luxembourg, Luxembourg	49.6117000	6.1319000	planned	LUX	planned	\N	2026-05-29 02:11:18.902214+00
es2015-12	earth-sandwich-2015	2015-09-04	Heidelberg, Germany	49.3988000	8.6724000	planned	FRA	planned	\N	2026-05-29 02:11:18.902214+00
es2015-13	earth-sandwich-2015	2015-09-07	Munich, Germany	48.1351000	11.5820000	planned	MUC	planned	\N	2026-05-29 02:11:18.902214+00
es2015-14	earth-sandwich-2015	2015-09-10	Salzburg, Austria	47.8095000	13.0550000	planned	SZG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-15	earth-sandwich-2015	2015-09-13	Venice, Italy	45.4408000	12.3155000	planned	VCE	planned	\N	2026-05-29 02:11:18.902214+00
es2015-16	earth-sandwich-2015	2015-09-15	Bologna, Italy	44.4949000	11.3426000	planned	BLQ	planned	\N	2026-05-29 02:11:18.902214+00
es2015-17	earth-sandwich-2015	2015-09-19	Florence, Italy	43.7696000	11.2558000	planned	FLR	planned	\N	2026-05-29 02:11:18.902214+00
es2015-18	earth-sandwich-2015	2015-09-25	Rome, Italy	41.9028000	12.4964000	planned	FCO	planned	\N	2026-05-29 02:11:18.902214+00
es2015-19	earth-sandwich-2015	2015-10-05	Shanghai, China	31.2304000	121.4737000	planned	PVG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-20	earth-sandwich-2015	2015-10-13	Beijing, China	39.9042000	116.4074000	planned	PEK	planned	\N	2026-05-29 02:11:18.902214+00
es2015-21	earth-sandwich-2015	2015-10-17	Yangshuo, China	24.7751000	110.4935000	planned	KWL	planned	\N	2026-05-29 02:11:18.902214+00
es2015-22	earth-sandwich-2015	2015-10-23	Taipei, Taiwan	25.0330000	121.5654000	planned	TPE	planned	\N	2026-05-29 02:11:18.902214+00
es2015-23	earth-sandwich-2015	2015-10-27	Houston, Texas, USA	29.7604000	-95.3698000	planned	IAH	planned	\N	2026-05-29 02:11:18.902214+00
es2015-24	earth-sandwich-2015	2015-10-30	New Orleans, Louisiana, USA	29.9511000	-90.0715000	planned	MSY	planned	\N	2026-05-29 02:11:18.902214+00
es2015-25	earth-sandwich-2015	2015-11-02	Mexico City, Mexico	19.4326000	-99.1332000	planned	MEX	planned	\N	2026-05-29 02:11:18.902214+00
es2015-26	earth-sandwich-2015	2015-11-05	Havana, Cuba	23.1136000	-82.3666000	planned	HAV	planned	\N	2026-05-29 02:11:18.902214+00
es2015-27	earth-sandwich-2015	2015-11-11	Bogotá, Colombia	4.7110000	-74.0721000	planned	BOG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-28	earth-sandwich-2015	2015-11-15	Pereira, Colombia	4.8133000	-75.6961000	planned	PEI	planned	\N	2026-05-29 02:11:18.902214+00
es2015-29	earth-sandwich-2015	2015-11-19	Cartagena, Colombia	10.3910000	-75.4794000	planned	CTG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-30	earth-sandwich-2015	2015-11-22	Taganga, Colombia	11.2667000	-74.1833000	planned	SMR	planned	\N	2026-05-29 02:11:18.902214+00
es2015-31	earth-sandwich-2015	2015-11-27	Leticia, Amazonas, Colombia	-4.2153000	-69.9406000	planned	LET	planned	\N	2026-05-29 02:11:18.902214+00
es2015-32	earth-sandwich-2015	2015-12-04	Manaus, Amazonas, Brazil	-3.1190000	-60.0217000	planned	MAO	planned	\N	2026-05-29 02:11:18.902214+00
es2015-33	earth-sandwich-2015	2015-12-06	Rio de Janeiro, Brazil	-22.9068000	-43.1729000	planned	GIG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-34	earth-sandwich-2015	2015-12-12	Ilha Grande, Rio de Janeiro, Brazil	-23.1595000	-44.2100000	planned	GIG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-35	earth-sandwich-2015	2015-12-15	Paraty, Rio de Janeiro, Brazil	23.2237000	-44.7129000	planned	GIG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-36	earth-sandwich-2015	2015-12-18	São Paulo, Brazil	-23.5505000	-46.6333000	planned	GRU	planned	\N	2026-05-29 02:11:18.902214+00
es2015-37	earth-sandwich-2015	2015-12-22	Sucre, Bolivia	-19.0431000	-65.2592000	planned	SRE	planned	\N	2026-05-29 02:11:18.902214+00
es2015-38	earth-sandwich-2015	2015-12-30	Uyuni, Bolivia	-20.4614000	-66.8258000	planned	SRE	planned	\N	2026-05-29 02:11:18.902214+00
es2015-39	earth-sandwich-2015	2016-01-04	La Paz, Bolivia	-16.4897000	-68.1193000	planned	LPB	planned	\N	2026-05-29 02:11:18.902214+00
es2015-40	earth-sandwich-2015	2016-01-11	Iquique, Chile	-20.2307000	-70.1357000	planned	IQQ	planned	\N	2026-05-29 02:11:18.902214+00
es2015-41	earth-sandwich-2015	2016-01-17	Puerto Varas, Chile	-41.3194000	-72.9796000	planned	PMC	planned	\N	2026-05-29 02:11:18.902214+00
es2015-42	earth-sandwich-2015	2016-01-24	Santiago, Chile	-33.4489000	-70.6693000	planned	SCL	planned	\N	2026-05-29 02:11:18.902214+00
es2015-43	earth-sandwich-2015	2016-01-28	Mendoza, Argentina	-32.8908000	-68.8272000	planned	MDZ	planned	\N	2026-05-29 02:11:18.902214+00
es2015-44	earth-sandwich-2015	2016-02-01	Buenos Aires, Argentina	-34.6037000	-58.3816000	planned	EZE	planned	\N	2026-05-29 02:11:18.902214+00
es2015-45	earth-sandwich-2015	2016-02-21	Auckland, New Zealand	-36.8509000	174.7645000	planned	AKL	planned	\N	2026-05-29 02:11:18.902214+00
es2015-46	earth-sandwich-2015	2016-02-24	Whangārei, New Zealand	-35.7275000	174.3166000	planned	AKL	planned	\N	2026-05-29 02:11:18.902214+00
es2015-47	earth-sandwich-2015	2016-02-27	Tauranga, New Zealand	-37.6878000	176.1651000	planned	TRG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-48	earth-sandwich-2015	2016-03-01	Wellington, New Zealand	-41.2866000	174.7756000	planned	WLG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-49	earth-sandwich-2015	2016-03-04	Kaikōura, New Zealand	-42.4047000	173.6808000	planned	CHC	planned	\N	2026-05-29 02:11:18.902214+00
es2015-50	earth-sandwich-2015	2016-03-07	Nelson, New Zealand	-41.2706000	173.2840000	planned	NSN	planned	\N	2026-05-29 02:11:18.902214+00
es2015-51	earth-sandwich-2015	2016-03-14	Queenstown, New Zealand	-45.0312000	168.6626000	planned	ZQN	planned	\N	2026-05-29 02:11:18.902214+00
es2015-52	earth-sandwich-2015	2016-03-21	Sydney, Australia	-33.8688000	151.2093000	planned	SYD	planned	\N	2026-05-29 02:11:18.902214+00
es2015-53	earth-sandwich-2015	2016-03-28	Port Douglas, Queensland, Australia	-16.4865000	145.4631000	planned	CNS	planned	\N	2026-05-29 02:11:18.902214+00
es2015-54	earth-sandwich-2015	2016-04-04	Cairo, Egypt	30.0444000	31.2357000	planned	CAI	planned	\N	2026-05-29 02:11:18.902214+00
es2015-55	earth-sandwich-2015	2016-04-09	Aswan, Egypt	24.0889000	32.8998000	planned	ASW	planned	\N	2026-05-29 02:11:18.902214+00
es2015-56	earth-sandwich-2015	2016-04-12	Nile River, Egypt	25.6900000	32.6500000	planned	ASW	planned	Floating the Nile between Aswan and Luxor	2026-05-29 02:11:18.902214+00
es2015-57	earth-sandwich-2015	2016-04-15	Luxor, Egypt	25.6872000	32.6396000	planned	LXR	planned	\N	2026-05-29 02:11:18.902214+00
es2015-58	earth-sandwich-2015	2016-04-18	Beirut, Lebanon	33.8938000	35.5018000	planned	BEY	planned	\N	2026-05-29 02:11:18.902214+00
es2015-59	earth-sandwich-2015	2016-04-25	Amman, Jordan	31.9539000	35.9106000	planned	AMM	planned	\N	2026-05-29 02:11:18.902214+00
es2015-60	earth-sandwich-2015	2016-05-02	Jerusalem, Israel	31.7683000	35.2137000	planned	TLV	planned	\N	2026-05-29 02:11:18.902214+00
es2015-61	earth-sandwich-2015	2016-05-06	Haifa, Israel	32.7940000	34.9896000	planned	TLV	planned	\N	2026-05-29 02:11:18.902214+00
es2015-62	earth-sandwich-2015	2016-05-09	Istanbul, Turkey	41.0082000	28.9784000	planned	IST	planned	\N	2026-05-29 02:11:18.902214+00
es2015-63	earth-sandwich-2015	2016-05-16	Aegean Coast, Turkey	38.4192000	27.1287000	planned	ADB	planned	Exploring the Aegean coastline	2026-05-29 02:11:18.902214+00
es2015-64	earth-sandwich-2015	2016-05-23	Greek Islands, Greece	36.3932000	25.4615000	planned	JTR	planned	Island hopping in the Aegean	2026-05-29 02:11:18.902214+00
es2015-65	earth-sandwich-2015	2016-05-30	Athens, Greece	37.9838000	23.7275000	planned	ATH	planned	\N	2026-05-29 02:11:18.902214+00
es2015-66	earth-sandwich-2015	2016-06-06	Sofia, Bulgaria	42.6977000	23.3219000	planned	SOF	planned	\N	2026-05-29 02:11:18.902214+00
es2015-67	earth-sandwich-2015	2016-06-09	Belgrade, Serbia	44.7866000	20.4489000	planned	BEG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-68	earth-sandwich-2015	2016-06-13	Sarajevo, Bosnia and Herzegovina	43.8486000	18.3564000	planned	SJJ	planned	\N	2026-05-29 02:11:18.902214+00
es2015-69	earth-sandwich-2015	2016-06-20	Mostar, Bosnia and Herzegovina	43.3438000	17.8078000	planned	DBV	planned	\N	2026-05-29 02:11:18.902214+00
es2015-70	earth-sandwich-2015	2016-06-23	Dubrovnik, Croatia	42.6507000	18.0944000	planned	DBV	planned	\N	2026-05-29 02:11:18.902214+00
es2015-71	earth-sandwich-2015	2016-06-27	Hvar, Croatia	43.1729000	16.4412000	planned	SPU	planned	The Hvar Islands	2026-05-29 02:11:18.902214+00
es2015-72	earth-sandwich-2015	2016-07-01	Plitvice Lakes, Croatia	44.8654000	15.5820000	planned	ZAG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-73	earth-sandwich-2015	2016-07-04	Budapest, Hungary	47.4979000	19.0402000	planned	BUD	planned	\N	2026-05-29 02:11:18.902214+00
es2015-74	earth-sandwich-2015	2016-07-11	Vienna, Austria	48.2082000	16.3738000	planned	VIE	planned	\N	2026-05-29 02:11:18.902214+00
es2015-75	earth-sandwich-2015	2016-07-18	Prague, Czech Republic	50.0755000	14.4378000	planned	PRG	planned	\N	2026-05-29 02:11:18.902214+00
es2015-76	earth-sandwich-2015	2016-07-25	Dresden, Germany	51.0509000	13.7383000	planned	DRS	planned	\N	2026-05-29 02:11:18.902214+00
es2015-77	earth-sandwich-2015	2016-07-25	Berlin, Germany	52.5200000	13.4050000	planned	BER	planned	\N	2026-05-29 02:11:18.902214+00
es2015-78	earth-sandwich-2015	2016-08-01	Warsaw, Poland	52.2297000	21.0122000	planned	WAW	planned	\N	2026-05-29 02:11:18.902214+00
es2015-79	earth-sandwich-2015	2016-08-04	Kraków, Poland	50.0647000	19.9450000	planned	KRK	planned	\N	2026-05-29 02:11:18.902214+00
es2015-80	earth-sandwich-2015	2016-08-08	Riga, Latvia	56.9496000	24.1052000	planned	RIX	planned	\N	2026-05-29 02:11:18.902214+00
es2015-81	earth-sandwich-2015	2016-08-11	Stockholm, Sweden	59.3293000	18.0686000	planned	ARN	planned	\N	2026-05-29 02:11:18.902214+00
es2015-82	earth-sandwich-2015	2016-08-15	New York, USA	40.7128000	-74.0060000	planned	JFK	planned	\N	2026-05-29 02:11:18.902214+00
es2015-ig-74	earth-sandwich-2015	2016-06-15	Prague, Czech Republic	50.0755000	14.4378000	visited	PRG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-75	earth-sandwich-2015	2016-06-15	Vršovice, Prague	50.0708000	14.4640000	visited	PRG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-76	earth-sandwich-2015	2016-06-14	Sedlec Ossuary, Kutná Hora	49.9608000	15.2884000	visited	PRG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-77	earth-sandwich-2015	2016-06-11	St. Stephen's Basilica, Budapest	47.5009000	19.0537000	visited	BUD	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-78	earth-sandwich-2015	2016-06-11	Fisherman's Bastion, Budapest	47.5021000	19.0349000	visited	BUD	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-79	earth-sandwich-2015	2016-06-09	Vienna State Opera	48.2025000	16.3691000	visited	VIE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-81	earth-sandwich-2015	2016-06-04	Latin Bridge, Sarajevo	43.8579000	18.4287000	visited	SJJ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-82	earth-sandwich-2015	2016-06-02	Trsteno Arboretum, Croatia	42.7178000	17.9636000	visited	DBV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-83	earth-sandwich-2015	2016-06-01	Dubrovnik, Croatia	42.6507000	18.0944000	visited	DBV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-84	earth-sandwich-2015	2016-06-01	Dubrovnik Old Town City Wall	42.6418000	18.1094000	visited	DBV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-85	earth-sandwich-2015	2016-05-28	Victoria Park, Athens	37.9914000	23.7335000	visited	ATH	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-86	earth-sandwich-2015	2016-05-26	Athens International Airport	37.9364000	23.9445000	visited	ATH	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-87	earth-sandwich-2015	2016-05-26	Blue Mosque, Istanbul	41.0054000	28.9768000	visited	IST	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-88	earth-sandwich-2015	2016-05-26	İstanbul Sabiha Gökçen International Airport	40.8986000	29.3092000	visited	IST	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-89	earth-sandwich-2015	2016-05-25	Hagia Sophia, Istanbul	41.0086000	28.9802000	visited	IST	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-91	earth-sandwich-2015	2016-05-24	Istiklal Street, Istanbul	41.0339000	28.9776000	visited	IST	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-92	earth-sandwich-2015	2016-05-22	Pamukkale, Turkey	37.9203000	29.1186000	visited	DNZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-93	earth-sandwich-2015	2016-05-22	Pamukkale, Turkey	37.9203000	29.1186000	visited	DNZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-94	earth-sandwich-2015	2016-05-19	Uchisar, Cappadocia	38.6300000	34.8064000	visited	ASR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-95	earth-sandwich-2015	2016-05-19	Uchisar, Cappadocia	38.6300000	34.8064000	visited	ASR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-96	earth-sandwich-2015	2016-05-17	Zelve Valley, Cappadocia	38.6764000	34.8458000	visited	ASR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-97	earth-sandwich-2015	2016-05-17	Paşabağ, Ürgüp	38.6589000	34.8431000	visited	ASR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-98	earth-sandwich-2015	2016-05-17	Derinkuyu Underground City	38.3725000	34.7350000	visited	ASR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-99	earth-sandwich-2015	2016-05-12	Kekova Island, Turkey	36.1881000	29.8597000	visited	AYT	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-102	earth-sandwich-2015	2016-05-04	Jerusalem, Israel	31.7683000	35.2137000	visited	TLV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-103	earth-sandwich-2015	2016-05-04	Tel Aviv, Israel	32.0853000	34.7818000	visited	TLV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-104	earth-sandwich-2015	2016-05-01	Jerusalem Central Bus Station	31.7891000	35.2032000	visited	TLV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-105	earth-sandwich-2015	2016-04-29	Mount Zion, Jerusalem	31.7715000	35.2287000	visited	TLV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-106	earth-sandwich-2015	2016-04-25	Wadi Rum, Jordan	29.5333000	35.4167000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-107	earth-sandwich-2015	2016-04-24	Wadi Rum, Jordan	29.5333000	35.4167000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-108	earth-sandwich-2015	2016-04-24	Wadi Rum, Jordan	29.5333000	35.4167000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-109	earth-sandwich-2015	2016-04-24	Dead Sea, Jordan	31.5590000	35.4732000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-110	earth-sandwich-2015	2016-04-23	Galleria Mall, Amman, Jordan	31.9700000	35.8500000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-111	earth-sandwich-2015	2016-04-22	Petra, Ma'an, Jordan	30.3285000	35.4444000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-112	earth-sandwich-2015	2016-04-22	Amman, Jordan	31.9539000	35.9106000	visited	AMM	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-113	earth-sandwich-2015	2016-04-17	Karnak Temple, Luxor	25.7188000	32.6573000	visited	LXR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-114	earth-sandwich-2015	2016-04-13	Winter Palace, Luxor	25.6982000	32.6396000	visited	LXR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-115	earth-sandwich-2015	2016-04-12	Nile River, Egypt	25.6900000	32.6500000	visited	ASW	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-116	earth-sandwich-2015	2016-04-09	Philae Temple, Egypt	24.0252000	32.8843000	visited	ASW	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-117	earth-sandwich-2015	2016-04-08	Cairo International Airport	30.1219000	31.4056000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-118	earth-sandwich-2015	2016-04-07	Mansheya Nasir, Cairo	30.0444000	31.2828000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-119	earth-sandwich-2015	2016-04-06	Al Jame Anwar, Cairo	30.0476000	31.2628000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-120	earth-sandwich-2015	2016-04-05	Mosque-Madrassa of Sultan Hassan, Cairo	30.0317000	31.2563000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-121	earth-sandwich-2015	2016-04-05	Saqqara Pyramid, Egypt	29.8714000	31.2168000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-122	earth-sandwich-2015	2016-04-04	Great Pyramids of Giza	29.9792000	31.1342000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-123	earth-sandwich-2015	2016-04-04	Cairo, Egypt	30.0444000	31.2357000	visited	CAI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-124	earth-sandwich-2015	2016-04-03	Milford Sound, Fiordland National Park	-44.6717000	167.9272000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-125	earth-sandwich-2015	2016-04-03	Daintree Rainforest, Australia	-16.0883000	145.4517000	visited	CNS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-126	earth-sandwich-2015	2016-04-03	Chillagoe & Mungana Caves, Australia	-17.1556000	144.5226000	visited	CNS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-127	earth-sandwich-2015	2016-04-02	Port Douglas, Queensland, Australia	-16.4865000	145.4631000	visited	CNS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-128	earth-sandwich-2015	2016-04-02	Great Barrier Reef, Australia	-16.5045000	146.0245000	visited	CNS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-129	earth-sandwich-2015	2016-03-29	Queenstown, New Zealand	-45.0312000	168.6626000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-130	earth-sandwich-2015	2016-03-29	Bondi Beach, Sydney	-33.8915000	151.2767000	visited	SYD	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-131	earth-sandwich-2015	2016-03-29	Wildlife Habitat, Port Douglas	-16.4830000	145.4675000	visited	CNS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-132	earth-sandwich-2015	2016-03-28	Bondi Beach, Sydney	-33.8915000	151.2767000	visited	SYD	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-133	earth-sandwich-2015	2016-03-26	Scenic World Blue Mountains, Australia	-33.7287000	150.3013000	visited	SYD	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-134	earth-sandwich-2015	2016-03-21	Bondi Beach, Sydney	-33.8915000	151.2767000	visited	SYD	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-135	earth-sandwich-2015	2016-03-19	Arrowtown, South Island, New Zealand	-44.9342000	168.8313000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-136	earth-sandwich-2015	2016-03-18	Kiwi Birdlife Park, Queenstown	-44.9358000	168.8330000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-137	earth-sandwich-2015	2016-03-17	Milford Sound, Fiordland National Park	-44.6717000	167.9272000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-140	earth-sandwich-2015	2016-03-15	Half-Moon Bay, Stewart Island, New Zealand	-46.8950000	168.1295000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-141	earth-sandwich-2015	2016-03-15	Kaikoura Coast Track, New Zealand	-42.4047000	173.6808000	visited	CHC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-142	earth-sandwich-2015	2016-03-15	Kaikoura Coast Track, New Zealand	-42.4047000	173.6808000	visited	CHC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-143	earth-sandwich-2015	2016-03-15	Lake Matheson, New Zealand	-43.4490000	169.9580000	visited	CHC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-144	earth-sandwich-2015	2016-03-15	Arrowtown, South Island, New Zealand	-44.9342000	168.8313000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-80	earth-sandwich-2015	2016-06-05	Military Museum, Kalemegdan, Belgrade	44.8230000	20.4480000	visited	BEG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-90	earth-sandwich-2015	2016-05-24	Istanbul, Turkey	41.0082000	28.9784000	visited	IST	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-100	earth-sandwich-2015	2016-05-08	Perge Ancient City, Antalya, Turkey	36.9609000	30.8541000	visited	AYT	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-101	earth-sandwich-2015	2016-05-04	Dome of the Rock, Temple Mount, Jerusalem	31.7780000	35.2354000	visited	TLV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-138	earth-sandwich-2015	2016-03-16	Little Paradise Lodge & Gardens, Glenorchy, New Zealand	-44.8906000	168.4196000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-139	earth-sandwich-2015	2016-03-16	Little Paradise Lodge & Gardens, Glenorchy, New Zealand	-44.8906000	168.4196000	visited	ZQN	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-145	earth-sandwich-2015	2016-03-04	Weta Cave, Miramar, Wellington	-41.3175000	174.8252000	visited	WLG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-146	earth-sandwich-2015	2016-03-04	Weta Cave, Miramar, Wellington	-41.3175000	174.8252000	visited	WLG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-147	earth-sandwich-2015	2016-03-04	Sheepworld Farm Park, New Zealand	-36.3550000	174.6230000	visited	AKL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-148	earth-sandwich-2015	2016-03-04	Little Earth Lodge, Whangārei	-35.7333000	174.3000000	visited	AKL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-149	earth-sandwich-2015	2016-03-04	Tongariro Alpine Crossing, New Zealand	-39.1336000	175.6589000	visited	TRG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-150	earth-sandwich-2015	2016-02-26	Auckland Museum	-36.8603000	174.7777000	visited	AKL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-151	earth-sandwich-2015	2016-02-26	Ace Rental Cars, Auckland	-36.8485000	174.7633000	visited	AKL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-152	earth-sandwich-2015	2016-02-26	Kitekite Falls, Piha, New Zealand	-36.9505000	174.4762000	visited	AKL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-153	earth-sandwich-2015	2016-02-23	Cristo Redentor, Rio de Janeiro, Brazil	-22.9519000	-43.2105000	visited	GIG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-154	earth-sandwich-2015	2016-02-15	Palacio de las Aguas Corrientes, Buenos Aires	-34.6005000	-58.3939000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-155	earth-sandwich-2015	2016-02-13	Cementerio de la Recoleta, Buenos Aires	-34.5876000	-58.3936000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-156	earth-sandwich-2015	2016-02-09	Puerto Iguazú, Argentina	-25.5996000	-54.5742000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-157	earth-sandwich-2015	2016-02-09	Barrio Chino, Barrancas de Belgrano, Buenos Aires	-34.5615000	-58.4527000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-158	earth-sandwich-2015	2016-02-09	Buenos Aires, Argentina	-34.6037000	-58.3816000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-159	earth-sandwich-2015	2016-02-03	Buenos Aires, Argentina	-34.6037000	-58.3816000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-160	earth-sandwich-2015	2016-02-03	Buenos Aires, Argentina	-34.6037000	-58.3816000	visited	EZE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-161	earth-sandwich-2015	2016-02-01	Andes Mountains, Argentina	-32.5000000	-69.5000000	visited	MDZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-162	earth-sandwich-2015	2016-02-01	Maipo Valley, Chile	-33.7167000	-70.6500000	visited	SCL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-163	earth-sandwich-2015	2016-02-01	Mendoza, Argentina	-32.8908000	-68.8272000	visited	MDZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-164	earth-sandwich-2015	2016-02-01	Cerro Santa Lucía, Santiago, Chile	-33.4396000	-70.6435000	visited	SCL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-165	earth-sandwich-2015	2016-01-27	Volcán Osorno, Puerto Varas, Chile	-41.1000000	-72.4933000	visited	PMC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-166	earth-sandwich-2015	2016-01-27	Santiago, Chile	-33.4489000	-70.6693000	visited	SCL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-167	earth-sandwich-2015	2016-01-27	Museo Chileno de Arte Precolombino, Santiago	-33.4378000	-70.6534000	visited	SCL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-168	earth-sandwich-2015	2016-01-27	Museo Chileno de Arte Precolombino, Santiago	-33.4378000	-70.6534000	visited	SCL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-169	earth-sandwich-2015	2016-01-20	Ensenada, Los Lagos, Chile	-41.2000000	-72.5333000	visited	PMC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-170	earth-sandwich-2015	2016-01-13	Sopocachi, La Paz, Bolivia	-16.5067000	-68.1278000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-172	earth-sandwich-2015	2016-01-11	El Alto, Bolivia	-16.5000000	-68.1667000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-173	earth-sandwich-2015	2016-01-11	La Paz, Bolivia	-16.4897000	-68.1193000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-174	earth-sandwich-2015	2016-01-10	Copacabana, Bolivia	-16.1660000	-69.0876000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-175	earth-sandwich-2015	2016-01-10	Lake Titicaca, Copacabana, Bolivia	-15.9255000	-69.3354000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-176	earth-sandwich-2015	2016-01-10	La Paz, Bolivia	-16.4897000	-68.1193000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-177	earth-sandwich-2015	2016-01-06	Vila Madalena, São Paulo	-23.5454000	-46.6906000	visited	GRU	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-178	earth-sandwich-2015	2016-01-06	São Paulo, Brazil	-23.5505000	-46.6333000	visited	GRU	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-179	earth-sandwich-2015	2016-01-06	Open Spanish ELE School, Sucre, Bolivia	-19.0331000	-65.2627000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-180	earth-sandwich-2015	2016-01-06	Train Cemetery, Uyuni, Bolivia	-20.4859000	-66.8268000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-181	earth-sandwich-2015	2016-01-06	Salvador Dalí Desert, Bolivia	-22.0500000	-67.7000000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-182	earth-sandwich-2015	2016-01-06	Death Road, La Paz, Bolivia	-16.3333000	-67.7833000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-183	earth-sandwich-2015	2016-01-06	Death Road, La Paz, Bolivia	-16.3333000	-67.7833000	visited	LPB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-184	earth-sandwich-2015	2016-01-04	Salar de Uyuni, Bolivia	-20.1338000	-67.4891000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-185	earth-sandwich-2015	2016-01-04	Reserva Eduardo Avaroa, Bolivia	-22.7333000	-67.6500000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-186	earth-sandwich-2015	2015-12-31	Sucre, Bolivia	-19.0431000	-65.2592000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-187	earth-sandwich-2015	2015-12-31	Salar de Uyuni, Bolivia	-20.1338000	-67.4891000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-188	earth-sandwich-2015	2015-12-23	Viru Viru International Airport, Santa Cruz, Bolivia	-17.6448000	-63.1354000	visited	SRE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-189	earth-sandwich-2015	2015-12-09	Amazon Forest	-3.5000000	-60.0000000	visited	MAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-190	earth-sandwich-2015	2015-12-09	Amazon Forest	-3.5000000	-60.0000000	visited	MAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-191	earth-sandwich-2015	2015-12-09	Amazon Forest	-3.5000000	-60.0000000	visited	MAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-192	earth-sandwich-2015	2015-12-09	Amazon Forest	-3.5000000	-60.0000000	visited	MAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-193	earth-sandwich-2015	2015-12-09	Leticia, Amazonas, Colombia	-4.2153000	-69.9406000	visited	LET	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-194	earth-sandwich-2015	2015-12-09	Bosque da Ciência - INPA, Manaus	-3.0961000	-59.9866000	visited	MAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-195	earth-sandwich-2015	2015-12-09	Confeitaria Colombo, Rio de Janeiro	-22.9050000	-43.1762000	visited	GIG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-196	earth-sandwich-2015	2015-12-09	Escadaria Selarón, Rio de Janeiro	-22.9152000	-43.1791000	visited	GIG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-197	earth-sandwich-2015	2015-11-21	Cartagena, Colombia	10.3910000	-75.4794000	visited	CTG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-198	earth-sandwich-2015	2015-11-21	Cartagena, Colombia	10.3910000	-75.4794000	visited	CTG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-199	earth-sandwich-2015	2015-11-19	Hacienda Venecia Coffee Farm, Colombia	5.0394000	-75.6333000	visited	PEI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-200	earth-sandwich-2015	2015-11-19	Hacienda Venecia Coffee Farm, Colombia	5.0394000	-75.6333000	visited	PEI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-201	earth-sandwich-2015	2015-11-19	Hacienda Venecia Coffee Farm, Colombia	5.0394000	-75.6333000	visited	PEI	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-202	earth-sandwich-2015	2015-11-15	Salt Cathedral of Zipaquirá, Colombia	5.0186000	-74.0008000	visited	BOG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-203	earth-sandwich-2015	2015-11-12	Havana, Cuba	23.1136000	-82.3666000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-204	earth-sandwich-2015	2015-11-12	Gimnasio de Boxeo Rafael Trejo, Havana	23.1346000	-82.3597000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-205	earth-sandwich-2015	2015-11-12	Havana, Cuba	23.1136000	-82.3666000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-206	earth-sandwich-2015	2015-11-12	Havana, Cuba	23.1136000	-82.3666000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-207	earth-sandwich-2015	2015-11-12	Viñales, Cuba	22.6167000	-83.7167000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-208	earth-sandwich-2015	2015-11-12	Havana, Cuba	23.1136000	-82.3666000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-209	earth-sandwich-2015	2015-11-12	Havana, Cuba	23.1136000	-82.3666000	visited	HAV	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-210	earth-sandwich-2015	2015-11-03	Wangfujing Night Market, Beijing	39.9099000	116.4154000	visited	PEK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-211	earth-sandwich-2015	2015-11-03	Great Wall of China, Jinshanling	40.6796000	117.2403000	visited	PEK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-212	earth-sandwich-2015	2015-11-03	Taipei 101 Mall, Taipei	25.0334000	121.5645000	visited	TPE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-213	earth-sandwich-2015	2015-11-03	Taipei, Taiwan	25.0330000	121.5654000	visited	TPE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-214	earth-sandwich-2015	2015-11-03	New Orleans, Louisiana, USA	29.9511000	-90.0715000	visited	MSY	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-215	earth-sandwich-2015	2015-10-25	Sanho Night Market, Taipei	25.0359000	121.5388000	visited	TPE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-216	earth-sandwich-2015	2015-10-25	228 Peace Memorial Park, Taipei	25.0420000	121.5158000	visited	TPE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-217	earth-sandwich-2015	2015-10-25	Taipei, Taiwan	25.0330000	121.5654000	visited	TPE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-218	earth-sandwich-2015	2015-10-25	Taipei, Taiwan	25.0330000	121.5654000	visited	TPE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-219	earth-sandwich-2015	2015-10-22	Yangshuo, China	24.7751000	110.4935000	visited	KWL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-220	earth-sandwich-2015	2015-10-21	Yangshuo, China	24.7751000	110.4935000	visited	KWL	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-221	earth-sandwich-2015	2015-10-20	Jianguo Hotel, Shanghai	31.2178000	121.4403000	visited	PVG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-222	earth-sandwich-2015	2015-10-20	Temple of Heaven, Beijing	39.8822000	116.4066000	visited	PEK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-223	earth-sandwich-2015	2015-10-20	Beijing, China	39.9042000	116.4074000	visited	PEK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-224	earth-sandwich-2015	2015-09-30	San Bartolomeo all'Isola, Rome	41.8908000	12.4773000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-225	earth-sandwich-2015	2015-09-30	Colosseum, Rome	41.8902000	12.4922000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-226	earth-sandwich-2015	2015-09-30	Sistine Chapel, Vatican City	41.9029000	12.4545000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-227	earth-sandwich-2015	2015-09-30	St Peter's Basilica, Vatican City	41.9022000	12.4533000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-228	earth-sandwich-2015	2015-09-30	Rome, Italy	41.9028000	12.4964000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-229	earth-sandwich-2015	2015-09-26	Rome, Italy	41.9028000	12.4964000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-230	earth-sandwich-2015	2015-09-26	Rome, Italy	41.9028000	12.4964000	visited	FCO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-231	earth-sandwich-2015	2015-09-22	Leaning Tower of Pisa	43.7230000	10.3966000	visited	FLR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-232	earth-sandwich-2015	2015-09-22	Riomaggiore, Cinque Terre, Italy	44.0995000	9.7375000	visited	FLR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-233	earth-sandwich-2015	2015-09-20	Mercato Centrale, Florence	43.7768000	11.2542000	visited	FLR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-234	earth-sandwich-2015	2015-09-20	Leonardo da Vinci Museum, Florence	43.7740000	11.2580000	visited	FLR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-235	earth-sandwich-2015	2015-09-19	Towers of Bologna	44.4945000	11.3461000	visited	BLQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-236	earth-sandwich-2015	2015-09-19	Piazza Maggiore, Bologna	44.4935000	11.3433000	visited	BLQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-237	earth-sandwich-2015	2015-09-19	San Petronio Basilica, Bologna	44.4928000	11.3433000	visited	BLQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-238	earth-sandwich-2015	2015-09-19	Bologna, Italy	44.4949000	11.3426000	visited	BLQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-239	earth-sandwich-2015	2015-09-15	Torre degli Asinelli, Bologna	44.4945000	11.3461000	visited	BLQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-240	earth-sandwich-2015	2015-09-15	Venezia Mestre Railway Station	45.4823000	12.2350000	visited	VCE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-241	earth-sandwich-2015	2015-09-13	Venice, Italy	45.4408000	12.3155000	visited	VCE	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-242	earth-sandwich-2015	2015-09-12	Red Bull Hangar-7, Salzburg	47.7937000	13.0042000	visited	SZG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-243	earth-sandwich-2015	2015-09-12	Mirabellgarten, Salzburg	47.8050000	13.0442000	visited	SZG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-244	earth-sandwich-2015	2015-09-10	Alpsee, Hohenschwangau, Germany	47.5563000	10.7384000	visited	MUC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-245	earth-sandwich-2015	2015-09-10	Neuschwanstein Castle, Füssen, Germany	47.5576000	10.7498000	visited	MUC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-246	earth-sandwich-2015	2015-09-10	Englischer Garten, Munich	48.1642000	11.6056000	visited	MUC	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-247	earth-sandwich-2015	2015-09-06	Grand Place, Brussels	50.8467000	4.3517000	visited	BRU	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-248	earth-sandwich-2015	2015-09-06	Brussels, Belgium	50.8503000	4.3517000	visited	BRU	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-249	earth-sandwich-2015	2015-09-06	Luxembourg City Park	49.6117000	6.1319000	visited	LUX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-250	earth-sandwich-2015	2015-09-06	Luxembourg City, Luxembourg	49.6117000	6.1319000	visited	LUX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-251	earth-sandwich-2015	2015-09-06	Heidelberg Castle, Germany	49.4106000	8.7156000	visited	FRA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-252	earth-sandwich-2015	2015-09-06	Heidelberg, Germany	49.3988000	8.6724000	visited	FRA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-253	earth-sandwich-2015	2015-08-28	Amsterdam, Netherlands	52.3676000	4.9041000	visited	AMS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-254	earth-sandwich-2015	2015-08-28	Tulip Market, Amsterdam	52.3679000	4.8852000	visited	AMS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-255	earth-sandwich-2015	2015-08-26	Place Jemâa el-Fna, Marrakech	31.6258000	-7.9893000	visited	RAK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-256	earth-sandwich-2015	2015-08-25	Merzouga, Sahara Desert, Morocco	31.0993000	-4.0118000	visited	RAK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-257	earth-sandwich-2015	2015-08-24	Merzouga, Sahara Desert, Morocco	31.0993000	-4.0118000	visited	RAK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-258	earth-sandwich-2015	2015-08-23	Fez, Morocco	34.0181000	-5.0078000	visited	FEZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-259	earth-sandwich-2015	2015-08-21	Riad Idrissy & The Ruined Garden, Fez	34.0631000	-4.9750000	visited	FEZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-260	earth-sandwich-2015	2015-08-20	Medina of Tetouan, Morocco	35.5757000	-5.3725000	visited	TNG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-261	earth-sandwich-2015	2015-08-19	Fez, Morocco	34.0181000	-5.0078000	visited	FEZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-262	earth-sandwich-2015	2015-08-18	Medina of Tetouan, Morocco	35.5757000	-5.3725000	visited	TNG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-263	earth-sandwich-2015	2015-08-18	Medina of Tetouan, Morocco	35.5757000	-5.3725000	visited	TNG	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-264	earth-sandwich-2015	2015-08-18	Rock of Gibraltar	36.1408000	-5.3536000	visited	AGP	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-265	earth-sandwich-2015	2015-08-17	Palacios Nazaríes, Alhambra, Granada	37.1773000	-3.5896000	visited	GRX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-266	earth-sandwich-2015	2015-08-17	Alhambra, Granada, Spain	37.1773000	-3.5896000	visited	GRX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-267	earth-sandwich-2015	2015-08-16	Granada, Spain	37.1773000	-3.5986000	visited	GRX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-268	earth-sandwich-2015	2015-08-15	Granada, Spain	37.1773000	-3.5986000	visited	GRX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-269	earth-sandwich-2015	2015-08-15	Granada, Spain	37.1773000	-3.5986000	visited	GRX	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-270	earth-sandwich-2015	2015-08-14	Plaza de Toros de la Real Maestranza, Seville	37.3866000	-6.0027000	visited	SVQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-271	earth-sandwich-2015	2015-08-14	Plaza de España, Seville	37.3772000	-5.9870000	visited	SVQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-272	earth-sandwich-2015	2015-08-11	Maria Luisa Park, Seville	37.3741000	-5.9882000	visited	SVQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-273	earth-sandwich-2015	2015-08-11	Tiana, Catalonia, Spain	41.4842000	2.2697000	visited	SVQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-274	earth-sandwich-2015	2015-08-11	Giralda, Seville Cathedral	37.3858000	-5.9926000	visited	SVQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-275	earth-sandwich-2015	2015-08-10	Lagos, Portugal	37.1017000	-8.6731000	visited	FAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-276	earth-sandwich-2015	2015-08-10	Spain	37.3886000	-5.9823000	visited	SVQ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-277	earth-sandwich-2015	2015-08-09	Lagos, Portugal	37.1017000	-8.6731000	visited	FAO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-278	earth-sandwich-2015	2015-08-06	Chiado, Lisbon	38.7106000	-9.1422000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-279	earth-sandwich-2015	2015-08-05	Sintra, Portugal	38.8029000	-9.3817000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-280	earth-sandwich-2015	2015-08-05	Cruz Alta, Pena Park, Sintra	38.7878000	-9.3895000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-281	earth-sandwich-2015	2015-08-05	Palácio da Pena, Sintra	38.7878000	-9.3905000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-282	earth-sandwich-2015	2015-08-05	Pena Palace, Sintra	38.7878000	-9.3905000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-283	earth-sandwich-2015	2015-08-05	Monserrate Palace, Sintra	38.7920000	-9.4189000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-284	earth-sandwich-2015	2015-08-04	Alfama, Lisbon, Portugal	38.7115000	-9.1305000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-285	earth-sandwich-2015	2015-08-04	Chiado, Lisbon	38.7106000	-9.1422000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-286	earth-sandwich-2015	2015-08-04	Rua da Bica de Duarte Belo, Lisbon	38.7104000	-9.1456000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-287	earth-sandwich-2015	2015-08-03	Ruínas do Convento do Carmo, Lisbon	38.7126000	-9.1408000	visited	LIS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-288	earth-sandwich-2015	2015-08-02	Powerscourt Gardens, Wicklow, Ireland	53.1856000	-6.1907000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-289	earth-sandwich-2015	2015-08-02	Powerscourt Gardens, Wicklow, Ireland	53.1856000	-6.1907000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-290	earth-sandwich-2015	2015-08-01	Guinness Storehouse, Dublin	53.3419000	-6.2867000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-291	earth-sandwich-2015	2015-07-31	Dublin, Ireland	53.3498000	-6.2603000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-292	earth-sandwich-2015	2015-07-31	Long Room Library, Trinity College, Dublin	53.3441000	-6.2575000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-293	earth-sandwich-2015	2015-07-31	The Cobblestone, Dublin	53.3491000	-6.2766000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-294	earth-sandwich-2015	2015-07-30	Galway, Ireland	53.2707000	-9.0568000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-295	earth-sandwich-2015	2015-07-30	Dublin, Ireland	53.3498000	-6.2603000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-296	earth-sandwich-2015	2015-07-29	Dublin, Ireland	53.3498000	-6.2603000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-297	earth-sandwich-2015	2015-07-29	Saint Patrick's Cathedral, Dublin	53.3399000	-6.2710000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-298	earth-sandwich-2015	2015-07-29	Dublin, Ireland	53.3498000	-6.2603000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-299	earth-sandwich-2015	2015-07-29	Dublin, Ireland	53.3498000	-6.2603000	visited	DUB	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-300	earth-sandwich-2015	2015-07-27	Toronto, Ontario	43.6532000	-79.3832000	visited	YYZ	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-301	earth-sandwich-2015	2015-07-26	Compass Point Beach Resort, Bahamas	25.0822000	-77.4084000	visited	NAS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-302	earth-sandwich-2015	2015-07-26	Compass Point Beach Resort, Bahamas	25.0822000	-77.4084000	visited	NAS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-303	earth-sandwich-2015	2015-07-23	Compass Cay, Exuma, Bahamas	24.2778000	-76.5097000	visited	NAS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-304	earth-sandwich-2015	2015-07-17	Seattle Aquarium	47.6076000	-122.3429000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-305	earth-sandwich-2015	2015-07-17	Alki Beach Park, Seattle	47.5794000	-122.4090000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-306	earth-sandwich-2015	2015-07-17	Alki Beach Park, Seattle	47.5794000	-122.4090000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-307	earth-sandwich-2015	2015-07-17	Alki Beach Park, Seattle	47.5794000	-122.4090000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-308	earth-sandwich-2015	2015-07-15	Vancouver International Airport, Canada	49.1939000	-123.1844000	visited	YVR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-309	earth-sandwich-2015	2015-07-11	Seattle, Washington, USA	47.6062000	-122.3321000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-310	earth-sandwich-2015	2015-07-11	Seattle, Washington, USA	47.6062000	-122.3321000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-311	earth-sandwich-2015	2015-07-08	Seattle, Washington, USA	47.6062000	-122.3321000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-312	earth-sandwich-2015	2015-07-07	Seattle, Washington, USA	47.6062000	-122.3321000	visited	SEA	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-313	earth-sandwich-2015	2015-07-04	Vancouver, Canada	49.2827000	-123.1207000	visited	YVR	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-315	earth-sandwich-2015	2015-06-29	Las Vegas, Nevada, USA	36.1147000	-115.1728000	visited	LAS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-316	earth-sandwich-2015	2015-06-27	Las Vegas, Nevada, USA	36.1147000	-115.1728000	visited	LAS	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-317	earth-sandwich-2015	2015-06-26	San Francisco International Airport, USA	37.6213000	-122.3790000	visited	SFO	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-318	earth-sandwich-2015	2015-06-26	JFK Airport, New York	40.6413000	-73.7781000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-319	earth-sandwich-2015	2015-06-26	New York, New York	40.7128000	-74.0060000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-320	earth-sandwich-2015	2015-06-25	New York, New York	40.7128000	-74.0060000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-321	earth-sandwich-2015	2015-06-25	New York, New York	40.7128000	-74.0060000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-ig-322	earth-sandwich-2015	2015-06-21	New York Harbor, New York	40.6892000	-74.0445000	visited	JFK	instagram	\N	2026-05-29 02:11:18.902214+00
es2015-sub-china	earth-sandwich-2015	2016-01-06	Shanghai, China	31.2304000	121.4737000	visited	PVG	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-italy	earth-sandwich-2015	2016-01-06	Venice, Italy	45.4408000	12.3155000	visited	VCE	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-austria	earth-sandwich-2015	2016-01-06	Salzburg, Austria	47.8095000	13.0550000	visited	SZG	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-germany-west	earth-sandwich-2015	2016-01-06	Heidelberg, Germany	49.3988000	8.6724000	visited	FRA	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-luxembourg	earth-sandwich-2015	2016-01-06	Luxembourg City, Luxembourg	49.6117000	6.1319000	visited	LUX	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-uruguay	earth-sandwich-2015	2016-02-17	Colonia del Sacramento, Uruguay	-34.4710000	-57.8430000	visited	EZE	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-argentina	earth-sandwich-2015	2016-02-15	Mendoza, Argentina	-32.8908000	-68.8272000	visited	MDZ	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-travel-safety	earth-sandwich-2015	2016-01-28	Santiago, Chile	-33.4489000	-70.6693000	visited	SCL	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-chile	earth-sandwich-2015	2016-01-19	San Pedro de Atacama, Chile	-22.9090000	-68.1996000	visited	IQQ	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-bolivia	earth-sandwich-2015	2016-01-19	Sucre, Bolivia	-19.0431000	-65.2592000	visited	SRE	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-the-demon	earth-sandwich-2015	2016-09-15	Seattle, Washington, USA	47.6062000	-122.3321000	visited	SEA	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-uncertainty	earth-sandwich-2015	2016-08-01	Montreal, Canada	45.5017000	-73.5673000	visited	YYZ	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-prologue	earth-sandwich-2015	2016-07-07	Edmonton, Canada	53.5461000	-113.4938000	visited	YVR	substack	\N	2026-05-29 02:11:18.902214+00
es2015-sub-epilogue	earth-sandwich-2015	2016-07-05	Seattle, Washington, USA	47.6062000	-122.3321000	visited	SEA	substack	\N	2026-05-29 02:11:18.902214+00
ecs2027-01	earth-club-sandwich-2027	2027-03-26	Estepona, Spain	36.4267000	-5.1494000	planned	AGP	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-02	earth-club-sandwich-2027	2027-07-01	Japan	35.6762000	139.6503000	planned	NRT	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-03	earth-club-sandwich-2027	2027-08-01	Nepal	27.7172000	85.3240000	planned	KTM	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-04	earth-club-sandwich-2027	2027-08-11	Bhutan	27.4728000	89.6393000	planned	PBH	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-05	earth-club-sandwich-2027	2027-08-21	Singapore	1.3521000	103.8198000	planned	SIN	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-06	earth-club-sandwich-2027	2027-08-31	Indonesia	-8.3405000	115.0920000	planned	DPS	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-07	earth-club-sandwich-2027	2027-09-10	Philippines	14.5995000	120.9842000	planned	MNL	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-08	earth-club-sandwich-2027	2027-09-20	Guam, USA	13.4443000	144.7937000	planned	GUM	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-09	earth-club-sandwich-2027	2027-09-30	Micronesia	6.8877000	158.2150000	planned	PNI	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-10	earth-club-sandwich-2027	2027-10-10	Hawaii, USA	21.3069000	-157.8583000	planned	HNL	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-11	earth-club-sandwich-2027	2027-12-24	Houston, Texas, USA	29.7604000	-95.3698000	planned	IAH	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-12	earth-club-sandwich-2027	2027-12-28	Galápagos Islands, Ecuador	-0.7395000	-90.3369000	planned	GPS	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-13	earth-club-sandwich-2027	2028-01-02	Patagonia, Argentina	-50.3373000	-72.2627000	planned	FTE	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-14	earth-club-sandwich-2027	2028-01-05	United Arab Emirates	25.2048000	55.2708000	planned	DXB	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-15	earth-club-sandwich-2027	2028-01-13	Qatar	25.2854000	51.5310000	planned	DOH	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-16	earth-club-sandwich-2027	2028-01-21	Bahrain	26.2235000	50.5876000	planned	BAH	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-17	earth-club-sandwich-2027	2028-01-29	Saudi Arabia	24.7136000	46.6753000	planned	RUH	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-18	earth-club-sandwich-2027	2028-02-06	South Africa	-33.9249000	18.4241000	planned	CPT	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-19	earth-club-sandwich-2027	2028-02-14	Botswana	-24.6282000	25.9231000	planned	GBE	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-20	earth-club-sandwich-2027	2028-02-22	Rwanda	-1.9441000	30.0619000	planned	KGL	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-21	earth-club-sandwich-2027	2028-03-01	Namibia	-22.5597000	17.0832000	planned	WDH	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-22	earth-club-sandwich-2027	2028-03-09	Istanbul, Turkey	41.0082000	28.9784000	planned	IST	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-23	earth-club-sandwich-2027	2028-03-17	Bulgaria	42.6977000	23.3219000	planned	SOF	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-24	earth-club-sandwich-2027	2028-03-25	Varna, Bulgaria	43.2141000	27.9147000	planned	VAR	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-25	earth-club-sandwich-2027	2028-04-02	Bucharest, Romania	44.4268000	26.1025000	planned	OTP	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-26	earth-club-sandwich-2027	2028-04-10	Armenia	40.1872000	44.5152000	planned	EVN	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-27	earth-club-sandwich-2027	2028-04-18	Uzbekistan	41.2995000	69.2401000	planned	TAS	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-28	earth-club-sandwich-2027	2028-04-26	Kazakhstan	43.2220000	76.8512000	planned	ALA	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-29	earth-club-sandwich-2027	2028-05-04	Kyrgyzstan	42.8746000	74.5698000	planned	FRU	planned	\N	2026-05-29 02:11:18.902214+00
ecs2027-30	earth-club-sandwich-2027	2028-05-12	Ürümqi, China	43.8256000	87.6168000	planned	URC	planned	\N	2026-05-29 02:11:18.902214+00
\.


--
-- Data for Name: substack_posts; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.substack_posts (id, stop_id, substack_id, title, subtitle, body, published_at, created_at) FROM stdin;
d9befc4f-0e9f-418d-b637-7b53e4530a3d	es2015-sub-china	seed:es2015-sub-china	China – Wela’s Memory Dump	\N	**Mainland**\n\nIt’s China, the motherland. There’s so much and so little to say. My heart has always been in Shanghai and the city is just getting better and better every year. This time even Ethan fell in love. Thanks Kath for showing him and all our guests the beauty of our hometown!\n\nWe had a hectic week of wedding planning in Shanghai before our guests arrived. The Jianguo Hotel, Cool Docks and Kartel really delivered for us. As did Ping Cheng Wu (Japanese Itzakaya) and Zhi Wei Guan in Hangzhou. Eat your heart out peoples!\n\nBeijing was still as loathsome as ever. Horribly rude cab drivers that just drop you in the middle of nowhere (sorry Kimbo!) and air so polluted you can’t breathe. The only redeeming thing about Beijing is the epic historical sites and of course the duck. But you can get that same duck in Markham at Chung King Garden. Amazing. Jacques, Clara and Ethan and I once ate two full ducks – three courses each, six courses total. Bless the day Dee Dee and I found this place so randomly! We thought the duck skin had cocaine in it – it was so crispy.\n\nYangshuo was SO WONDERFUL. The natural beauty was unparalleled. Aside from the episode where we thought Alice was kidnapped because she lost her phone and we couldn’t find her for like two days, the rest of Yangshuo was so fun. We climbed the TV tower, we floated down the Yu Long river on bamboo rafts, we ate really spicy Guangxi food and we visited hundred year old villages. We biked around and rode scooters and we ambled about the cute town center of Yangshuo. You can literally spend a month in this area ambling about enjoying the food and mountain scenery. With calls for a 5 year wedding vow renewal, we already spotted some swanky hotels that we could stay in and have our friends come join us at! This area was magical. Now if only they can decrease the smogginess.\n\nWe met a lady who was 90 years old in an ancient village around the area. She showed us her home which was super old and run down and she even showed us the plaque that an emperor had award her family which she had to flip backwards and use s a cutting board during the cultural revolution so that it wouldn’t be confiscated. Incredible.\n\nThe evening cormorant fishing trip great – man can these birds fish. I did feel kind of badly for them but I guess they get the smaller fish, the ones that they can swallow despite the ring around their necks.\n\nWe ate mostly at a place we called “Uncle’s Place” because it was owned by the uncle of the co-owner of the Riverside Dragon Hostel we stayed at. The place is actually called Long Men Nin Xiang Non Jia Fan (dragon door fragrant country cooking). The owners were so very sweet and the food was so very plentiful and yummy.\n\nChina is not cheap to travel in anymore. Things are pricey.\n\nPut lots of bug spray on! Alice got bitten up SO BAD and so did we but Ethan doesn’t react so much and I sprayed myself. Even then the sand fly bites were SO itchy and ten times worse than mosquito bites and took like a month to heal. I suspect we got bitten on the bamboo rafting trip.\n\nAlways carry with you toilet paper everywhere in China. This is getting better but still a must. Good advice for all non first world countries.\n\n**Taiwan**\n\nTaipei felt like a very practical city where everything was really affordable. I am told the housing prices are like Hong Kong / Vancouver so aside from this huge downer, the rest was very organized. Taipei was like a more civilized mainland. People are unbelievably nice there. Like really really nice. They smile and bow a lot, probably from a legacy of the Japanese colonial times.\n\nThe small eats here were so great. We spent a lot of time just eating.\n\nWe didn’t do much by way of tourism – we didn’t feel like there were major sites to see though the Palace Museum is a must. All of the treasures that left China with the KMT and Chiang Kai-Shek. The strange thing was that every museum was called the National Museum. The actual National Museum – THE MUSEUM is really the Palace Museum. Don’t get confused and go to like two other not that great National Museums like we did!\n\nTaipei felt very much like a less nice Singapore. Sorry to my Taiwanese friends! It’s just older. The buildings are older and kind of look like they’re from the 60s. What Taipei lacks in flashiness it does definitely make up with a sense of easy living. Again, the people are SO OVERLY NICE.\n\nYou can feel the Japanese influence. The thermal hot springs at Beitou were developed by the Japanese. We visited the area but didn’t partake in the pools. Lots of Japanese food available. I am told the Taiwanese are the only Asians who don’t hate the Japanese. This is because Japan actually tried to develop Formosa into a kind of Japanese paradise to showcase how benevolent it’s rule can be. Despite enforcing the teaching and mandatory speaking of Japanese at school, older Taiwanese people will still talk about the Japanese in a positive light.\n\nLongshan Temple is well worth a visit. It is over the top ornate yet its visitors are just ordinary Taiwanese going about their day and taking a moment to pray to Buddha.\n\nOne of the funnest things we ended up doing in Taipei was to go shrimping. This was literally an open all night pool with live shrimps where you literally fish for shrimp. I didn’t catch any and Ethan caught two. Luckily some super nice locals took pity on us and gave us some of their extra shrimps so we had more than two to grill at the end of two hours. Yea.. shrimping isn’t our forte. Boy were the fresh grilled shrimp delicious though! Thanks to the random strangers who took pity so that we could have more than one shrimp a person to eat! Two hours flew by. You drink beer and eat sunflower seeds while trying to catch them. So great. Thanks for the pro-tip Daniel!\n\nA must visit restaurant in Taipei is Hua Zhi Xun. The most delicious and inventive Japanese tapas ever!	2016-01-06 00:00:00+00	2026-05-29 02:11:18.948796+00
992e45bf-84d0-470f-a91e-e701ebba4e2e	es2015-sub-italy	seed:es2015-sub-italy	Italy – Wela’s Memory Dump	\N	**Venice**\n\nAs soon as we left the comforts of Anglo/Saxon Germany / Austria, we were thrust solidly back into the second world when we arrived in Venice.\n\nItaly is much dirtier than it’s northern neighbours. Not surprised. Ethan encountered a train strike on his way into Venice on the first day. Welcome to Italy! The driver seems to have just walked off the job. There were still other trains to take but there you have it. On Strike!\n\nThe touristy parts of Venice is insufferable. But like the redlight district in Amsterdam (where everyone is wall to wall), if you venture even a couple of steps away, it is a different world (Chinatown in the case of Amsterdam which is just one street over from the redlight district) and away from the grand canal in Venice.\n\nNorthern Italians weren’t all that friendly, especially people in Venice. I guess you can’t blame them when their entire country is constantly overrun with tourists. Literally black friday overrun. Everywhere.\n\nTwo very memorable meals in Venice – again no restaurant names but they are away from the tourist areas in Venice. Sorry, I suck. But definitely have the little crostini toasts with various spreads and cured meats on it!\n\nIt’s definitely a great place to visit as tourist – its Venice! but really you should plan to spend a lot of money to stay somewhere nice and also to go to a masquerade ball. The buildings are gorgeous and we saw a swanky ball going on where guests arrived by boat. Wouldn’t that be fabulous?!\n\nTake the public transit boats and go around the islands for cheap! This was definitely a highlight. People literally take these boats as commuter boats. There are some seats for tourists at the front if you want to take photos.\n\nVenice by night is SO GORGEOUS. Be warned, this Italy post will feature a lot of SO GORGEOUS statements.\n\n**Bologna**\n\nWe didn’t make the most of Bologna. We came here to eat and ended up cooking a lot. We didn’t find our eating groove until the last night when we finally found this amazing street (near Via Clavature) with stunning charcuterie plates and wines and seafood and pastas. For a filling and cheap lunch / dinner eat at Osteria dell’Orsa.\n\nThe city itself is not particularly interesting aside from the fact that its town center is covered with porticos (covered arcarde) so you never have to be in the sun (yes!)\n\nThere’s a leaning tower there as well. I believe the Italians are just not that great at building straight towers?\n\nThe San Luca church in Bologna is gorgeous. It is on a hill overlooking the city and you can get to it by walking the entire way under 666 arches. I loved the hike up and the views and the church itself was so unique and beautiful on the inside. We have seen a lot of churches in Europe but this one really stood out in my mind. The colour was also really great for a church – not the somber gothic gray but a delightful orange!\n\nBologna’s university has some interesting lecture rooms. The Anatomical Theater where medicine / dissection was first taught and the reading room were interesting to visit.\n\nBolognese sauce. Enough said\n\nTortellini, Tagliatelle, Lasagne, Modena vinegar, pancetta, mortadella, piadinas. SO yummy.\n\n**Florence / Cinq Terre / Pisa**\n\nFlorence is very much like Rome a complete tourist town. It is for good reason though because Florence just has so much heft in western culture. Leonard da Vinci. Michelangelo. GAH!!!\n\nThe David at the Galleria Academia was incredible. You have to see it in person. Its just magnificent. How did he make it from a piece of stone?!!\n\nThe Duomo is so grand and SO FULL OF TOURISTS.\n\nEvery inch of Florence was crawling. The Ponte Vecchio was wall to wall. Plaza Michelangelo has been overtaken by stalls selling tourist kitsch. Still, you can’t not visit Florence because it’s really just that pretty.\n\nI liked the Italian train stations. They were open. The Florence one was open as well. Something nice about them.\n\nUnfortunately we were too tired to drag ourselves to the Uffizi (I even bought tickets) because the Cinq Terre hike killed me. Also we got rained out on the day we were supposed to scoot around Tuscany. HUGE DISAPPOINTMENT.\n\nEat papperdelle in Florence. YUMMY! with wild boar ragu!\n\nTuscany is GORGEOUS. Surprise Surprise. Just beautiful landscapes and green.\n\nFlorence’s central market has food galore!! You can just spend all day here eating.\n\nCinq Terre – also OVERRUN. But the hike is magnificent. We stayed in Corniglia – do this to avoid the tourists. We hiked the first two towns, then the next two the next day. We saw met this German couple on the steppes of Cinq Terre (where they grow wine – and have these crazy wine collecting rail cars) who had a dog called the Elo. We wanted one! He was like a cuter chow chow. So fluffy and friendly!!\n\nCinq Terre – while it is an adult Disneyland – was again gorgeous. I think that is mostly what I have to say about Italy. Overrun but gorgeous. Anyhow, the hike is brutal! You definitely cannot handle it if you’re not ready for some hard core mountain climbing. Seriously. I was down for the count for like a whole day afterwards in Florence.\n\nEat pesto in Cinq Terre.\n\nThe square of miracles was so strange in Pisa. Everything about the square – the buildings, the leaning tower, was just eerie and weird. The leaning tower is worth going up. It feels incredibly strange to be up there. The entire square is just bizarre. I have nothing more to say aside from the fact that while touristy, I would say its worth visiting.\n\n**Rome**\n\nThe term living museum doesn’t define the city of Rome. Every inch of it is covered with something terribly important historically or the starting point of Western civilization. Everyone must come to Rome, it is Rome for heaven sakes! The Vatican, the Coliseum, the Forum, the fountains, the statues the blah blah blah blah. I can just go on and on about it. We spent like 10 days here and it was not enough. We only scratched the surface. Whereas in other cities the small fountains would be a center piece, in Rome it is just the side art to something even grander and larger.\n\nI went out to Tivoli by myself on a day trip to see Hadrian’s Villa and The Villa d’Este. OMFG. Este was mind blowing. The water gardens were out of this world. My favourite garden hands down. Unbelievable!\n\nRoman pizza is the MOST DELICIOUS pizza in the world. Forget the pizza in Naples. Roman square pizza is where it’s at people! the crust is so crispy. We ate so much pizza. Also cacio e pepe spaghetti and pizzas. The cheese is divine.\n\n**Naples / Capri**\n\nCapri was again very beautiful and obviously for rich people. Do the chair lift up to the top of the mountain in Anacapri for views of the Bay of Naples and the Amalfi Coast. Cold but worth it! It is a great place to enjoy the wonderfully manicured environs and food. The Caprese salad is from here. Fresh mozzarella!\n\nWe didn’t do the blue grotto but we didn’t think we were missing too much.\n\nWe had heard that Naples was gross and seedy but we actually really enjoyed Naples! The food was fantastic and cheap and it felt really down to earth. It’s definitely not that pretty in comparison to other Italian cities but I think Naples felt really comfortable because a large majority of Italian immigrants are from the south of Italy so these were the loud, vocal, bodacious Italians we are used to who populate NYC’s little Italy. The food also felt much more down to earth and not like the refined dishes from northern Italy. It was all big portions and lots of carbs. Certainly would get uber fat eating in the south of Italy. Naples had some small streets and neighbourhoods that were so very narrow and full of life with all sorts of people going about their day.\n\nNext trip will have to involve scooting around Tuscany, perhaps visiting Portofino and then going to Rome and heading south to see the rest of southern Italy including the Vesuvius, Amalfi and Sicily!	2016-01-06 00:00:00+00	2026-05-29 02:11:18.948796+00
e2f817eb-36fd-482a-bb91-a517e2a805fb	es2015-sub-austria	seed:es2015-sub-austria	Austria – Wela’s Memory Dump	\N	Salzburg was very cute. The city itself is tiny but it hits above its weight in name due to it’s prized son the world over knows: Wolfgang Amadeus Mozart!\n\nWe did a very kitchy but seriously fun Sound of Music tour. The guide was SUPER uppidy for someone who has to take people every day on the same circuit while doing Sound of Music sing-a-longs on the bus. It has been a childhood dream of mine to see where the movie was shot and boy was it amazing! Austria’s mountains are gorgeous. There’s a lot of adventure sports to do in this area but we only had 3 days, not enough to do anything.\n\nThe tour guide was also half-American. Maybe that contributed to the uppidy-ness?\n\nThe real Maria Von Trapp was not happy with the Hollywood movie. Surprise Surprise.\n\nSalzburg’s Augustiner beer hall was also great! It was in a strange location – like an old monastery – and don’t try to just buy saukerkraut, they want like 12 Euros for it! The meat plates though, those were cheap.\n\nWould be wonderful to come to the Salzburg music festival. We also didnt get a chance to go see the puppet show or attend a concert which I think would be worthwhile if you go to Salzburg!	2016-01-06 00:00:00+00	2026-05-29 02:11:18.948796+00
73fc9042-c1f2-4779-92c4-0537832dbc1e	es2015-sub-germany-west	seed:es2015-sub-germany-west	Germany (West) – Wela’s Memory Dump	\N	The Heidelberg Schloss is incredible. It is also a must visit! The grounds and castle itself was really beautiful and the funicular ride up was great. Aside from that Heidelberg was a quaint and sleepy university town. We ate a lot of schnitzel and brats and other typical German food. We also ended up staying in at our hotel which served good hearty German dishes because we were trying to catch up on work. The hotel I booked was in an area called the Pfaffengrund. The term “Pfaffengrund” is now a stand-in for “staying in bed” (or in our case staying in at the hotel / Airbnb / “home” we are currently occupying).\n\nGermans are a very no fuss kind of peoples. They always mean business and seem to always be serious, no unnecessary niceties unless there’s beer.\n\nWe rented an Audi to drive down from Heidelberg to Fussen where the Neuschwanstein and the Hohenschwangau castles were. The Autobahn down to Bavaria was INCREDIBLE. I just couldn’t figure how how they kept the highways SO smooth. Ethan drove up to 180 KM / Hr at one point. No bumps. I was did my best not to say anything but I was scared. But damn that German engineering is just astonishing. Also the entire drive down every couple of minutes there was a sign for a castle. Next time I want to come back and do the Romantic Road! We didn’t have time this time. I want to visit the gazillions of castles littered across Bavaria!\n\nWhen we finally got to Neuschwanstein, it totally blew away any and all expectations. The lake in front of Hohenschwangau was SO clear – we took out a row boat for a crisp row around the lake. The Hohenschwangau castle was very cute. It was the summer home of King Ludwig II, the “fairytale” / “mad” king as a kid as it belonged to his father King Maximilian. On display was a crust of bread that is over 100 years old! Also lots of scepters and swords etc. King Ludwig was considered the crazy king but my reading is that mostly he was just gay and people didn’t quite know what to make of it. His patronage of Richard Wagner along with other German artists really has created some of the world’s most fantastical art – including the Neuschwanstein castle itself.\n\nMy biggest disappointment was that the viewpoint of Neuschwanstein that gave you the full shot was closed when we were there. I am still upset over that. But in any case the castle itself is unparalleled. I know I’ve said that about a lot of things but seriously this castle is the castle to end all castles. I mean Disney copied this castle! It is unfinished but even in it’s unfinished state it is literally the fairytale castle of all your childhood dreams.\n\nThe area of Bavaria that Neuschwanstein is in is SO GORGEOUS. It’s indescribable the views from the two castles. I cannot rave enough about the natural beauty of Bavaria! We will be back Bavaria!!!\n\nWagner’s Bridal Chorus – the one everyone walks down the aisle to – comes from the opera Lohengrin which inspired the Mad King to build the fantastical Neuschwanstein.\n\nLots of Swan imagery around the castle – a symbol of the Bavarian royal family.\n\nWe missed Oktoberfest but Munich was still incredible. Ethan did a Hitler’s third reich tour which I opted out of. It made me too sad and I couldn’t stomach it to do it. Munich itself is a very clean livable friendly and open city. I was blown away by how trusting they were of everyone. Over a million people and the public transit system was entire honour based. No guards, no swipes, just buy your own ticket and take your own bus/train/tram etc.\n\nMunich had some really pretty old German buildings but mostly it is just a great lifestyle place. Everything worked, there was great food and had a very friendly atmosphere.\n\nThe food at the Viktualienmarkt is SO YUMMY. Soups, brats, grilled, roasted meats – eat your heart out baby! And all open air. Fresh fruits, cheese, jams, and on and on and on. Even amazing seafood!\n\nHighlight in Munich was of course the beer-halls. Hofbrauhaus was so lively and SO German with big apple strudels (not that yummy there, eat it somewhere else) and of course HUGE beers. Ethan had a blast, there was a four piece band and we hung out with some Germans who were definitely not into having Syrian refugees come.\n\nDefinitely a totally different perspective from Ethan’s well traveled young Third Reich tour guide who shows the burdens of younger generation of Germans who still feel guilty over the Holocaust and feel the need to repent and accept refugees.\n\nWhen I went to Germany in 2006 for the world cup to visit my good friend Sam (hi Sam!) he said it still made his mother uncomfortable to see large German pride displays – they’re actually scared of their own flag because of the baggage that comes with it. Side political note – this is NOT how the Japanese feel over their massacre of the Chinese, Koreans and other South East Asian countries during the war. Just saying. Some of us are still awaiting a proper apologies. Ok – sorry about that deeply ingrained political tangent. Anyways.. the burden they carry is truly heavy and you can feel it when you visit Munich where Hitler got his start – actually at the Hofbrauhaus.\n\nWe also went to the Augustiner beer hall. That place was also incredibly old but we went really late and didnt get to eat any food but I definitely had already eaten a ton of schnitzel and pork knuckle etc etc to last me a few months at that point.\n\nThe same open cafeteria format can be found at the eatery in the English Garden park! The Chinese pagoda there is not Chinese at all. It is a German’s idea of what a Chinese pagoda is, but it is obviously not Chinese. Haha.\n\nThe surfing in English Garden was really cool to watch.\n\nNext time, Oktoberfest!	2016-01-06 00:00:00+00	2026-05-29 02:11:18.948796+00
f9c4bab6-e37c-4e6e-9696-401090fdc720	es2015-sub-luxembourg	seed:es2015-sub-luxembourg	Luxembourg – Wela’s Memory Dump	\N	Luxurious is a good way to call Luxembourg City. Even the clouds were round and luxurious. Simple cafes serve 5 star meals.\n\nWe had a wonderful time walking around and eating snacks. The city itself is compact with a beautiful valley which had a nice park. There were some really nice old European buildings. Everyone seemed rich.\n\nThe city has some beautiful walls / fortifications which you can go into on a walking tour. We explored them on our own.\n\nWe were lucky enough to catch the Luxembourg City annual fair called Schueberfouer. It has been running for 675 years! It had everything you would want at a fair – carnival games, vomit inducing spinny rides, hearty German sausages, apple pies, cotton candy, popcorn etc. etc. The city ran free buses to and from the fair (yes free!). Ethan went on a huge spinny ride after eating a bratwurst. I told him it was a bad idea but he did it anyway. When he got off he was almost going to puke but didn’t. Carnival rides and junk food is not a good combination.	2016-01-06 00:00:00+00	2026-05-29 02:11:18.948796+00
e50fa1b4-eb8d-49eb-9ebc-244708f02c3b	es2015-sub-uruguay	seed:es2015-sub-uruguay	Uruguay – Wela’s Memory Dump	\N	We did the mandatory day trip to Sacramento de Colonia from Buenos Aires. I would kind of consider it a flop.\n\nDad wanted to go so we had to make the journey. Probably don’t need to come back to Uruguay. We read a lot about how it is the most developed South American country and is very small and liberal etc etc but Sacramento was a disappointment.\n\nThis is likely due to the fact that we have been to way cuter colonial towns. I mean the town was cute but it wasn’t THAT cute. There are some nice boutique hotels and some fancy restaurants but aside from that nothing stood out.\n\nThe cost was unbelievably high to do this trip. The ferry over was ludicrously priced. There’s a big discount for booking ahead but sometimes you cannot make that determination of whether you will go. I had told dad that friends told us it wasn’t worth going to for such an expensive price tag (he ended up paying almost CAD$600 for the three of us to do the return trip) but he wanted to go. Perhaps his thinking was that he will never go back to Uruguay again. I guess I can understand that.\n\nIn town the restaurants were ludicrously priced and the food was NOT good in comparison to the fantastic and cheap food in BA.\n\nIt was hot and the water was still black. Not much more to say, didn’t leave any sort of lasting or good impression.	2016-02-17 00:00:00+00	2026-05-29 02:11:18.948796+00
1a3bd278-1532-4106-9e89-157278d450c7	es2015-sub-argentina	seed:es2015-sub-argentina	Argentina – Wela’s Memory Dump	\N	Argentina is also quite orderly but not as orderly as Chile. It is better than Brazil in terms of the overall development for the population. In Chile we saw the same problems in North America where while most people seem to have a higher standard of living but things were very expensive which also inevitably leaves a segment of the population in poverty. In Argentina, things are very affordable and the standard is quite high and the wealth gap between the rich and poor is not as obvious.\n\nArgentina is the love child of a Spanish and an Italian person. I am was blown away by how very Italian Argentina is; everything from the availability of calamari to the presence of the bidet in hotels, Argentina is definitely equal parts Italian and Spanish.\n\nThis is perhaps also why Argentina has defaulted several times on it’s sovereign debt. Unlike it’s neighbor – the very German influenced Chile with it’s industriousness – Argentinians definitely seem rather to pursue enjoying life than working. The schedule here is Spanish with siesta hours being taken seriously. Dinner starts at 9PM and mothers are out with their babies until the wee hours of the evening.\n\nThe Argentine Parilla is a huge ass slab of assorted meats and offal and sausages that get served to you on a flat-iron sizzling plate with hot coals underneath. While good to try once or twice, it is very hit and miss whether you get a good combination and sometimes you wind up with only one meat that is good while the rest is just ok.\n\n**Mendoza**\n\nI don’t have much to say because our time here got cut short by three days. We stayed outside of Mendoza in Lujan de Cuyo, a smaller town closer to the vineyards. The town was fine but not much to say. The area is pretty but also not as spectacular as I thought it would be. I think I just had too strong of a desire to bike around beautiful vineyards but that never happened because the roads were not really bike paths. Maybe I will have to try again in Napa Valley or the Okanagan or somewhere in France.\n\nWe did a 5 hour wine tasting lunch at Ruca Malen – one of the smaller wineries. It was interesting to see how wine is made and aged and the setting was really beautiful here. The meal itself was nice but not really THAT spectacular for the expensive price tag. I think living in NYC really spoils you when it comes to unrealistic expectations of food when you pay a lot of money. The lunch was very memorable because the three of us had a great time chatting and we learned some interesting stories from my dad but the food itself was not the best I’ve had. The atmosphere was wonderful though.\n\nIt was a miracle we actually got to Mendoza. According to everyone we talked to, the Chile to Argentina border over the Andes was actually closed every day of that week except for the day we traveled. There had been apparently a huge snow storm in the Andes and so they had closed the border. The only reason we traveled that day was because we couldn’t get tickets for any other day after we decided to stay another night in Santiago. We ended up staying three extra nights in Santiago and in a weird turn of events it just so happened that we wouldn’t have been able to leave sooner even if we wanted to. Chile was just not willing to let us go! The drive in the Andes was epic, but not the most epic, like Bolivia was. The switchbacks were beautiful but I failed to get a photo. The high altitude did burst our bus window though!\n\nOnce we crossed the border from Chile to Argentina, we were coming down from the Andes when the bus window in the row in front of my dad’s seat literally burst open. This of course proceeded to rain glass shards on everyone. The most hurt was the couple in the seat where the window was. Either the pressure or the glass made her ear bleed. Dad was thankfully ok but glass was everywhere. Ethan and I also had little glass shards rain on us but we weren’t really hurt. This was another event in the series of unfortunate events that happened to dad. His trip was feeling a little like a page out of Lemony Snicket’s books!\n\nMendoza had comfortable weather. Apparently this was lucky because normally Mendoza is hot as hell. 35 degrees in the summer! This is a reason why it’s great for grape going. Hot and dry so they can control the amount of water the grapes get. Apparently this year the weather was bad though because there had been a lot of rain which is bad for the grapes. In Mendoza city proper there are canals for them to control the amount of water from the Andes but the heavy rains are a problem for the grapes.\n\nMendoza has a huge park called San Martin which was full of people exercising and enjoying the relative cool-ness of the park in the early morning. I can see this park as being an oasis for the people to escape the hot weather. The park has a beautiful set of gates from the people who made the Buckingham Palace gates and it also has a beautiful four rivers water fountain that is pretty much a copy of the one in Rome. Everything that is European is just basically a copy of Rome.\n\nThe Italian influence in Argentina seems to be huge. The streets of Mendoza really reminded me of Italy. I was surprised by the huge Italian component. They even have huge public garbage bins on the street like in Florence.\n\n**Iguazu**\n\nA South American highlight and a must, we spent two days here so we can see both the Brazil side of the falls as well as the Argentina side. Both sides are must visit because each side gives different views. Argentina’s side is much more interactive. You get very close to the falls and the park is very extensive with several trails for hiking as well as a train that takes you right up to Devil’s Throat. The raccoon like coati animals are everywhere and will viciously come snatch your food so beware!\n\nWe did the boat ride on the Argentina side. Best $20 we spent. The speedboat drives you right up to the falls and you get soaking wet. You definitely need a whole day on the Argentina side if you want to take your time on the paths. We were a bit rushed because we didn’t get out of the hotel early enough. The bus from Puerto Iguazu drops you off at the entrance of the falls but then you have to ride a train to Devil’s throat so it all took a long time. Better to bring food next time as the only option inside the park on the trails are Subway sandwiches. The service is snail paced and the ingredients are not great. There is some other food available but it’s not the best.\n\nThe buses to and from both sides were a little difficult to figure out but we made it work. On the Argentina side the town is called Puerto Iguazu and you need to take a bus that takes you to the Iguazu national park. On the Brazil side there are several things to note. First, the local buses can take you from Puerto Iguazu across the border to the large Brazilian town of Foz do Iguacu. Don’t get confused because this is the town, not the actual national park. To get to the national park you actually have to transfer buses (unless you buy a bus ticket that goes directly from Puerto Iguazu to the Cataratas do Iguacu park entrance). Luckily the buses are flexible with taking Pesos or Reals.\n\nThis area feels VERY Brazilian. It is rain-forest and wild animals and hot and humid. The quintessential image of Brazil. The Argentine side felt like Brazil.\n\nTwo words: POR KILOS! That and Argentinian Parillas equals MEAT MEAT MEAT. This is the home of the world’s most carnivorous diet!\n\nThe feel of the parks on the Brazilian side and the Argentinian sides are a bit different. The Brazilian side seems more luxurious / well built but the Argentinian side is a lot bigger and more to do. Brazil’s panoramic views are incredible though.\n\nTurns out you don’t even need a Brazilian visa to go visit the falls if it’s a day trip. The bus takes you to the border, Argentina stamps you out and you’re merrily on your way. There was no stamp to enter Brazil. Same thing on the way back. Turns out that’s a pretty nice loop-hole. But, also it was very easy to get a Brazilian visa here. My dad got one the next day – WAY less of a hassle than getting one in New York.\n\nWe were also told that the water isn’t always brown. Apparently in the fall (August) the water is white. I would love to see the falls when the water is white!\n\n**Buenos Aires**\n\nDefinitely the most beautiful South American city architecturally. There are quite a few old Italian/Spanish colonial buildings are just gorgeous. The streets are very wide, with trees and the vibe is very relaxed and the summer is glorious. Hot, but beautiful sunshine.\n\nThe Italian influence is on full display here. The walking the San Telmo area was pretty much walking in Italy. The city is full of beautiful theaters, one of which is now a library – the El Alteneo. The most beautiful building I have seen in South America is BA’s Water Company Palace; a water pumping station of all things! It is decorated with Royal Doulton iridescent ceramic tiles!\n\nBA definitely lives up to the hype. On first glance it seems kind of a boring place to visit for the lack of obvious tourist sites but given that we gave ourselves two weeks here, it has allowed us to soak up the culture here and the feel is just wonderful. It is the best parts of Europe with a South American price tag.\n\nTwo words: THE STEAKS. Holy moly is this not over-blown. The meat here is fantastic and SO SO SO cheap. You can eat such amazing food for very little. They Portenos understand the meaning of la dolce vida. The shopping is great. The parks are large and airy. The Art is gorgeous and the food is glorious. What more could you want out of life?\n\nPortenos talk with their hands – that is their Italian side.\n\nPlaying polo was super interesting but tiring. You have a lot to do – control the horse, hold the whip, gallop the horse, hold the incredibly heavy mallet, swing it at the ball, etc etc. Overall a great experience though. I think I would’ve been much less miserable had it not been 35 degrees and in the sun.\n\nTANGO! Such a romantic, sexy, passionate dance. It all made sense after the Tango show, why this place is the love child of Spain and Italy. The heat and emotion is palpable. The dancing is so beautiful both technically and artistically. We saw the show at Tango Porteno. It seemed the only reasonably priced show, the others are quite expensive. After the show, I was convinced that this now overtook the best $25 bucks we’ve spent.\n\nThe residential streets are full of HUGE poops. I guess people don’t pick up after their dogs. It’s gross and really disconcerting and such a pity for an otherwise glorious city.\n\nThe Chinatown here is clean and awesome and kitchy and has AMAZING Chinese vegetables! Heaven!\n\nWhen it rains, it floods. Like end of days rain and flooding in the streets. An awesome sight to behold.\n\nThe water in the delta is black and gross. It is too bad because if it were not black it would be quite beautiful.\n\nThe Recoleta Cemetery is a weird tourist attraction but it is hauntingly beautiful and a must visit. The National Library is gross on the inside but really interesting on the outside. The floralis generica is gorgeous. We did the Museum of Fine Arts which was really nice with some wonderful Argentine painters as well as a Picasso and Stuck’s Bethsheba!\n\nThe KFC at the Palermo Alto mall served Coke products. Weird.\n\nThe shopping in Buenos Aires is fantastic. Too bad I am horrible at shopping. I can see the potential yet I have no idea what to buy. It is a pity because I can think of many friends who would relish in the shopping whereas I am just lost.\n\nBuenos Aires is HOT as hell. It’s been consistently 35 degrees. The strange thing is it’s a bit of a pressure valve. You will get two days of 35 and then one day of 38 which means you are sweating bullets just by being awake and then boom – HUGE rain storm to cool it all down. This cycle has happened three times during the two weeks we were here. After the rains the temperature is wonderful.\n\nThe glazed croissants here called media-lunas (half-moons) are SO yummy.\n\nThe steaks here don’t get cooked very evenly. Within the same steak you can get a range from well done to medium. I believe it’s the slow cooking method using wood fire only that makes it cook kind of unevenly. Delicious but strange. Also when you order a medium or a well done, you can’t be certain how it will come. The well dones are never as well done as you’d like and the medium is never as rare as you’d like.\n\nEthan and I had a difficult time in BA strangely because we both enjoyed it so much. Being that we were here for two weeks it was difficult because it was like being home in NYC but without two key elements: no friends and no job. While I love the cultural aspects of the city as well as the architecture and Art, he loves that the city is great for partying and going out. Except at home, I would have girlfriends to share culture with and he would have guy friends to party with. Also since we are both not working during the day, there’s a lot of time to spare but neither of us really want to go do what the other person wants. His involves a lot of drinking and being in the heat, mine involves a lot of walking around and looking at things. Fighting ensues. As a result of his feeling like he is trapped here and that everything is too planned, he decided to book us to go to Tonga next week from New Zealand. Yea. That happened. I am happy that he has at least finally done something about his own travel satisfaction as opposed to just whining about it and not doing anything!	2016-02-15 00:00:00+00	2026-05-29 02:11:18.948796+00
57b7a11a-bb81-48b8-9bf9-6b67379ba1ea	es2015-sub-travel-safety	seed:es2015-sub-travel-safety	Some Thoughts on Travel Safety	\N	Thus far, we have been on the road for 6 months and Ethan and I have been pretty lucky that we haven’t had anything major happen. Knock on wood we can stay safe for the second half of our journey. Unfortunately for dad, he was targeted and robbed right under a security camera. I will relay what happened and some thoughts on the matter.\n\nAfter Ethan and dad picked up their bags from storage, they were making their way back to the Alameda bus station (Santiago, Chile) so that we could catch our overnight bus to Mendoza. It was at night time and there were a lot of people in the area. Ethan said that a woman had come up to him to say that there was bird poop on him. He looked and there was black stuff and she handed him a paper and water to help him wipe it off. They then did the same thing to dad. Dad said he felt something was off because they were really insistent, the woman said there was bird poop on his back and coaxed him into putting his bag down. It took seconds from when the bag left his body when he put it down to the bag disappearing. A witness said a man had made off with the bag. The crime was done within seconds and everything was gone. Luckily his passport and wallet were on him so those were safe but his computer, notebooks, some clothes and his sense of security was completely shattered.\n\nIt seems to me from this incident several lessons can be learned which Ethan and I practice but forget that other travelers do not.\n\nHedge your bets – split up your valuables.\n\nBlack is not a good coloured bag. The criminals dropped another black bag on the ground as a decoy because dad’s bag was black.\n\nThese people are professionals. Unfortunately dad stood out quite a bit as obviously easy pickings – he looked like a person who doesn’t travel rough. His backpack in hindsight just looks like it’s packed full of valuables.\n\nYour bag should never under zero circumstances leave your body.\n\nSadly I was not with them – I had heard of this scam before and maybe could have prevented it but sometimes these things happen so fast and is unavoidable.\n\nOther tips we have learned – don’t put your bag overhead on long bus rides – things will get easily snatched; watch the driver close the under-hold so people cannot steal your bag from under the bus while you’ve gone up to take a seat; always have a strap of the bag anchored to your body if you are sitting somewhere or sitting on a long bus ride.\n\nI have had a couple of friends have travel incidents: friend’s iphone got robbed in Barcelona; friend’s mom’s necklace snatched by a man on a bike in Vietnam; friend was even pepper sprayed in Millwoods while the robber tried to take her laptop/bag. Shit happens. Life happens. We can only do so much to try to prevent it but sometimes these things are going to happen regardless.\n\nYou may not do this but your parents might – they are used to traveling in a time when bank access was not so readily available. Tell them NOT to bring tons of cash in their bags – they should just factor in the ATM withdrawal fees into their travel budget. Walking around with tons of cash is just not safe.\n\nIf worse case scenario you are in a stick up – let go of your things! Your physical safety is the most important. Stuff is stuff and losing stuff sucks but you don’t want to trade your physical safety for stuff.\n\nAlways be vigilant, especially at night and in crowded places. It doesn’t matter if you’re in Stockholm or Nairobi, you can be targeted anywhere.\n\nGoing out into the world involves risks. This can happen to anyone and really shakes up your view of humanity. It is just so bad that the few have to ruin it for the rest of us. But generally people everywhere just want to do good and we have witnessed this for 6 months and I know will continue to witness it for another six. All we can do is try our best to be the best person we personally can be and work towards a better world.	2016-01-28 00:00:00+00	2026-05-29 02:11:18.948796+00
bb044e41-6948-46af-abf5-048b354bd4a2	es2015-sub-chile	seed:es2015-sub-chile	Chile – Wela’s Memory Dump	\N	The North of Chile is one gigantic desert. We took a 24 hour bus ride down from San Pedro de Atacama and it was just desert the entire way.\n\nNorthern Chileans were not very nice. Everyone tried to scam us. Taxi drivers would tell us one price and ask for another upon arrival. The hotel staff tried to say that the price of three nights was really only one night. Left us with a really bad taste in our mouths but maybe we just ran out of travel karma for a couple of days.\n\nChileans speak really fast Spanish and are hard to understand. Their accent is also bizarre. They also LOVE to correct your Spanish. Everyone corrects your Spanish. This is actually pretty good for us because we are learning but we can see why the Mexican couple on our Uyuni tour spoke badly of Chile. When you’re from Mexico – and when you are a HUGE country and when your Spanish is considered Latin American standard, it must confound you to no end that some Chilean is telling you that you are speaking your own language incorrectly!\n\nChile is pretty much Europe. Thus far you cannot even really tell you’re in Latin America. The people look white. The food is white. It’s just Europe.\n\nWhile Chile is pretty much Europe, it still has a ton of stray dogs – like all developing countries – and unlike in Europe. Though Europe had some.. not nearly as many.\n\nAccording to our Puerto Varas host Malva, Chileans are kind of like Canadians – a bit cold at first but then life long friends. They like to be independent and really don’t want hand outs. This is why Chileans seem not as nice at first. They also look down on the indigenous and want to be like Europe and detest their neighbours the Argentinians!\n\nSouthern Chile is pretty much Canada weather.\n\nChileans are fairly proud and their flag is seen everywhere.\n\nChile is very isolated geographically with the south pole on the bottom, a huge desert at the top, ocean on one side and mountains on the other. Hence their independence, their pull themselves up by the bootstraps and their need for self sufficiency. Strangely they are actually more open to the outside world than Argentinians (according to Chileans).\n\nUnlike the other South American countries we have been to, the Chilean police – the Carabineros – are very obvious and strong. Legacy of Pinochets regime, these are actually military police. Further to this, the presence of the Chilean government can be felt – this is the same as in Canada.\n\nUnfortunately Santiago has largely been ruined by my dad’s backpack getting robbed.\n\nChile is the least diverse country we have been to yet in South America – probably due to isolation. Chile has also been interesting because it is so uninteresting and downright bland – in that it does not exhibit really any signs of South America. It is an orderly society – so it would seem – south of the Atacama desert.\n\nChileans are the least “hispanic” of all the South American countries. It is likely due to Pinchoet’s regime where people are used to following the rules. They seem to take things more seriously and everything you purchase they give you a receipt. Even if you pay $0.20 to go to a public bathroom they hand you a receipt. It is completely the opposite of what you would expect of South America which people generally think of as a bit disorganized but very warm and kind of a fluid society.\n\nExamples of the orderliness of Chileans abound: if you bought a bus ticket for a certain time, they would rather let the earlier bus leave with empty seats instead of let you get on the earlier bus. If you want to get security camera footage from the police, you have to go through a long and orderly court process.\n\nHere you feel like it is quite like North America – the kind of somewhat rigid and unnecessary bureaucracy that comes with an orderly society. Ironic that it is here of all places that we got robbed. Perhaps it is because there was a sense of false security in the orderliness.\n\n**Iquique**\n\nFirst thing you notice upon arriving from Bolivia is that the roads are smooth. Wow! the miracle of first world roads!\n\nNot much to see or do here. We went paragliding – probably the only thing that’s fun here. It was a fantastic experience here. The combination of factors makes it a great place to paraglide. Take off was easy and the flight was long. We met a lost 60 year old Dutch guy who worked for Puero Velo the paragliding company. He was really fun to talk to and in love with a Chilean woman. I guess we all eventually find our natural homes.\n\nThe other fun thing to visit here was the recreation of the Esmeralda Chilean Navy ship from the 1855 war of the Pacific. You got to see all the cabins of the shipmates and the kitchen and living quarters. The guide talked super fast in Spanish so we missed a lot of stuff but the boat itself is very pretty and fun to go onto.\n\nBolivians are pretty bitter about having lost their access to the Pacific coast to Chile in the War of the Pacific (Saltpetre War). Chile seems to have done pretty well since they got Iquique from Peru and cut Bolivia off from the Pacific coast. Apparently Bolivia has an agreement with Argentina and has access to their water way.\n\nWeather was pretty balmy on the coast which was nice.\n\n**San Pedro de Atacama**\n\nAnother purely tourist town. Really great food at a restaurant called Adobe as well as La Casona. Fantastic place to star gaze. I think having just come from the Uyuni desert we were kind of tired of being in the desert so we really didn’t get up to much.\n\nThe town of San Pedro itself with its adobe buildings is incredibly cute. Really great to wander around and look into the stores. It is an expensive tourist town but would have been a delight to arrive to after Uyuni. It is just much more European and prettier in every way than Uyuni.\n\nOur star gazing tour was great. We got to see and learn a lot of constellations through the magical telescope. There was sausages and hot chocolate – so first world! There were things that are not visible to us in the southern hemisphere and because the star culture comes from Greece everything is viewed backwards in the south. The moon was definitely the most epic as well as Sirius which looked like a diamond – we took a photo of the moon through the telescope and you can see it’s craters!\n\nDon’t know why but there were really shady characters lurking around at night. Our host in Puerto Varas says it’s because there’s a lot of drinking and people are just drunk.\n\n**Puerto Varas**\n\nWelcome to Germany! the lake district is pretty much a mix of Europe (mostly German) architecture and culture – and Canada like scenery. LOVE IT.\n\nMust eat at the Donde El Gordito – seafood place – even Anthony Bourdain ate here, as well as La Marca an excellent steak restaurant.\n\nRented a car and drove around the area – breathtaking. Went up the Osorno Volcano and did super fun zip line. The volcano really looks like mount fuji, it towers over the huge ass lake Llanquihue. The driving around was so much fun. The Petrohue waterfalls were turquoise blue – incredible! (due to basalts from the volcanos).\n\nHere buffets are called Tenedor Libre (free fork!)\n\nOur hosts Alex and Malva are fantastic. No better place to stay than the container at Casa Fischer. They help you with everything and Spanish class with Malva is so much fun – she told us that in Chile you can tell a person’s socio economic status by the way they speak their Spanish (pitch and accent). Also that they are happy to adopt English words into their vocab unlike Argentinians who Hispancize English words or try to not use them.\n\nThere are these HUGE horseflies in the area apparently only in January. They are large and buzz and are super annoying when you are walking around the lakes and forests. They do bite although you can generally swat them away. They are attracted to dark colours – black and blue so it’s good to avoid wearing those colours.\n\nThe weather in the Lake district was very cool – very long days just like Edmonton summer and only warm during the daytime.\n\nWe unfortunately ran out of time to go to Fruitllar – which I really wanted to do.\n\nWe did get to go to Chiloe – SO fantastic. The island is gorgeous. We saw Penguins and seals, had Curanto (seafood and meat buried in the earth with hot rocks on top to cook it) saw the palafito stilt houses and went to a couple of the UNESCO world heritage wooden churches. They were extremely cute – one even had wooden pillars painted in marble patterns!\n\nEthan surprised me with a stay for my birthday at Ocio resort on the bank facing Castro (the main city in Chiloe). The hotel is GORGEOUS and the views from the Wind Suite (Viento) are unbelievable and the stay was so luxurious. Definitely a splash out but so great, they even gave us knitted booties made from the wool of the sheeps on the island.\n\nEthan really loved the very salt of the earth feel of the towns on Chiloe – the traditional fishing village feel of the towns were palpable. I imagine Nantucket to be very much like this.\n\n**Santiago / Valparaiso**\n\nSantiago is a fairly miscellaneous city. It is quite clean and organized for South America. La Moneda is worth seeing – a public art and cultural space under the Presidential palace. Bellavista is a nice neighbhourhood with great restaurants. Ethan really enjoyed the human rights museum as well as the Pre-Columbian Museum.\n\nValpo was fine – not sure what all the fuss is about. I think it’s cause we’ve been to more interesting places in South America. It’s ascensores are cool but not as awesome as La Paz’s teleferico. It’s colourful tin houses are cool but Batman Alley was cooler. I think it was just overrated because everyone kept telling us how awesome it is. Instead it was just fine. Interesting for Chile but not the most interesting overall. It also smelt of pee and poop. A great view can be had from the restaurant called Cuarto Viento at the last ascensore at the end of town.\n\nMy dad’s backpack got robbed from him in Santiago near the Alameda bus terminal. This has been a traumatic experience. I will discuss this in another post. Because of it we had to change our plans stay behind an extra 3 nights in Santiago very begrudgingly and causing all sorts of havoc.\n\nAside from that I don’t have much more to say about the kind of miscellaneous-ness of Santiago. The Bella Vista area is nice with some great restaurants. There are parts of it that are incredibly modern – pretty much looks like Toronto with lots of glass and steel buildings.\n\nOur Airbnb host was phenomenal. He helped us go to the police station and waited with us. Picked us up and dropped us off. I overall really enjoyed the kind of very frank and somewhat clinical attitudes of the people. I can see it coming from the German influence. Definitely Southern Chile was the best part. I don’t need to come back to Santiago.	2016-01-19 00:00:00+00	2026-05-29 02:11:18.948796+00
488f99e9-4ab7-4d14-996a-3594d1068408	es2015-sub-bolivia	seed:es2015-sub-bolivia	Bolivia – Wela’s Memory Dump	\N	Bolivia. What an incredible country. It is definitely the most indigenous country we have been to / will go to in South America. It’s entire country is overwhelmingly indigenous in ethnicity (something like 70%) and here you can definitely feel the difference.\n\nI was obsessed with the bowler hat wearing squat and rotund Bolivian women. Their hair was so black and so thick and lush and long and always in two long braids. The bowler hats!! just fascinating. And the same kind of ruffly half skirts and holy moly what were they carrying in those large packs strapped to their backs? I still cannot tell. They reminded me of the cupcake dolls from the 90s. Same kind of ruffly skirt.\n\nBolivians seemed to us a very industrious lot. Cold places seem to inspire industry. People were not lazing around on the beach – no sir – people were always working hard.\n\nBolivia is a harsh place and a difficult one to travel to because it is quite physically uncomfortable. It is very rewarding though if you do make it there.\n\nThe Altiplano which is the area of Bolivia we were in (The high plains) was just that. SO freaking high. The clouds were literally on the ground. The air was so thin that all our packaged toiletries with air inside expanded. No joke. I imagine Mongolia to be kind of like this part of Bolivia.\n\nLlamas!!!\n\nIt was never really that warm in Bolivia even though we were there during their summer. You definitely need to always carry with you and ultralight down jacket. The nights are always cold.\n\nBolivia’s roads are terrible. The most bumpy ass roads you will ever have to endure.\n\nEvo Morales – Bolivia’s populist President – is omnipresent. His face is in the graffiti; there are Si Evo signs everywhere. This may be left over from the 2014 Presidential election but people seem to really like his socialist reform policies. He dislikes fast food so much that McDonald’s left the country (though there are terrible tasting Burger Kings). He seems to be full of rhetoric and is credited with lifting people out of poverty. They call him Evito!\n\nI am sad we didn’t get to visit Tiwanaku, the main site of the Aymara natives of the area near Lake Titcaca and La Paz. I think it would have been great. That and the Valle de la Luna – though maybe we had enough weird rock formations to look at even within La Paz. Also the world’s highest golf course. Didn’t visit.\n\nApparently a new law went into effect whereby Evo Morales has not mandated a second indigenous language to be taught to all Bolivians. You had to get a certificate to say you could speak another language. The main one in Sucre was Quecha and because of the new law advertisements for Quecha classes was just as dominant as classes for Ingles.\n\nDue to the high altitude or just weirdness of Bolivia, my phone went haywire twice. Once completely and another time just kind of fizzy. I had it repaired in Sucre for like 6 bucks. Worked like new and literally was a reboot. It never occurs to you that these sorts of things can happen. I was told that the battery on cellphones will literally expand upon reaching Bolivia altitude. Whao! Also apparently water boils at a lower temperature in La Paz!\n\n**Sucre**\n\nWhen we landed in Santa Cruz – we had to wait for our flight to Sucre. Two things we noticed were: (1) Cinnabon (oh so yummy) and (2) Amish people! It was seriously weird to see Pennsylvania Dutch Country Amish people in Bolivia. We had a fantastic going to the civil war re-enactment and touring Amish country in Pennsylvania but seriously didn’t think we’d see them in Bolivia of all places.\n\nOur plane landing in Sucre was seriously harrowing. Thunder bolts and lightening, very very frightening! I literally thought to myself I am going to die in Bolivia but then we didnt die and landed. Phew. Can’t blame the pilot.. it was seriously horrific conditions.\n\nThe altitude is super high here so the first night I found it hard to breathe but adjusted quite quickly. I think the mate the coca made me a bit ill. Last time in Peru I drank it up and kept drinking. This time I found it just made me a bit ill so I didn’t keep drinking it.\n\nSucre has a tiny but cute colonial center. I doubt we will ever go back to Sucre but we had a relaxing stay. We took Spanish classes from Open Spanish on Potosi street with a really lively girl named Shirley. These classes were such a riot for us and we just had so much fun getting to know her and to know Bolivia. Very fond memories of Shirley and the school (even though it was pretty run down). The owner Gonzales was an awkward but nice fellow, super thin and tall. His dog Lucas was the best though – an English Sheepdog straight out of the Little Mermaid. It was very friendly (and on the last day took a huge pee in the yard) but oh so cute.\n\nSucre’s market was the one I had been looking for! Real fresh veggies! Allowed me to make wonderful Christmas brunch and dinner. We cooked pretty much exclusively here. Chocolates Para Ti is also a must. Fantastic chocolate covered fruit kebabs!\n\nThere’s an uber cheap fried chicken place on Calvo street just south of the main Plaza that was really yummy.\n\nSucre is known as the white city but it was more orange than white.\n\nThe place we stayed at La Selenita was great. The room was of average comfort but the caretaker there Juan was just so amazing attending to every need. The kitchen was functional for cooking so we just spent the better part of the week at home cooking and reading and eating and doing Spanish class. It was a quiet Christmas which I was happy for – Ethan was sad we weren’t in Brazil for this. La Selenita also had fresh jams daily and fresh fruit juice. It was so luxurious!\n\nBolivian cuisine is nothing to speak of. We tried it once and decided we would forego eating Bolivian food. Just a lot of chicken and spiciness. The soups are always good though – especially mountainous and cold countries – they always have soup.\n\n**Uyuni**\n\nThe bus ride from Sucre to Potosi was uneventful. Potosi looked sad and depressing – its claim to fame their horrific conditioned silver mine. The mountain apparently had a trickle of molten silver running down it which started the silver rush and is now just a desolate sad place. It’s literally the highest city in the world I believe. Life here seems harsh and just depressing.\n\nFrom Potosi to Uyuni the scenery got weirder and weirder – literally looked like we were looking out onto Mars. Desolate. Red. Rocky. Incredible.\n\nUyuni itself is a lot more robust than imagined. There’s far more streets and the distances longer than you would think. It’s in the middle of the desert but there’s lots of expats here to cater to a really growing tourism industry.\n\nHands down you have to stay at La Petite Porte. It is pretty booked up though. The other hotels here charge you exorbitant prices for much less comfort. Whilst the toilet being kind of open at Le Petite Porte is a bit uncomfortable, it’s nothing a couple can’t endure for a day or two. The breakfast here was really great as well.\n\nWe ate two dinners at the Minuteman Pizza restaurant inside the Tonito Hotel. This is a pizza shop that actually has spectacular pizza on account of where it is. The best were the nachos. By god! Everywhere in the world tries to sell you nachos – even in Brazil – but it’s all just wrong! the salsa is wrong, the beef is wrong, the chips – dont even get me started. But nachos are American and this guy is from Boston so praise the lord the nachos were a god send! We saw no reason in going anywhere else. We ate here the night we landed and ate here the night we came back from the Uyuni tour. YESSS.\n\nUyuni is definitely just a tourist town, not much else besides abandoned train parts as the town center piece. Strangely lots of Asians here. You cannot help but come here before and after the Salt Flats tour so might as well make the most of it. It was a lot better than we had thought it would be with a lot better infrastructure. It also looks like it’s only going to get better. The night we came back from our tour we had to stay at the Jardines hotel because La Petite Porte was booked (boo) and the hotel itself was bad. But the new restaurant attached to it was good and newly opened. The breakfast was yummy – the bacon was really yummy. The new manager there is a really cool guy named Tony who we got to talking to. He’s half Bolivian half French, trained in France and lived in New York – really international kind of guy. He had just gotten to Uyuni to help manage this restaurant. You can tell he takes pride in his food. He gave us recommendations for La Paz but I am pretty sure once his venture gets going the food will be great. With the breakfast you can already tell there will be some flair.\n\nAnother roadside open bbq meal. This time we believe it lead to Ethan losing his wedding band. His hands were greasy and so he thinks he wiped his ring into a garbage can in Uyuni. Our overnight bus to La Paz was leaving so he didn’t have much time to go look for the ring once we discovered it gone but he definitely did dig in those garbage cans around the little park near the Jardines hotel. Eww. Sigh.\n\n**Salar Uyuni and Eduardo Avaroa Reserve**\n\nIf there ever was an “EPIC” Journey it is this one. Three full days in a 4×4 driving on the moon and Mars. Words cannot describe the kind of life altering experience being on the Salar and in the Reserve is. You just have to do it.\n\nThe journey is incredibly hard. It is bumpy. It is SO DRY and it is SO FREAKING DUSTY. Just dust penetrating all your orifices. The food was not good. Our driver Edwin was always missing (as visto Edwin?) but who can blame him? We spent New Years Eve at a salt hotel. The Salar itself is just incredible – unbroken and so flat – just gorgeous. The random flamboyances of flamingos. The desert foxes. The weird rock formations. The salt piles. The seriously Dali-esque everything (not just the Dali Desert) – most of all Incahuasi the bizarro cactus prehistoric under-water – but now exposed Island. What an experience. Such a slog but so very worth it. It’s unbelievable to me that these guides just drive 16 hours a day. We got up at 4 am both mornings and it was just driving driving. Again, nothing to say aside from the fact that the journey was epic.\n\nWe found 3 inukshuks and we built another one on the salt falts!!\n\nThere was no water – the rain had come late. GRR global warming! This gives us an excuse to come back to see it when there’s water!\n\nWe stopped to have a wonderful lunch in a lush valley on our way back to Uyuni. The water was so clear. There were llamas close by. It was always such a delight when there was water in the desert. The thermal pool was also great – I only dipped my feet but Ethan went for a swim and said it was wonderful. Just naturally warm water bubbling forth from the ground.\n\nCannot recommend this enough. It’s brutal but really very worth it. Definitely not for the faint of constitution though!\n\nWe were on the tour with a lesbian Mexican couple (one was probably 22ish, the other 30) from Durango, and a couple who live in Santiago but the guy was from Bolivia and the woman was from Medellin – both grad students. We could never tell if the couple was having fun but they were very in love so we called them the Amantes.\n\n**La Paz / El Alto / Titicaca**\n\nWhat a fantastically situated city. Right in the bowl of the mountains. The MiTeleferico cable car rides is a must – Green line to see the rich, red line to see the poor. La Paz was just so interesting in every way.\n\nWe stayed in Sopacachi – the upper middle class neighbourhood. Ate twice at Chez Moustache – probably the most divine French restaurant in Latin America – no joke. Sopacahi had character. It’s not bland like the rich neighbourhood in the south we visited. It was La Paz but definitely not as uncomfortable.\n\nWalking in La Paz sucks because it’s so vertical and hilly and you’re out of breath due to the altitude.\n\nWe may be missing something but we weren’t quite sure why the Calle de Brujas (Witch’s Market) is such a big deal when it’s like two stalls who sell llama fetuses. We are scared we had a “National Museum” moment and didn’t go to the right place.\n\nCycling the death road was epic. I am shocked I did it and didn’t die – It was very very dangerous. Just two weeks earlier some Italian man jumped his bike and plunged to his death. I was just glad both Ethan and I survived unscathed. I spent the whole time breaking and it was so incredibly bumpy but I am very proud of myself for having done it. The ride was unbelievably beautiful and rewarding. If you have a little bit of guts you should definitely do it. It’s quite difficult though and there’s definitely no shame in chickening out. The downhill is relentless. Absolutely relentless.\n\nLake Titicaca was absolutely huge. Copacabana is pretty meh but we stayed at the bizarro Seashell Suite 8 of Hostal Las Olas. That was definitely the most interesting hotel stay thus far on our trip. The fire place there gave Ethan tons to do. The restaurant there is also quite yummy. The hotel had llamas as their form of grass cutting! I tried to go pet one but the male chased me out. A little kid told us pueden morder. Luckily they didn’t moder me!\n\nThe lake itself is beautiful. The drive around it on the bus back on the Bolivia side is beautiful. The ride there was horrible. Apparently the indigenous always block up El Alto to prevent traffic into La Paz as a form of protest. As such our bus company had to take us through Peru and back into Bolivia. That’s right – customs on both sides for us. We literally entered Peru for 20 minutes only to exit it on the same day. We have the stamps to prove it.\n\nIsla de Sol was great but we had 40 minutes on the Island. It was probably enough – we got to see the reed boats that apparently sailed all the way to Polynesia! That was really great. That and more bowler hat wearing Bolivian women. Woohoo!\n\nWe hung out with two Aussie girls from Melbourne who tell us there’s a huge Melbourne – Sydney rivalry. They seemed to really dislike Sydney. Too bad we’re not going to Melbourne this time around.\n\nOn the ride back our bus drove onto a barge and the barge ferried us across a little gap on Titicaca. Incredible this wooden barge!\n\nTiticaca is HUGE. It looks like the ocean. I was very happy to have gotten to see it. Ethan seemed uninterested but I was really enjoying the landscapes.\n\nLa Paz’s cemetery district is like a whole tiny city made up of interesting boxes that are graves that is just open to the world. How fascinating that you can visit your loved ones this way. It is similar in China at the fancy graves boxes we went to to visit Ethan’s aunt and grandparents – except here they’re out in the open. It was really very beautiful.\n\nAt the tiny Coca museum in La Paz, I learned that coca was in Coca-Cola for the longest time! Nowadays the leaves are only used for flavouring (.. sure..). The museum also showed the effects of crack cocaine and how the white man took this traditional Andean leaf and made it bad. Edwin our Uyuni tour driver constantly was chewing the leaves. The locals do it all time, kind of like drinking coffee.\n\nThe La Paz Sunday market is HUGE. Everything and anything under the sun is sold there. Used cars, electrical parts, food, wool pants, knock offs. Whatever you can dream up, they well it. We read they even sold used medical equipment though we ourselves didn’t see any. We ate various snacks including egg buddies (I think of them as very Hong Kong – those little waffle bits you can get in NYC’s Chinatown), fruits, drinks and fried anchovies. So delicious. We wandered around for a long time. Next time Ethan wants to buy a car at the market (we saw trucks being sold for 5000 Bolivianos so USD800) drive it down through Uyuni to Chile.\n\nThe cholitas wrestling was also strange. Lots of shouting and pomp and fun. A lot of female on female kicks and punches and jumping. Seriously lucho libre – like seriously the women fought the men and won. It was incredible.\n\nIn La Paz, it is the opposite. The rich live really low in the valley – this is where the weather is nicer – and the poor live in El Alto where it is cold. To the point where the entire plain where Titicaca is on is actually where El Alto is and La Paz sits below. Still it doesn’t take away the fact that the two cities are pretty much one and that it is the world’s highest metropolis.	2016-01-19 00:00:00+00	2026-05-29 02:11:18.948796+00
ea7d26f4-b933-4b9a-8752-eb2bc7b53c4f	es2015-sub-the-demon	seed:es2015-sub-the-demon	The Demon	\N	I still don’t know what I’m doing.\n\nA part of me thinks that by the time you’re into your 30s that somehow you’re supposed to have figured out what it is you’re doing with your life. Yet, another part of me realizes that the older I get, the more I see that people are still just making it up as they go; that an answer to life doesn’t just land on you and that everyone everywhere, no matter how old is still just making it up as they go.\n\nAccording to George Orwell:\n\n> Writing a book is a horrible, exhausting struggle, like a long bout of some painful illness. One would never undertake such a thing if one were not driven on by some demon whom one can neither resist nor understand. For all one knows that demon is simply the same instinct that makes a baby squall for attention. And yet it is also true that one can write nothing readable unless one constantly struggles to efface one’s own personality.\n\nI suppose when I was a lawyer, that demon inside of me was put in a box. It was shut away in some dark corner of my soul and I constantly floated above that bottom layer by occupying my time with daily drudgery. Putting it in a box and storing it in the bottom of my closet made me melancholy. Kind of like the feeling you get when a wonderful vacation is about to come to an end but you can’t bear to let yourself go back to your real life. I went about my days hiding from myself. If I just ignore the low level buzz coming from the deep, I could go on and pretend like everything is ok. However, over time, the demon slowly seeped out of its box. It wanted out, and it was not going to rest until it got out.\n\nSo then I let it out.\n\nI wrote a book. I wrote a big book. With lots of pictures. And I wrote it and drew it all by hand. Every day I had a fever. I woke and wrote and drew and went to bed and woke up again to write and draw.\n\nBut then the other part of me, the rational, honest good part of me put on the breaks. What are you doing? It asked. Put it back in its place! And so I did and I tried to run again. This time I did better work, I did work that felt somewhat meaningful. But still the demon was not satisfied.\n\nAnd so I took a trip. A very long trip. A trip that made me stare the demon in the face. And now every-day, I am the demon.\n\nSo now I must learn to live with the demon because it is a dark and stormy. It runs around and causes chaos and doesn’t let me have a moment’s rest. It calls me to feed it, to attend to it at every waking moment because it wants my blood, it wants my youth, it wants my sanity and it wants revenge. Every moment I am not thinking about it, or breathing it, or talking about it, or tending to it, it screams for my attention. Just like a baby. Screaming for attention.\n\nAnd now that I am living the demon, I find myself descending into the madness at an alarming rate. I don’t care for social interaction. I like to draw the blinds. I try to sleep a lot but cannot because my sleep is pierced with its screams.\n\nSomehow I must find a way to balance the two. The sanity and the insanity. I must contain the demon to certain parts of my day and function as a normal human being the other parts. I must learn how to harness its energy in a productive way. I must stare it in the face and tell it that it is not the boss. I must reach towards the light so that I don’t fall perpetually towards the dark.\n\nBeing a writer is a strange career choice. There are no rules. There are no boundaries. There are no set hours you have to show up, nor an outfit you have to put on. Every day you wake up and it is a blank page staring at you, and you alone must bear the burden of what happens that day. It is hard not to compare yourself to other writers you hear about. You wonder if you are being productive enough, you wonder if you are creating enough. It is a career where you make up the rules and where success or failure is marked by your accumulation of days and months and years of struggling in the dark.\n\nYou spend your hours feeding the demon and you hope that at the end of the day it is satisfied so that there are moments of peace from it and the fever it causes. You keep reaching and reaching through your entire life waiting for the day it leaves. But you know you can never get there, because the moment you do, you too will expire. So you carry it with you as part of who you are and you wake up each day, and you live with your fever, because that is all you can do.	2016-09-15 00:00:00+00	2026-05-29 02:11:18.948796+00
fbbd9a5c-10aa-4c3d-92d6-8e1bff479ebd	es2015-sub-uncertainty	seed:es2015-sub-uncertainty	A Lesson in Uncertainty	\N	It wasn’t until I was standing in my naked living room did it dawn on me that we were really going. After years of dreaming, talking, planning and saving, the day had finally come to leave it all behind. It had been a long time coming.\n\nThe idea to go traveling for a year came to me probably not too long after I returned from studying abroad in South East Asia. After meditating in ancient temples, burying my toes in white sand beaches and gorging myself at midnight hawker stalls, it’s not hard to see why returning to my formal banal existence hit me so hard. When I first had the idea, it was nothing more than longing. Sure, everyone talks about quitting their lives and leaving with just a backpack, but so few people actually go. Growing up I had always done what was expected of me. I obeyed my parents, worked hard at school and landed a steady job even before graduation. By every external measure, I should have been happy with the life I built; instead all I could feel was a desperation. The familiar feeling of being trapped crept back into my consciousness and I knew I needed a way out. I applied to law school.\n\nUnlike the improbability of being a world traveler, law school was always certain. As the child of Chinese immigrants, I was taught at a very young age that success could only come from education. While other parents fussed over high-school graduation, my parents found the production laughable. While other parents cried at their kids’ university graduation, my parents gave me a terse “good job.” To them none of these events registered as achievements because there was always even higher education. When it came to what career I should have the “choice” was simple: I was to become either a doctor or a lawyer. “And since you’re uncomfortable with the sight of blood” my dad remarked “you should become a lawyer!”\n\nEven as I applied to law school my feelings toward it were mixed. On the one hand, I knew that my Arts degree was not enough professionally and studying law was the most practical choice. On the other hand, as someone who never wanted to be a lawyer, spending three years slogging through law school seemed simply preposterous. In an attempt to ease my own misgivings, I told myself that after graduation I would immediately enter the Foreign Service. I reasoned that as long as I avoided the realities of lawyering, I could still rise to the top of this uncertainty stew and find a job abroad. Oddly enough, in the maelstrom of deciding whether to even go to law school, I was clear on one thing. If I was going to law school, it would be McGill.\n\nI suppose I could say that I was interested in McGill’s bi-lingual program. Or that it was one of Canada’s best law schools. Instead it was Montreal.\n\nIn the summer after Singapore I cleverly devised a way to extend my wanderings by going to Quebec for six weeks. Thanks to the bounty of a Canadian government bursary, a friend and I stuffed our faces with poutine and pork crackling as a guise for learning French culture.	2016-08-01 00:00:00+00	2026-05-29 02:11:18.948796+00
550941db-fad1-477b-882a-cb96d05b8679	es2015-sub-prologue	seed:es2015-sub-prologue	Ourearthsandwich Prologue	\N	I don’t quite remember when my love of travel started. Growing up in suburban Edmonton, “going somewhere” meant making the three hour drive to Calgary. Alberta is a big province and Edmonton is so far north that you couldn’t go anywhere without driving for hours and hours. If you drove for tenhours in Alberta you would still be in… Alberta.\n\nIt is strange that despite growing up in such a vast place, I felt like it was too small. Throughout my grade school years, no one knew where my hometown Shanghai was and no one cared to learn. My classmates were content with where they were and never thought about anything more. Edmonton felt small because the people felt small and I wanted something bigger. As far back as I can remember, I was always itching to leave. I dreamt of going to the faraway places because felt desperately trapped by mediocrity. In my youth I was just biding my time, waiting for the day to come when I was old enough to go see the world. When it came time to apply for university, I thought my chance had finally come. I decided on the journalism program at Carlton and eagerly told my parents that I was going east to Ottawa. “No” they said. “You’re not going to Ottawa.”\n\nI didn’t end up going to Ottawa. I was 17 and my mother said I was too young to move so far away. Instead of running away to the other side of the country, all I did was run away to the other side of town because when I was accepted to the U of A, I gave up on something bigger. Even though I wanted so much to be different from my classmates, I just wasn’t; I was going to the same university and living the same boring life as they were. Contrary to what I thought though, as soon as classes started I found that university was different. I met professors who seemed so worldly and talked to classmates who also wanted to see the world. I dove right into my political science classes and relished in my status as the over-eager first year.\n\nBy the time second year rolled around I was well into the swing of university life. The U of A was a whole other world and I was all too happy to live within its confines. I almost forgot about the outside world when I found out about the Sandy Mactaggart Award. $13,500.00 it said. Full ride for a year in Asia.\n\nIntimidated does not even begin to describe how I felt about applying for the award. As much as I wanted to go see the world the reality was that I had never gone anywhere. The longest time I had been away from home was a week at a high school writing camp and that was still in Alberta. I also felt like I was just not good enough. To me this award was meant for the superstars, the ones who were not only academic achievers but also well-rounded. I was just too ordinary in every way for such an extraordinary award. When I found out that my top-of-the-class friend was also applying I pretty much threw in the towel. He had received the highest GPA in the entire Faculty of Arts the year before which pretty much meant that he was a shoe-in. Since we both believed this award was his for the taking, I decided to have some fun with the application. With nothing to lose and a flair for some creative writing I added a bit of humour to the essays: “How would your host university benefit from your presence?” was the question and “I’d bring my fashion sense” was my answer. To my utter surprise (as well as the surprise of my shoe-in friend), I was awarded the scholarship. Congratulations, the letter said – you are going to Singapore for a year!\n\nThe first night in Singapore was hard. I was in a new country on the other side of the world. I had dreamed of this moment for so long but now that reality was here I felt utterly lost. I didn’t have my house, I didn’t have my bed and I certainly didn’t have any friends. Worst of all it was suffocatingly hot. When a tiny salamander crawled up my dorm wall I literally screamed out in fright. I was full of doubt when I called my parents and as much as I didn’t want to, I bawled on the phone. That evening I fell asleep completely exhausted wondering what I had done to myself.\n\nStrangely, the next morning I woke up with a feeling of peace. The fears from the night before evaporated as I stepped out of my dorm. I didn’t know anyone and no one knew me but somehow it felt great. From that moment on, something changed within me that to this day I still cannot explain. I no longer dreamed of traveling the world – I was actually doing it. The year I spent in Asia changed my life profoundly because it was the first time I traveled extensively. Since that year I had always wanted to travel again but this time do it full-time. Traveling full time was the culmination of waiting to fulfill a dream I had since going to Asia, and this is the story of that journey.	2016-07-07 00:00:00+00	2026-05-29 02:11:18.948796+00
aefa6cc1-ba7f-4280-a10d-6d74fc38a09a	es2015-sub-epilogue	seed:es2015-sub-epilogue	Ourearthsandwich Epilogue	\N	The sound of construction is everywhere. The noise of hammers, saws and steel beams being laid down come through the big windows of the apartment constantly reminding me of my restlessness. It is the day after 4th of July and the sky is full of rain clouds. Yesterday, while others were celebrating with BBQs and fireworks, I mostly moped about in my PJs wondering when the sun would come out. It did finally come out at around 6PM, but by then the day had already escaped me and I was in no mood to party. It has been two weeks since I’ve arrived in Seattle and my bad attitude hasn’t gotten any better. Every morning, I wake up to a perpetually gray sky and every morning I think to myself: what the hell am I doing here?\n\nSeattle is a beautiful city. On a clear day, gorgeous snow-capped mountains are visible from tall buildings downtown. Beside the numerous lakes around the city, her streets are brimming with trees and her coastlines full of sailboats. As far as a city to build a home in, it’s almost impossible to argue against her airy buildings, her clean streets and her laid-back attitude. Yet try as I might, I just don’t like it here. Maybe it just takes more time.\n\nWhen I first moved to New York, I also deeply despised it. I found it to be uncomfortable in so many ways and that wasn’t even counting the rats. It took me a very long time to get adjusted to life there; over three years to be exact. Strangely, when the time came to leave New York after four years, I was sad to go because I had finally gotten used to living there. It seems like for New York, three years is the magical amount of years where you go from a visitor to a resident. In the eight years that Ethan had been there, he saw three waves of people come and go and only those who made it past year three actually stayed in the city. If it weren’t for our trip, we would still be there now. Instead, here we are in Seattle. A year of running around the world later and we find ourselves amidst the tech construction boom in America’s Pacific Northwest. Amidst lumbersexuals, man-buns, thick rimmed glasses and plaid shirts.\n\nA year ago, I set out on a trip to try to find some answers and a year later I seem to only have more questions. Perhaps that’s just adulthood; an unending tide of questions for which there are no answers and so damnit, you just have to make up your own. When Seattleites wake up, they stare up at the gray sky and they say to themselves “another beautiful day in Seattle”. Tell yourself anything enough and you will eventually believe it.	2016-07-05 00:00:00+00	2026-05-29 02:11:18.948796+00
\.


--
-- Data for Name: trips; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.trips (id, title, description, start_date, end_date, created_at, updated_at) FROM stdin;
miscellaneous-adventures	Miscellaneous Adventures	A collection of adventures across Latin America, Europe, and North America.	2019-05-13	2024-02-20	2026-05-29 02:11:18.896682+00	2026-05-29 02:11:18.896682+00
earth-sandwich-2015	Earth Sandwich 2015	A round-the-world journey from Dublin to New York spanning July 2015 to August 2016.	2015-06-21	2016-09-15	2026-05-29 02:11:18.896682+00	2026-05-29 02:11:18.896682+00
earth-club-sandwich-2027	Earth Club Sandwich 2027	A round-the-world journey spanning March 2027 to May 2028, with stops across Asia, the Pacific, the Americas, the Gulf, Africa, and Central Asia.	2027-03-26	2028-05-12	2026-05-29 02:11:18.896682+00	2026-05-29 02:11:18.896682+00
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: instagram_posts instagram_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.instagram_posts
    ADD CONSTRAINT instagram_posts_pkey PRIMARY KEY (id);


--
-- Name: regions regions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.regions
    ADD CONSTRAINT regions_pkey PRIMARY KEY (iata_code);


--
-- Name: stops stops_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stops
    ADD CONSTRAINT stops_pkey PRIMARY KEY (id);


--
-- Name: substack_posts substack_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.substack_posts
    ADD CONSTRAINT substack_posts_pkey PRIMARY KEY (id);


--
-- Name: trips trips_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trips
    ADD CONSTRAINT trips_pkey PRIMARY KEY (id);


--
-- Name: instagram_posts uq_instagram_posts_instagram_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.instagram_posts
    ADD CONSTRAINT uq_instagram_posts_instagram_id UNIQUE (instagram_id);


--
-- Name: instagram_posts uq_instagram_posts_stop_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.instagram_posts
    ADD CONSTRAINT uq_instagram_posts_stop_id UNIQUE (stop_id);


--
-- Name: substack_posts uq_substack_posts_substack_id; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.substack_posts
    ADD CONSTRAINT uq_substack_posts_substack_id UNIQUE (substack_id);


--
-- Name: ix_instagram_posts_stop_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_instagram_posts_stop_id ON public.instagram_posts USING btree (stop_id);


--
-- Name: ix_instagram_posts_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_instagram_posts_timestamp ON public.instagram_posts USING btree ("timestamp");


--
-- Name: ix_stops_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stops_date ON public.stops USING btree (date);


--
-- Name: ix_stops_trip_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stops_trip_date ON public.stops USING btree (trip_id, date);


--
-- Name: ix_stops_trip_region; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stops_trip_region ON public.stops USING btree (trip_id, region_code);


--
-- Name: ix_stops_trip_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_stops_trip_status ON public.stops USING btree (trip_id, status);


--
-- Name: ix_substack_posts_published_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_substack_posts_published_at ON public.substack_posts USING btree (published_at);


--
-- Name: ix_substack_posts_stop_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_substack_posts_stop_id ON public.substack_posts USING btree (stop_id);


--
-- Name: ix_trips_start_end_date; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trips_start_end_date ON public.trips USING btree (start_date, end_date);


--
-- Name: stops fk_stops_region_code; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stops
    ADD CONSTRAINT fk_stops_region_code FOREIGN KEY (region_code) REFERENCES public.regions(iata_code) ON DELETE SET NULL;


--
-- Name: instagram_posts instagram_posts_stop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.instagram_posts
    ADD CONSTRAINT instagram_posts_stop_id_fkey FOREIGN KEY (stop_id) REFERENCES public.stops(id) ON DELETE CASCADE;


--
-- Name: stops stops_trip_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.stops
    ADD CONSTRAINT stops_trip_id_fkey FOREIGN KEY (trip_id) REFERENCES public.trips(id) ON DELETE CASCADE;


--
-- Name: substack_posts substack_posts_stop_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.substack_posts
    ADD CONSTRAINT substack_posts_stop_id_fkey FOREIGN KEY (stop_id) REFERENCES public.stops(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict BuRBpJr0XfYjmzMngiZfMPHJVu0rtQ9rSahBeGWUVGfUxduFJLEJZfZCa5sxjhS

