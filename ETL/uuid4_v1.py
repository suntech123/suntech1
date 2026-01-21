SELECT 
    t.description,
    -- Extract the UUID specifically associated with the DOC_ID key
    REGEXP_SUBSTR(
        t.description, 
        -- Pattern explanation below
        'DOC_DOC360_GLOBAL_DOC_ID\\s*=\\s*["\']?([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})["\']?', 
        1, 1, 'ie', 1
    ) as extracted_uuid
FROM 
    your_table_name t
WHERE 
    -- Filter to only show rows containing a valid V4 UUID for this specific key
    REGEXP_LIKE(
        t.description, 
        'DOC_DOC360_GLOBAL_DOC_ID\\s*=\\s*["\']?[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}',
        'i'
    );