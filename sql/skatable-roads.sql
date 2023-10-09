CREATE OR REPLACE VIEW skatable_roads AS
    SELECT * FROM "public"."planet_osm_line" WHERE 
        highway IS NOT NULL AND 
        (surface IS NULL OR surface IN ('asphalt', 'paved', 'chipseal')) AND 
        (tracktype IS NULL OR tracktype IN ('grade1')) AND 
        highway NOT IN ('path') AND 
        (tracktype IS NOT NULL OR surface IS NOT NULL)
