## auth-service

.env

```
SECRET_KEY=
ALGORITHM= 
ACCESS_TOKEN_EXPIRE_MINUTES=
COMPANY_DOMAIN=xxx.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=xxx@xxx.com
SMTP_PASSWORD=
```

ALGORITHM please see https://bvsreyanth.medium.com/comparison-of-rs256-and-hs256-algorithms-for-token-signing-in-cryptography-bd21e9e7a54d

## app

.env

```
AUTH_SERVICE_URL=http://localhost:8000
```

