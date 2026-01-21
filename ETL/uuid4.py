SELECT 
    t.*,
    -- Extract the actual UUID found for verification
    REGEXP_SUBSTR(
        t.large_text_field, 
        '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',
        1, 1, 'i'
    ) as found_uuid
FROM 
    your_table_name t
WHERE 
    REGEXP_LIKE(
        t.large_text_field, 
        -- The Regex for UUID v4
        '[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',
        'i' -- Case insensitive (matches A-F and a-f)
    );




--------------------------

WHERE REGEXP_LIKE(
    t.large_text_field, 
    '\\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\\b',
    'i'
);