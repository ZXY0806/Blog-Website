drop database if exits blog_website;
create database blog_website;
use blog_website;
create user 'blog_admin'@'localhost' identified by 'password';
alter user 'blog_admin'@'localhost' identified with mysql_native_password by 'password';
grant insert, select, update, delete on blog_website.* to 'blog_admin'@'localhost';

create table users(
    `id` varchar(50) not null,
    `email` varchar(50) not null,
    `name` varchar(50) not null,
    `passwd` varchar(50) not null,
    `image` varchar(500) not null,
    `admin` bool not null,
    `created_at` real not null,
    unique key `idx_email` (`email`),
    key `idx_created_at` (`created_at`),
    primary key (`id`)
)engine=innodb default charset=utf8;

create table blogs(
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `name` varchar(50) not null,
    `summary` varchar(200) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
)engine=innodb default charset=utf8;

create table comments(
    `id` varchar(50) not null,
    `user_id` varchar(50) not null,
    `user_name` varchar(50) not null,
    `user_image` varchar(500) not null,
    `blog_id` varchar(50) not null,
    `content` mediumtext not null,
    `created_at` real not null,
    key `idx_created_at` (`created_at`),
    primary key (`id`)
)engine=innodb default charset=utf8;

