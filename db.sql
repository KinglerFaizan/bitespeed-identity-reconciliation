CREATE DATABASE IF NOT EXISTS bitespeed_db;
USE bitespeed_db;

CREATE TABLE IF NOT EXISTS Contact (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    phoneNumber     VARCHAR(20)  NULL,
    email           VARCHAR(255) NULL,
    linkedId        INT          NULL,
    linkPrecedence  ENUM('primary', 'secondary') NOT NULL DEFAULT 'primary',
    createdAt       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
    updatedAt       DATETIME(3)  NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
    deletedAt       DATETIME(3)  NULL
);