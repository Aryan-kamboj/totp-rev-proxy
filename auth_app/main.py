import logging
from fastapi import FastAPI, Request, Cookie, HTTPException
from typing import Annotated
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import io
import json
import time
import base64
import pyotp
import qrcode
import jwt
from cryptography.fernet import Fernet
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auth_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CustomException(Exception):
    def __init__(self, status_code: int, detail: str, headers: dict = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(detail)

def handle_exception(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Exception occurred: {str(exc)}", exc_info=True)
    
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers
        )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )

load_dotenv()  # loads from .env by default
logger.info("Environment variables loaded successfully")

app = FastAPI()
app.add_exception_handler(Exception, handle_exception)
templates = Jinja2Templates(directory="templates")

# Rest of the original imports and code continues...



load_dotenv()  # loads from .env by default

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class SubmitOtpReqModel(BaseModel):
    otp: str

class ResetTotpSecretReqModel(BaseModel):
    password: str

@app.get("/verify")
def verify_is_logged_in(login_cookie: Annotated[str | None, Cookie()] = None):
    try:
        token = login_cookie 
        jwt_secret = os.getenv("JWT_SECRET")
        
        if not jwt_secret:
            logger.error("JWT_SECRET not found in environment variables")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )
            
        if token:
            logger.info("Attempting to decode JWT token")
            decoded = jwt.decode(token, jwt_secret, algorithms=["HS256"])
            logger.info("JWT token decoded successfully")
        else:
            logger.warning("Login cookie not provided")
            raise HTTPException(
                status_code=307,
                detail="Please login with the otp.",
                headers={"location": "/otp"}
            )
            
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise HTTPException(
            status_code=303,
            detail="Token has expired. Please login again.",
            headers={"location": "/otp"}
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token")
        raise HTTPException(
            status_code=303,
            detail="Invalid token. Please login again.",
            headers={"location": "/otp"}
        )
    except Exception as e:
        logger.error(f"Unexpected error in verify_is_logged_in: {str(e)}")
        raise HTTPException(
            status_code=303,
            detail="Internal server error",
            headers={"location": "/otp"}
        )

@app.get("/otp", response_class=HTMLResponse)
def get_otp_form(request: Request):
    try:
        saved_info = None
        try:
            with open("../data/data.txt", "r") as f:
                saved_info = f.read()
        except FileNotFoundError:
            logger.info("data.txt not found, generating new secret")
            saved_info = None
        except Exception as e:
            logger.error(f"Error reading data.txt: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        if saved_info:
            logger.info("Returning OTP form with existing secret")
            return templates.TemplateResponse("otp_form.html", {"request": request})
        
        logger.info("Generating new OTP secret")
        pt_secret = pyotp.random_base32()
        encryption_key = os.getenv("ENCRYPTION_KEY")

        if not encryption_key:
            logger.error("ENCRYPTION_KEY not found in environment variables")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        try:
            cipher = Fernet(encryption_key)
            encrypted_secret = cipher.encrypt(pt_secret.encode())
            with open("../data/data.txt", "w") as f:
                f.write(encrypted_secret.decode())
        except Exception as e:
            logger.error(f"Error encrypting or saving secret: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        protected_app_name = os.getenv("PROTECTED_APP_NAME") 
        if not protected_app_name:
            logger.error("PROTECTED_APP_NAME not found in environment variables defaulting to ProtectedRevProxy")
            protected_app_name = "ProtectedRevProxy"

        try:
            uri = pyotp.totp.TOTP(pt_secret).provisioning_uri(issuer_name=protected_app_name)
            img = qrcode.make(uri)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        logger.info("Returning create_otp template with QR code")
        return templates.TemplateResponse("create_otp.html", {
            "request": request,
            "qr_code_base64": img_str,
        })
    except Exception as e:
        logger.error(f"Unexpected error in get_otp_form: {str(e)}", exc_info=True)
        raise CustomException(
            status_code=500,
            detail="Internal server error"
        )


        

@app.post("/otp", response_class=HTMLResponse)
def submit_otp(request: Request, response: JSONResponse, body: SubmitOtpReqModel):
    try:
        otp = body.otp
        logger.info(f"Received OTP submission: {otp[:3]}xxx")  # Log only first 3 digits for security
        
        if not (len(otp) == 6 and otp.isdigit()):
            logger.warning("Invalid OTP format")
            raise CustomException(
                status_code=400,
                detail="Invalid OTP format. OTP must be 6 digits."
            )

        try:
            with open("../data/data.txt", "r") as f:
                encrypted_secret = f.read()
        except FileNotFoundError:
            logger.error("data.txt not found")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )
        except Exception as e:
            logger.error(f"Error reading data.txt: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            logger.error("ENCRYPTION_KEY not found in environment variables")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        try:
            cipher = Fernet(encryption_key)
            pt_secret = cipher.decrypt(encrypted_secret.encode())
            totp = pyotp.TOTP(pt_secret)
            correct_totp = totp.now()
        except Exception as e:
            logger.error(f"Error decrypting secret or generating TOTP: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        if otp == str(correct_totp):
            logger.info("OTP verification successful")
            jwt_secret = os.getenv("JWT_SECRET")
            if not jwt_secret:
                logger.error("JWT_SECRET not found in environment variables")
                raise CustomException(
                    status_code=500,
                    detail="Internal server error"
                )

            token = jwt.encode(
                {"verified_at": int(time.time()), "exp": time.time() + 18000},
                jwt_secret
            )
            message = "Logged In successfully."
        else:
            logger.warning("Invalid OTP provided")
            raise CustomException(
                status_code=401,
                detail="Invalid OTP. Please try again."
            )

        response = JSONResponse(
            content={"message": message},
            status_code=303,
            headers={"location": "/"}
        )
        
        if token:
            response.set_cookie(
                key="login_cookie",
                secure=True,
                samesite="none",
                path="/",
                value=token,
                max_age=60*60*5  # 5 hours
            )

        return response

    except CustomException as ce:
        logger.error(f"Custom exception in submit_otp: {str(ce)}")
        raise ce
    except Exception as e:
        logger.error(f"Unexpected error in submit_otp: {str(e)}", exc_info=True)
        raise CustomException(
            status_code=500,
            detail="Internal server error"
        )

@app.post("/reset-totp-secret", response_class=HTMLResponse)
def reset_totp_secret(request: Request, body: ResetTotpSecretReqModel):
    try:
        given_password = body.password
        reset_pass_env = os.getenv("TOTP_SECRET_RESET_PASSWORD")
        
        if not reset_pass_env:
            logger.error("TOTP_SECRET_RESET_PASSWORD not found in environment variables")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        if given_password != reset_pass_env:
            logger.warning("Invalid reset password provided")
            raise CustomException(
                status_code=401,
                detail="Invalid reset password"
            )

        logger.info("Reset password verified, generating new TOTP secret")
        pt_secret = pyotp.random_base32()
        
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            logger.error("ENCRYPTION_KEY not found in environment variables")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        try:
            cipher = Fernet(encryption_key)
            encrypted_secret = cipher.encrypt(pt_secret.encode())
            with open("../data/data.txt", "w") as f:
                f.write(encrypted_secret.decode())
        except Exception as e:
            logger.error(f"Error encrypting or saving new secret: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        try:
            uri = pyotp.totp.TOTP(pt_secret).provisioning_uri(issuer_name="ProtectedRevProxy")
            img = qrcode.make(uri)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            raise CustomException(
                status_code=500,
                detail="Internal server error"
            )

        logger.info("Returning create_otp template with new QR code")
        return templates.TemplateResponse("create_otp.html", {
            "request": request,
            "qr_code_base64": img_str,
            "secret": pt_secret 
        })
        
    except CustomException as ce:
        logger.error(f"Custom exception in reset_totp_secret: {str(ce)}")
        raise ce
    except Exception as e:
        logger.error(f"Unexpected error in reset_totp_secret: {str(e)}", exc_info=True)
        raise CustomException(
            status_code=500,
            detail="Internal server error"
        )
    
    # Return empty response for invalid password case
    return HTMLResponse()
