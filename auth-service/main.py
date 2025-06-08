from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
import uuid
from pathlib import Path

from database import get_db, User, OTPToken
from models import UserCreate, UserLogin, OTPVerify, Token
from auth import verify_password, get_password_hash, create_access_token, verify_token
from email_service import generate_otp, send_otp_email

load_dotenv()

app = FastAPI(title="Authentication Service")
security = HTTPBearer()

COMPANY_DOMAIN = os.getenv("COMPANY_DOMAIN")

@app.post("/register")
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if email domain is allowed
    email_domain = user.email.split("@")[1]
    if email_domain != COMPANY_DOMAIN:
        raise HTTPException(
            status_code=400,
            detail=f"Registration only allowed for {COMPANY_DOMAIN} domain"
        )
    
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {"message": "User registered successfully"}

@app.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # Verify user credentials
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Generate and send OTP
    otp_code = generate_otp()
    
    # Store OTP in database
    otp_token = OTPToken(email=user.email, otp_code=otp_code)
    db.add(otp_token)
    db.commit()
    
    # Send OTP via email
    if not send_otp_email(user.email, otp_code):
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    
    return {"message": "OTP sent to your email"}

@app.post("/verify-otp", response_model=Token)
async def verify_otp(otp_data: OTPVerify, db: Session = Depends(get_db)):
    # Check OTP validity (within 5 minutes)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    otp_token = db.query(OTPToken).filter(
        OTPToken.email == otp_data.email,
        OTPToken.otp_code == otp_data.otp_code,
        OTPToken.created_at > five_minutes_ago,
        OTPToken.is_used == False
    ).first()
    
    if not otp_token:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Mark OTP as used
    otp_token.is_used = True
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": otp_data.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/verify-token")
async def verify_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    email = verify_token(credentials.credentials)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return {"email": email}


@app.post("/create-session")
async def create_session(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Create a shared session that can be used across apps"""
    try:
        email = verify_token(credentials.credentials)
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Create a session ID
        session_id = str(uuid.uuid4())
        
        # Store session data
        session_data = {
            "email": email,
            "token": credentials.credentials,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }
        
        # Create sessions directory if it doesn't exist
        sessions_dir = Path("sessions")
        sessions_dir.mkdir(exist_ok=True)
        
        # Save session to file
        session_file = sessions_dir / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(session_data, f)

            
        # ✅ Debug log
        print(f"[DEBUG] Writing session to: {session_file.resolve()}")
        
        return {"session_id": session_id}
    except Exception as e:
        print(f"Session creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@app.get("/get-session/{session_id}")
async def get_session(session_id: str):
    """Retrieve session data by session ID"""
    try:
        session_file = Path("sessions") / f"{session_id}.json"
        
        if not session_file.exists():
            raise HTTPException(status_code=404, detail="Session not found")
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Check if session is expired
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.utcnow() > expires_at:
            # Clean up expired session
            session_file.unlink()
            raise HTTPException(status_code=401, detail="Session expired")
        
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Session retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session")

@app.delete("/cleanup-sessions")
async def cleanup_expired_sessions():
    """Clean up expired sessions (can be called periodically)"""
    try:
        sessions_dir = Path("sessions")
        if not sessions_dir.exists():
            return {"message": "No sessions directory"}
        
        cleaned = 0
        for session_file in sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.utcnow() > expires_at:
                    session_file.unlink()
                    cleaned += 1
            except Exception:
                # If we can't read the file, delete it
                session_file.unlink()
                cleaned += 1
        
        return {"message": f"Cleaned up {cleaned} expired sessions"}
    except Exception as e:
        print(f"Session cleanup error: {e}")
        return {"message": "Cleanup failed"}
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)