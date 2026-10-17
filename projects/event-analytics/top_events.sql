-- Frequency of each event_type, most common first. Mirrors validation in pipeline.py (ALLOWED_EVENTS).
SELECT event_type,
       COUNT(*) AS event_count
FROM events
GROUP BY event_type
ORDER BY event_count DESC, event_type ASC;
