CREATE TABLE properties (
    id BIGSERIAL NOT NULL PRIMARY KEY,
    osm_id BIGINT NOT NULL UNIQUE,
    total_curviness DOUBLE PRECISION NOT NULL,
    c_a DOUBLE PRECISION NOT NULL,
    c_b DOUBLE PRECISION NOT NULL,
    c_c DOUBLE PRECISION NOT NULL,
    c_d DOUBLE PRECISION NOT NULL,
    c_e DOUBLE PRECISION NOT NULL,
    c_f DOUBLE PRECISION NOT NULL,
    length DOUBLE PRECISION NOT NULL, 
    total_elevation DOUBLE PRECISION NOT NULL
);