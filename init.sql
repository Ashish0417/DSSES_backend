-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ${MYSQL_DATABASE};

-- Grant all privileges to root user from all hosts
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO 'root'@'localhost';
GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO 'root'@'%';
FLUSH PRIVILEGES;