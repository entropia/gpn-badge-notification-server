DROP TABLE IF EXISTS notifications;
CREATE TABLE notifications
(
    id SERIAL PRIMARY KEY NOT NULL,
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
