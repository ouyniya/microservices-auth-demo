# Key Features:

✅ 2FA Email OTP: 6-digit codes sent via email  
✅ Domain Restriction: Only company domain emails (e.g., @yourcompany.com)  
✅ Security: Password hashing, OTP expiration, JWT tokens  
✅ Single Sign-On: Login once, access both apps  
✅ Seamless Switching: Click links to switch between apps while staying logged in  
✅ Shared Logout: Logout from one app logs out of both  
✅ Session Persistence: Sessions survive app refreshes  



# Step 1 Create a file named .env in the folders:

## auth-service

.env

```
SECRET_KEY=
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=
COMPANY_DOMAIN=xxx.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

ALGORITHM please see https://bvsreyanth.medium.com/comparison-of-rs256-and-hs256-algorithms-for-token-signing-in-cryptography-bd21e9e7a54d

## app

.env

```
AUTH_SERVICE_URL=http://localhost:8000
```

---

# Step 2 Start all services


### Terminal 1: Auth Service

```bash
cd auth-service && python main.py
```


### Terminal 2: App 1

```bash
cd app1 && streamlit run streamlit_app.py --server.port 8501
```


### Terminal 3: App 2

```bash
cd app2 && streamlit run streamlit_app.py --server.port 8502
```


