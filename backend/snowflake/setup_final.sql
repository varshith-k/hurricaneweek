-- Hurricane Week: Snowflake setup with real names from Snowflake Public Data.
-- Generated from setup.sql; names verified in Phase 2 discovery.
-- Run: python snowflake/run_sql.py --token setup --file snowflake/setup_final.sql
--
-- Data: SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE
--   FEMA_DISASTER_DECLARATION_INDEX (+ _AREAS_INDEX): DISASTER_TYPE = 'Hurricane', Miami-Dade COUNTY_GEO_ID = 'geoId/12086'
--   FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX: FLOOD_EVENT = 'Hurricane Irma' (no location column, so all states)
--   NOAA_WEATHER_METRICS_TIMESERIES: station USW00012839 (MIAMI INTL AP), VARIABLE = 'precipitation'

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

-- 2a. Distinct federal hurricane declarations (major disaster + emergency) covering Miami-Dade.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'miami_dade_hurricane_declarations',
       'Federal hurricane declarations (major disaster + emergency) covering Miami-Dade since 1965',
       COUNT(DISTINCT d.DISASTER_ID), 'declarations',
       'FEMA disaster declarations via Snowflake Public Data',
       'Distinct DISASTER_ID in FEMA_DISASTER_DECLARATION_INDEX where DISASTER_TYPE = ''Hurricane'', joined to FEMA_DISASTER_DECLARATION_AREAS_INDEX with COUNTY_GEO_ID = ''geoId/12086'' (Miami-Dade, formerly Dade). DR and EM declarations for the same storm count separately.'
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_INDEX d
JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_DISASTER_DECLARATION_AREAS_INDEX a
  ON a.DISASTER_ID = d.DISASTER_ID
WHERE d.DISASTER_TYPE = 'Hurricane' AND a.COUNTY_GEO_ID = 'geoId/12086';

-- 2b. NFIP claims from Hurricane Irma, all states (the claims data has no location column).
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'irma_nfip_claims_all_states',
       'NFIP flood insurance claims from Hurricane Irma (all states)',
       COUNT(*), 'claims',
       'FEMA NFIP claims via Snowflake Public Data',
       'FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX where FLOOD_EVENT = ''Hurricane Irma'' and DATE_OF_LOSS between 2017-09-09 and 2017-09-12. All states: the claims data has no county or state column, so this is not a Miami-Dade figure.'
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX
WHERE FLOOD_EVENT = 'Hurricane Irma' AND DATE_OF_LOSS BETWEEN '2017-09-09' AND '2017-09-12';

-- 2c. Average NFIP contents payout (> 0) for those claims.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'irma_avg_contents_paid_all_states',
       'Average NFIP payout for belongings (contents) after Hurricane Irma (all states)',
       ROUND(AVG(AMOUNT_PAID_ON_CONTENTS_CLAIM)), 'USD',
       'FEMA NFIP claims via Snowflake Public Data',
       'Mean AMOUNT_PAID_ON_CONTENTS_CLAIM over ' || COUNT(*) || ' claims with a contents payment > 0; FLOOD_EVENT = ''Hurricane Irma'', DATE_OF_LOSS 2017-09-09..2017-09-12, all states. Rounded to whole dollars.'
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.FEMA_NATIONAL_FLOOD_INSURANCE_PROGRAM_CLAIM_INDEX
WHERE FLOOD_EVENT = 'Hurricane Irma' AND DATE_OF_LOSS BETWEEN '2017-09-09' AND '2017-09-12'
  AND AMOUNT_PAID_ON_CONTENTS_CLAIM > 0;

-- 2d. Wettest single day at Miami International Airport during Irma.
INSERT INTO HURRICANE_WEEK.APP.FACTS (ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE)
SELECT 'irma_max_daily_rain_miami',
       'Most rain in one day at Miami International Airport during Hurricane Irma',
       MAX(VALUE), ANY_VALUE(UNIT),
       'NOAA weather station data via Snowflake Public Data',
       'Max daily VARIABLE = ''precipitation'' in NOAA_WEATHER_METRICS_TIMESERIES at station USW00012839 (MIAMI INTL AP), DATE 2017-09-09..2017-09-12.'
FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.NOAA_WEATHER_METRICS_TIMESERIES
WHERE NOAA_WEATHER_STATION_ID = 'USW00012839' AND VARIABLE = 'precipitation'
  AND DATE BETWEEN '2017-09-09' AND '2017-09-12';

SELECT ID, VALUE_NUM, UNIT, LABEL FROM HURRICANE_WEEK.APP.FACTS ORDER BY ID;
