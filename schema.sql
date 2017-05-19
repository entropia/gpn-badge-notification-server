-- psql gulasch_notifier -f schema.sql

DROP TABLE IF EXISTS channels;
CREATE TABLE channels
(
    id SERIAL PRIMARY KEY NOT NULL,
    url VARCHAR(20) NOT NULL UNIQUE,
    display_name VARCHAR(10) NOT NULL UNIQUE -- more than 10 chars does not fit on badge display
);

DROP TABLE IF EXISTS notifications;
CREATE TABLE notifications
(
    id SERIAL PRIMARY KEY NOT NULL,
    channel SERIAL references channels(id) NOT NULL,
    summary VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(255),
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP NOT NULL
);

DROP TABLE IF EXISTS users;
CREATE TABLE users
(
    id SERIAL PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    passhash VARCHAR(255) NOT NULL
);
