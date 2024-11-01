# outputxml2postgres
Python script to parse the output.xml data to a postgres database 

## Parsing data
Parsing the output.xml data to the database: ```python .\output2postgres.py```  
Default input location is: results/output.xml  
To parse an xml file from a different location use the --input attribute: ```python .\output2postgres.py --input otherlocation/output.xml```

## Cleaning up data:
--retention_period "[value]"
example: python .\output2postgres.py ----retention_period "30 Days"
valid values are: MINUTES, HOURS, DAYS, MONTHS, YEARS


## Docker
The docker-compose.yaml generates 3 containers
To start the docker containers do a docker compose up

__pg_data_rf:__
Contains a postgres database to store the RobotFramework output.xml data

__pg_grafana:__
Contains a postgres database that is used by Grafana

__grafana:__
Contains a Grafana installation

.env file
used bij vscode
contains database connection settings

## Grafna
http://localhost:3111/  
connections > datasources > add datasource
postgresql  
Host URL localhost *: pg_data_rf:5432
Database name *: my_data_rf_db
Usernam *: my_data_rf_user
Password *: my_data_rf_pwd
TLS/SSL Mode: Disable