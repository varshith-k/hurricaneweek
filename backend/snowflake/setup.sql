-- Hurricane Week: Snowflake setup template.
--
-- Phase 3 copies this file to setup_final.sql and replaces every <PLACEHOLDER>
-- with names discovered in Snowflake Public Data (Phase 2). Never guess names.
-- Run with:  python snowflake/run_sql.py --token setup --file snowflake/setup_final.sql
--
-- Placeholders
--   <PUBLIC_DB>.<PUBLIC_SCHEMA>       database/schema of Snowflake Public Data
--   <FEMA_DECLARATIONS_VIEW>          FEMA disaster declarations (one row per declared area)
--     <DECL_DISASTER_ID>              disaster number/id column
--     <DECL_INCIDENT_TYPE>            incident type column (value for hurricanes: <HURRICANE_VALUE>)
--     <DECL_AREA_FILTER>              boolean SQL expression selecting Miami-Dade (FIPS 12086)
--   <NFIP_CLAIMS_VIEW>                NFIP flood insurance claims
--     <CLAIM_AREA_FILTER>             boolean SQL expression selecting Miami-Dade (FIPS 12086)
--     <CLAIM_DATE_OF_LOSS>            date-of-loss column
--     <CLAIM_CONTENTS_PAID>           amount paid on contents claim (USD)
--   <NOAA_TIMESERIES_VIEW>            NOAA weather time series
--     <TS_STATION_ID> <TS_VARIABLE> <TS_DATE> <TS_VALUE> <TS_UNIT>
--     <PRECIP_VARIABLE_FILTER>        boolean SQL expression selecting daily precipitation
--   <NOAA_STATION_INDEX_VIEW>         NOAA station index (used to find <MIAMI_STATION_ID>)
--   <SNOWFLAKE_USER>                  value of SNOWFLAKE_USER (always keep the double quotes)

-- 1. Compute and storage ------------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS HW_WH
  WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;
USE WAREHOUSE HW_WH;
CREATE DATABASE IF NOT EXISTS HURRICANE_WEEK;
CREATE SCHEMA IF NOT EXISTS HURRICANE_WEEK.APP;

-- 2. Real-world facts ---------------------------------------------------------
CREATE OR REPLACE TABLE HURRICANE_WEEK.APP.FACTS (
  ID          STRING PRIMARY KEY,
  LABEL       STRING NOT NULL,
  VALUE_NUM   NUMBER(38, 2),
  UNIT        STRING,
  SOURCE      STRING,
  NOTE        STRING,
  UPDATED_AT  TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
);

-- 2a. Distinct federal hurricane declarations that include Miami-Dade.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'miami_dade_hurricane_declarations',
       'Federal hurricane disaster declarations covering Miami-Dade',
       COUNT(DISTINCT <DECL_DISASTER_ID>), 'declarations',
       'FEMA disaster declarations via Snowflake Public Data',
       'Distinct <DECL_DISASTER_ID> where <DECL_INCIDENT_TYPE> = <HURRICANE_VALUE> and <DECL_AREA_FILTER>'
FROM <PUBLIC_DB>.<PUBLIC_SCHEMA>.<FEMA_DECLARATIONS_VIEW>
WHERE <DECL_INCIDENT_TYPE> = <HURRICANE_VALUE> AND <DECL_AREA_FILTER>;

-- 2b. NFIP claims in Miami-Dade with a date of loss during Hurricane Irma.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'irma_nfip_claims_miami_dade',
       'NFIP flood claims in Miami-Dade from Hurricane Irma',
       COUNT(*), 'claims',
       'FEMA NFIP redacted claims via Snowflake Public Data',
       '<CLAIM_AREA_FILTER> and <CLAIM_DATE_OF_LOSS> between 2017-09-09 and 2017-09-12'
FROM <PUBLIC_DB>.<PUBLIC_SCHEMA>.<NFIP_CLAIMS_VIEW>
WHERE <CLAIM_AREA_FILTER> AND <CLAIM_DATE_OF_LOSS> BETWEEN '2017-09-09' AND '2017-09-12';

-- 2c. Average contents payout (> 0) for those claims.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'irma_avg_contents_paid_miami_dade',
       'Average NFIP contents payout in Miami-Dade after Hurricane Irma',
       ROUND(AVG(<CLAIM_CONTENTS_PAID>)), 'USD',
       'FEMA NFIP redacted claims via Snowflake Public Data',
       'Mean of <CLAIM_CONTENTS_PAID> > 0; <CLAIM_AREA_FILTER>; date of loss 2017-09-09..2017-09-12'
