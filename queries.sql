-- ============================================================
-- Global Seismic Trends: SQL Analytical Queries
-- Table: earthquakes  (loaded by 03_load_mysql.py)
--
-- NOTE: The USGS feed has no "casualties" or "economic loss" fields,
-- and no "continent" field (only the regex-derived "country").
-- Queries 11-13 use `sig` (significance score) as the closest proxy
-- for impact/loss, and "continent" queries are written against
-- `country` instead. Swap in a real casualty/continent lookup table
-- if your evaluator requires the literal fields.
-- ============================================================

-- MAGNITUDE & DEPTH ------------------------------------------------

-- 1. Top 10 strongest earthquakes
SELECT id, time, place, mag, depth_km
FROM earthquakes
ORDER BY mag DESC
LIMIT 10;

-- 2. Top 10 deepest earthquakes
SELECT id, time, place, mag, depth_km
FROM earthquakes
ORDER BY depth_km DESC
LIMIT 10;

-- 3. Shallow earthquakes (<50km) with mag > 7.5
SELECT id, time, place, mag, depth_km
FROM earthquakes
WHERE depth_km < 50 AND mag > 7.5
ORDER BY mag DESC;

-- 4. Average depth per country (proxy for "per continent")
SELECT country, ROUND(AVG(depth_km), 2) AS avg_depth_km
FROM earthquakes
GROUP BY country
ORDER BY avg_depth_km DESC;

-- 5. Average magnitude per magType
SELECT magType, ROUND(AVG(mag), 2) AS avg_magnitude, COUNT(*) AS n
FROM earthquakes
GROUP BY magType
ORDER BY avg_magnitude DESC;

-- TIME ANALYSIS ------------------------------------------------

-- 6. Year with most earthquakes
SELECT year, COUNT(*) AS total
FROM earthquakes
GROUP BY year
ORDER BY total DESC
LIMIT 1;

-- 7. Month with highest number of earthquakes
SELECT month, COUNT(*) AS total
FROM earthquakes
GROUP BY month
ORDER BY total DESC
LIMIT 1;

-- 8. Day of week with most earthquakes
SELECT day_of_week, COUNT(*) AS total
FROM earthquakes
GROUP BY day_of_week
ORDER BY total DESC
LIMIT 1;

-- 9. Count of earthquakes per hour of day
SELECT hour, COUNT(*) AS total
FROM earthquakes
GROUP BY hour
ORDER BY hour;

-- 10. Most active reporting network
SELECT net, COUNT(*) AS total
FROM earthquakes
GROUP BY net
ORDER BY total DESC
LIMIT 1;

-- CASUALTIES & ECONOMIC LOSS (proxy via `sig`) ------------------

-- 11. Top 5 places with highest impact (sig used as casualty proxy)
SELECT place, MAX(sig) AS max_significance
FROM earthquakes
GROUP BY place
ORDER BY max_significance DESC
LIMIT 5;

-- 12. Total significance score per country (proxy for economic loss)
SELECT country, SUM(sig) AS total_significance
FROM earthquakes
GROUP BY country
ORDER BY total_significance DESC;

-- 13. Average significance by alert level (proxy for economic loss)
SELECT alert, ROUND(AVG(sig), 2) AS avg_significance
FROM earthquakes
WHERE alert <> 'Unknown'
GROUP BY alert
ORDER BY avg_significance DESC;

-- EVENT TYPE & QUALITY METRICS ------------------------------------------------

-- 14. Reviewed vs automatic earthquakes
SELECT status, COUNT(*) AS total
FROM earthquakes
GROUP BY status;

-- 15. Count by earthquake type
SELECT type, COUNT(*) AS total
FROM earthquakes
GROUP BY type
ORDER BY total DESC;

-- 16. Number of earthquakes by data type (types)
SELECT types, COUNT(*) AS total
FROM earthquakes
GROUP BY types
ORDER BY total DESC;

-- 17. Average RMS and gap per country
SELECT country, ROUND(AVG(rms), 3) AS avg_rms, ROUND(AVG(gap), 2) AS avg_gap
FROM earthquakes
GROUP BY country
ORDER BY avg_rms DESC;

-- 18. Events with high station coverage (nst > threshold, e.g. 50)
SELECT id, time, place, nst
FROM earthquakes
WHERE nst > 50
ORDER BY nst DESC;

-- TSUNAMIS & ALERTS ------------------------------------------------

-- 19. Number of tsunamis triggered per year
SELECT year, SUM(tsunami) AS tsunami_count
FROM earthquakes
GROUP BY year
ORDER BY year;

