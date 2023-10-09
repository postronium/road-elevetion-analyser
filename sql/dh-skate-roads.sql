CREATE OR REPLACE VIEW dh_skate_roads AS
    SELECT 
        r.osm_id AS osm_id, 
        r.way AS way, 
        r.name AS name, 
        p.total_curviness AS total_curviness,
        p.c_b + p.c_c + p.c_d + p.c_e + p.c_f AS local_curviness, 
        p.length AS length, 
        p.total_elevation AS total_elevation
    FROM skatable_roads r 
    INNER JOIN properties p ON p.osm_id = r.osm_id 
        WHERE c_c + c_b + c_d + c_e + c_f >= 1 OR
        p.total_curviness > 0.2;