FROM <PUBLIC_DB>.<PUBLIC_SCHEMA>.<NFIP_CLAIMS_VIEW>
WHERE <CLAIM_AREA_FILTER> AND <CLAIM_DATE_OF_LOSS> BETWEEN '2017-09-09' AND '2017-09-12'
  AND <CLAIM_CONTENTS_PAID> > 0;

-- 2d. Wettest single day at a Miami station during Irma.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'irma_max_daily_rain_miami',
       'Most rain in one day in Miami during Hurricane Irma',
       MAX(<TS_VALUE>), ANY_VALUE(<TS_UNIT>),
       'NOAA weather station data via Snowflake Public Data',
       'Max daily precipitation at station <MIAMI_STATION_ID>, 2017-09-09..2017-09-12'
FROM <PUBLIC_DB>.<PUBLIC_SCHEMA>.<NOAA_TIMESERIES_VIEW>
WHERE <TS_STATION_ID> = '<MIAMI_STATION_ID>' AND <PRECIP_VARIABLE_FILTER>
  AND <TS_DATE> BETWEEN '2017-09-09' AND '2017-09-12';

SELECT * FROM HURRICANE_WEEK.APP.FACTS ORDER BY ID;

-- 3. Knowledge base for RAG ---------------------------------------------------
-- Rows come from backend/app/data/assistant_knowledge.json (question + answer as
-- CHUNK, SOURCE 'Verified Hurricane Week content (<status>)') plus one chunk per
-- FACTS row. Escape single quotes by doubling them ('').
CREATE OR REPLACE TABLE HURRICANE_WEEK.APP.KNOWLEDGE (
  ID         STRING PRIMARY KEY,
  CHUNK      STRING NOT NULL,
  SOURCE     STRING NOT NULL,
  EMBEDDING  VECTOR(FLOAT, 768)
);

-- Example knowledge row (repeat for every JSON entry):
-- INSERT INTO HURRICANE_WEEK.APP.KNOWLEDGE (ID, CHUNK, SOURCE)
-- VALUES ('kb:<id>', '<question> <answer>', 'Verified Hurricane Week content (<status>)');

INSERT INTO HURRICANE_WEEK.APP.KNOWLEDGE (ID, CHUNK, SOURCE)
SELECT 'fact:' || ID,
       LABEL || ': ' || TO_VARCHAR(VALUE_NUM) || ' ' || COALESCE(UNIT, '') || '. ' || COALESCE(NOTE, ''),
       SOURCE
FROM HURRICANE_WEEK.APP.FACTS;

UPDATE HURRICANE_WEEK.APP.KNOWLEDGE
SET EMBEDDING = SNOWFLAKE.CORTEX.EMBED_TEXT_768('<EMBED_MODEL>', CHUNK);

-- Vector search test.
SELECT ID, SOURCE,
       VECTOR_COSINE_SIMILARITY(EMBEDDING,
         SNOWFLAKE.CORTEX.EMBED_TEXT_768('<EMBED_MODEL>', 'Does renters insurance cover flooding?')) AS SCORE
FROM HURRICANE_WEEK.APP.KNOWLEDGE
ORDER BY SCORE DESC
LIMIT 3;

-- 4. Least-privilege role for the backend --------------------------------------
CREATE ROLE IF NOT EXISTS HW_APP;
GRANT USAGE ON WAREHOUSE HW_WH TO ROLE HW_APP;
GRANT USAGE ON DATABASE HURRICANE_WEEK TO ROLE HW_APP;
GRANT USAGE ON SCHEMA HURRICANE_WEEK.APP TO ROLE HW_APP;
GRANT SELECT ON TABLE HURRICANE_WEEK.APP.FACTS TO ROLE HW_APP;
GRANT SELECT ON TABLE HURRICANE_WEEK.APP.KNOWLEDGE TO ROLE HW_APP;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE HW_APP;
GRANT ROLE HW_APP TO USER "<SNOWFLAKE_USER>";

-- 5. App token (Phase 5, run separately with --capture-token SNOWFLAKE_PAT) -------
-- ALTER USER "<SNOWFLAKE_USER>" ADD PROGRAMMATIC ACCESS TOKEN HW_BACKEND
--   ROLE_RESTRICTION = 'HW_APP' DAYS_TO_EXPIRY = 7 COMMENT = 'Hurricane Week backend';
