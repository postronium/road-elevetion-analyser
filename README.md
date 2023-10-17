# Road Elevation Analyser
This is a tool to analyse the curviness and elevation of roads. The Goal is to be able to sort roads by elevation and curviness. The tool works open data.

## Usage

Create a **file/.env** file and add your database credentials in it.
Run the **setup-sql-database.sh** file to start the postgres postgis docker container.
Log into the postgres database and execute the sql scripts in the **./sql** folders.
Go to https://download.geofabrik.de/ to download some openstreetmap data for the roads.
Go to the https://www.usgs.gov to download some elevation maps.
After that you can load the osm data from an osm or osm.pbf file into the SQL database.
You can get all paved roads with the **paved_roads** view in the SQL database.

## TODO
* Load paved roads into graph database