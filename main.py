from fastapi import FastAPI, File,UploadFile,Query,Depends, HTTPException, status
import os
from fastapi.security import OAuth2PasswordBearer ,OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, time, timedelta
from pydantic import BaseModel
from sqlalchemy import text
import time
from sqlalchemy.orm import Session
from database import SessionLocal, User
from week1_dsse_txt import des_encrypt, des_decrypt, generate_key, tokenize_document, encrypt_keywords, build_index, generate_search_token


app = FastAPI() 

#####################################################################################################


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this if your frontend runs on a different origin
    allow_credentials=True,
    allow_methods=["*"],  # This enables OPTIONS requests
    allow_headers=["*"],  # Allows all headers
)



######################################################################################################


SECRET_KEY = "ashish_asmita"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXP_MIN = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

pwd_context = CryptContext(schemes=['bcrypt'],deprecated ="auto")


UPLOAD_DIR = "uploads"
ENCRYPTED_DIR = "encrypted_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ENCRYPTED_DIR, exist_ok=True)

key = generate_key()  # Generate DES key
encrypted_docs = []  # Store encrypted documents
index = {}  # Store encrypted keyword index

class SignUpRequest(BaseModel):
    email: str
    user_name: str
    password: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password:str):
    return pwd_context.hash(password)

def verify_password(plain_password:str,hashed_password:str):
    return pwd_context.verify(plain_password,hashed_password)

def create_access_token(data:dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow()+expires_delta
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,SECRET_KEY, algorithm=ALGORITHM)

@app.get("/")
def read_root():
    return {"message": "Hello Ashish !"}

@app.post("/signup/")
async def signup(form_data : SignUpRequest , db:Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == form_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail= "Email already registred")
    
    shared_key = generate_key().hex()
    hashed_password = hash_password(form_data.password)

    new_user = User(email = form_data.email, username = form_data.user_name,password = hashed_password,shared_key= shared_key)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)#??

    return {"message": "User registered successfully", "email": form_data.email, "shared_key": shared_key}

@app.post("/login/")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password,user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    acess_token = create_access_token(data = {"sub": user.email},expires_delta=timedelta(minutes= ACCESS_TOKEN_EXP_MIN))
    return {"access_token":acess_token ,"token_type":"bearer","username":user.username  }


@app.post("/users/me")
async def get_current_user_info(token: str = Depends(oauth2_scheme), db:Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid Token")
    except JWTError:
        raise HTTPException(status_code=401, detail= "Invalid Token")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401 , detail="User not Exist")
    
    return user.id

@app.post("/upload-text-file/")
async def upload_etxt_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_location,"wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename , "message":"File Uploaded sucessfully"}

@app.post("/upload-and-encrypt/")
async def upload_and_encrypt(file: UploadFile = File(...),user_id :int = Depends(get_current_user_info),db: Session = Depends(get_db)):
    file_content = await file.read()
    plain_text = file_content.decode("utf-8")

    encrypted_text = des_encrypt(plain_text, key)
    encrypted_docs.append(encrypted_text)

    # Store the encrypted file
    encrypted_filename = f"encrypted_{file.filename}"
    encrypted_file_path = os.path.join(ENCRYPTED_DIR, encrypted_filename)

    with open(encrypted_file_path, "w", encoding="utf-8") as enc_file:
        enc_file.write(encrypted_text)

    db.execute(
        text("INSERT INTO encrypted_files (user_id, filename, file_path) VALUES (:user_id, :filename, :file_path)"),
        {"user_id":user_id,"filename":file.filename, "file_path":encrypted_file_path}
    )
    db.commit()

    file_id = db.execute(text("SELECT LAST_INSERT_ID()")).fetchone()[0]


    # Index the file for search
    words = tokenize_document(plain_text)
    encrypted_words = encrypt_keywords(words, key)

    for e_word in encrypted_words:
        db.execute(
            text("INSERT INTO encrypted_index (keyword, file_id) VALUES (:keyword, :file_id)"),
            {"keyword": e_word, "file_id" : file_id}
        )
        db.commit()

    return {"message": "File encrypted & indexed successfully", "filename": file.filename}


@app.get("/search/")
async def search_keyword(keyword: str = Query(...),user_id :int = Depends(get_current_user_info),db : Session= Depends(get_db)):
    encrypt_keyword = generate_search_token(keyword, key)
    print(encrypt_keyword)
    matching_files = db.execute(
        text("SELECT file_id FROM encrypted_index WHERE keyword = :keyword"),
        {"keyword": "S2rbPvAC/Ew="}
    ).fetchall()

    if not matching_files:
        return {"message":"No matches found"}
    print()
    print(matching_files)
    print()
    file_paths = []
    for row in matching_files:
        file_id = row[0]
        file_path = db.execute(
            text("SELECT file_path FROM encrypted_files WHERE id = :file_id AND user_id = :user_id"),
            {"file_id": file_id, "user_id":user_id}
        ).fetchone()

        if file_path:
            file_paths.append(file_path[0])
    print(file_paths)

    return{"file_found":list(file_paths)} 