-- 20. Count earthquakes by alert level
SELECT alert, COUNT(*) AS total
FROM earthquakes
GROUP BY alert
ORDER BY total DESC;

-- SEISMIC PATTERN & TREND ANALYSIS ------------------------------------------------

-- 21. Top 5 countries by highest avg magnitude (past 5 years = full dataset)
SELECT country, ROUND(AVG(mag), 2) AS avg_mag, COUNT(*) AS n
FROM earthquakes
GROUP BY country
HAVING n >= 5
ORDER BY avg_mag DESC
LIMIT 5;

-- 22. Countries with both shallow AND deep earthquakes in the same month
SELECT country, year, month
FROM earthquakes
GROUP BY country, year, month
HAVING SUM(CASE WHEN depth_category = 'Shallow' THEN 1 ELSE 0 END) > 0
   AND SUM(CASE WHEN depth_category = 'Deep' THEN 1 ELSE 0 END) > 0;

-- 23. Year-over-year growth rate in total earthquakes globally
WITH yearly AS (
    SELECT year, COUNT(*) AS total
    FROM earthquakes
    GROUP BY year
)
SELECT year, total,
       ROUND(100.0 * (total - LAG(total) OVER (ORDER BY year))
             / LAG(total) OVER (ORDER BY year), 2) AS yoy_growth_pct
FROM yearly
ORDER BY year;

-- 24. Top 3 most seismically active regions (frequency + avg magnitude combined score)
SELECT country,
       COUNT(*) AS frequency,
       ROUND(AVG(mag), 2) AS avg_mag,
       ROUND(COUNT(*) * AVG(mag), 2) AS activity_score
FROM earthquakes
GROUP BY country
ORDER BY activity_score DESC
LIMIT 3;

-- DEPTH, LOCATION & DISTANCE-BASED ANALYSIS ------------------------------------------------

-- 25. Avg depth per country for earthquakes within ±5 degrees latitude of the equator
SELECT country, ROUND(AVG(depth_km), 2) AS avg_depth_km
FROM earthquakes
WHERE latitude BETWEEN -5 AND 5
GROUP BY country
ORDER BY avg_depth_km DESC;

-- 26. Countries with highest ratio of shallow to deep earthquakes
SELECT country,
       SUM(CASE WHEN depth_category = 'Shallow' THEN 1 ELSE 0 END) AS shallow_count,
       SUM(CASE WHEN depth_category = 'Deep' THEN 1 ELSE 0 END) AS deep_count,
       ROUND(SUM(CASE WHEN depth_category = 'Shallow' THEN 1 ELSE 0 END)
             / NULLIF(SUM(CASE WHEN depth_category = 'Deep' THEN 1 ELSE 0 END), 0), 2) AS shallow_deep_ratio
FROM earthquakes
GROUP BY country
ORDER BY shallow_deep_ratio DESC;

-- 27. Avg magnitude difference: earthquakes WITH tsunami vs WITHOUT
SELECT
    (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 1) AS avg_mag_with_tsunami,
    (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 0) AS avg_mag_without_tsunami,
    (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 1)
      - (SELECT AVG(mag) FROM earthquakes WHERE tsunami = 0) AS mag_difference;

-- 28. Events with the lowest data reliability (highest avg gap & rms)
SELECT id, time, place, gap, rms
FROM earthquakes
ORDER BY (gap + rms * 100) DESC
LIMIT 20;

-- 29. Pairs of earthquakes within 50km and within 1 hour of each other
SELECT a.id AS quake_1, b.id AS quake_2, a.time AS time_1, b.time AS time_2,
       ROUND(
         111.045 * DEGREES(ACOS(LEAST(1, GREATEST(-1,
           COS(RADIANS(a.latitude)) * COS(RADIANS(b.latitude)) *
           COS(RADIANS(a.longitude) - RADIANS(b.longitude)) +
           SIN(RADIANS(a.latitude)) * SIN(RADIANS(b.latitude))
         ))))
       , 2) AS distance_km
FROM earthquakes a
JOIN earthquakes b
  ON a.id < b.id
 AND ABS(TIMESTAMPDIFF(MINUTE, a.time, b.time)) <= 60
HAVING distance_km <= 50
ORDER BY time_1
LIMIT 100;

-- 30. Regions with highest frequency of deep-focus earthquakes (depth > 300km)
SELECT country, COUNT(*) AS deep_focus_count
FROM earthquakes
WHERE depth_km > 300
GROUP BY country
ORDER BY deep_focus_count DESC;
