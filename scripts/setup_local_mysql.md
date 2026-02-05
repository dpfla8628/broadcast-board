# 로컬 MySQL 설치/세팅 가이드

## macOS (Homebrew)
1. 설치
   - `brew install mysql@8.0`
2. 서비스 실행
   - `brew services start mysql@8.0`
3. 접속
   - `mysql -u root`

## Ubuntu/Debian
1. 설치
   - `sudo apt update`
   - `sudo apt install mysql-server`
2. 서비스 실행
   - `sudo systemctl start mysql`
3. 접속
   - `sudo mysql`

## Windows (WSL2)
1. WSL2 Ubuntu 설치 후 아래 명령 실행
   - `sudo apt update`
   - `sudo apt install mysql-server`
   - `sudo service mysql start`
2. 접속
   - `sudo mysql`

## DB 생성 및 계정 설정
```sql
CREATE DATABASE nkshop_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'nkshop_user'@'%' IDENTIFIED BY 'nkshop_password_1234';
GRANT ALL PRIVILEGES ON nkshop_local.* TO 'nkshop_user'@'%';
FLUSH PRIVILEGES;
```

## 접속 테스트
- `mysql -u nkshop_user -p -h 127.0.0.1 -P 3306 nkshop_local`
