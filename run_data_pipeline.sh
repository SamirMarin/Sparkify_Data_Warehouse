#!/bin/bash

#run create_tables.py then etl.py
echo running create_tables.py
python3 create_tables.py
echo running etl.py
python3 etl.py
