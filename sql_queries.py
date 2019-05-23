import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create = ("""CREATE TABLE IF NOT EXISTS staging_events\
                                (\
                                    artist varchar,\
                                    auth varchar,\
                                    firstName varchar,\
                                    gender varchar,\
                                    itemInSession int,\
                                    lastName varchar,\
                                    length numeric,\
                                    level varchar,\
                                    location varchar,\
                                    method varchar,\
                                    page varchar,\
                                    registration varchar,\
                                    sessionId int,\
                                    song varchar,\
                                    status int,\
                                    ts varchar,\
                                    userAgent varchar,\
                                    userId int\
                                );\
                            """)

staging_songs_table_create= ("""CREATE TABLE IF NOT EXISTS staging_songs\
                                (\
                                    artist_id varchar,\
                                    artist_latitude numeric,\
                                    artist_location varchar,\
                                    artist_longitude numeric,\
                                    artist_name varchar,\
                                    duration numeric,\
                                    num_songs int,\
                                    song_id varchar,\
                                    title varchar,\
                                    year int\
                                );\
                            """)

songplay_table_create = ("""CREATE TABLE IF NOT EXISTS songplays\
                            (\
                                songplay_id int IDENTITY(0,1) NOT NULL PRIMARY KEY,\
                                start_time timestamp REFERENCES time(start_time),\
                                user_id int REFERENCES users(user_id),\
                                level varchar,\
                                song_id varchar REFERENCES songs(song_id),\
                                artist_id varchar REFERENCES artists(artist_id),\
                                session_id int,\
                                location varchar,\
                                user_agent varchar\
                            );\
                         """)

user_table_create = ("""CREATE TABLE IF NOT EXISTS users\
                        (\
                            user_id int NOT NULL PRIMARY KEY,\
                            first_name varchar,\
                            last_name varchar,\
                            gender varchar,\
                            level varchar\
                        );\
                    """)

song_table_create = ("""CREATE TABLE IF NOT EXISTS songs\
                        (\
                            song_id varchar NOT NULL PRIMARY KEY,\
                            title varchar,\
                            artist_id varchar REFERENCES artists(artist_id),\
                            year int,\
                            duration numeric\
                        );\
                    """)

artist_table_create = ("""CREATE TABLE IF NOT EXISTS artists\
                       (\
                            artist_id varchar NOT NULL PRIMARY KEY,\
                            name varchar,\
                            location varchar,\
                            latitude numeric,\
                            longitude numeric\
                       );\
                       """)

time_table_create = ("""CREATE TABLE IF NOT EXISTS time\
                        (\
                            start_time timestamp NOT NULL PRIMARY KEY,\
                            hour int,\
                            day int,\
                            week int,\
                            month int,\
                            year int,\
                            weekday int\
                        );\
                    """)

# STAGING TABLES
staging_events_copy = ("""COPY staging_events \
                          FROM {} \
                          CREDENTIALS 'aws_iam_role={}' \
                          FORMAT AS JSON {} \
                       """).format(config.get('S3','LOG_DATA'),config.get('IAM_ROLE','ARN'),config.get('S3','LOG_JSONPATH'))

staging_songs_copy = ("""COPY staging_songs \
                         FROM {} \
                         CREDENTIALS 'aws_iam_role={}' \
                         FORMAT AS JSON 'auto' \
                      """).format(config.get('S3','SONG_DATA'),config.get('IAM_ROLE','ARN'))

# FINAL TABLES

songplay_table_insert = ("""INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent) \
                            SELECT DISTINCT (timestamp 'epoch' + (((e.ts)::bigint)/1000) * interval '1 second') AS start_time, \
                                   e.userId AS user_id, \
                                   e.level AS level, \
                                   s.song_id AS song_id, \
                                   s.artist_id AS artist_id, \
                                   e.sessionId AS session_id, \
                                   e.location AS location, \
                                   e.userAgent AS user_agent \
                            FROM staging_events e \
                            JOIN staging_songs s ON (e.song=s.title AND e.artist=s.artist_name AND e.length=s.duration) \
                            WHERE e.page='NextSong' \
                        """)

user_table_insert = ("""INSERT INTO users (user_id, first_name, last_name, gender, level) \
                        SELECT DISTINCT userId AS user_id, \
                               firstName AS first_name, \
                               lastName AS last_name, \
                               gender, \
                               level \
                        FROM staging_events \
                        WHERE page='NextSong' \
                    """)

song_table_insert = ("""INSERT INTO songs (song_id, title, artist_id, year, duration) \
                        SELECT DISTINCT song_id, title, artist_id, year, duration \
                        FROM staging_songs \
                     """)

artist_table_insert = ("""INSERT INTO artists (artist_id, name, location, latitude, longitude) \
                          SELECT DISTINCT artist_id, \
                                 artist_name AS name, \
                                 artist_location AS location, \
                                 artist_latitude AS latitude, \
                                 artist_longitude AS longitude \
                          FROM staging_songs \
                       """)

time_table_insert = ("""INSERT INTO time (start_time, hour, day, week, month, year, weekday) \
                        SELECT DISTINCT (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second') AS start_time, \
                               EXTRACT(hour from (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second')) AS hour, \
                               EXTRACT(day from (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second')) AS day, \
                               EXTRACT(week from (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second')) AS week, \
                               EXTRACT(month from (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second')) AS month, \
                               EXTRACT(year from (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second')) AS year, \
                               EXTRACT(dayofweek from (timestamp 'epoch' + (((ts)::bigint)/1000) * interval '1 second')) AS weekday \
                        FROM staging_events \
                        WHERE page='NextSong' \
                    """)

# QUERY LISTS
create_table_queries = [staging_events_table_create, staging_songs_table_create, time_table_create, artist_table_create, song_table_create, user_table_create, songplay_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
