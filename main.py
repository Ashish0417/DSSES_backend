from fastapi import FastAPI, File, Path,UploadFile,Query,Depends, HTTPException, status,Body
import os
import tempfile
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer ,OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, time, timedelta
from pydantic import BaseModel
from sqlalchemy import text
import time
from sqlalchemy.orm import Session
from database import EncryptedFile, EncryptedIndex, SessionLocal, User
from week1_dsse_txt import des_encrypt, des_decrypt, generate_key, tokenize_document, encrypt_keywords, build_index, generate_search_token
import fitz 
import speech_recognition as sr
from moviepy import AudioFileClip
import mp4_enc
from io import BytesIO
from fastapi.responses import StreamingResponse

app = FastAPI() 

#####################################################################################################


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  
        "http://127.0.0.1:5173",  
        "http://localhost:3000",  
        "http://127.0.0.1:3000", 
        "https://beamish-pastelito-d62e1b.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    expose_headers=["*"]  
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

# key = generate_key()  # Generate DES key
# encrypted_docs = []  # Store encrypted documents
# index = {}  # Store encrypted keyword index

class SignUpRequest(BaseModel):
    email: str
    user_name: str
    password: str


class FileDeleteRequest(BaseModel):
    file_path: str  # Expect JSON with file_path    

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

def extract_transcript(video_path: str) -> str:
    try:
        recognizer = sr.Recognizer()
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            audio_path = temp_audio.name
        
        # Extract audio from video without the verbose parameter
        try:
            audio_clip = AudioFileClip(video_path)
            audio_clip.write_audiofile(audio_path)  # Remove verbose and logger parameters
            audio_clip.close()
        except Exception as e:
            raise Exception(f"Failed to extract audio from video: {str(e)}")
        
        # Transcribe audio
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                transcript = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            transcript = ""  # No speech detected
        except sr.RequestError as e:
            raise Exception(f"Speech recognition service error: {str(e)}")
        finally:
            # Clean up temp audio file
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
        return transcript if transcript else "No speech detected in video"
        
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

def store_encrypted_metadata(db: Session, user_id: int, filename: str, file_path: str) -> int:
    db.execute(
        text("INSERT INTO encrypted_files (user_id, filename, file_path) VALUES (:user_id, :filename, :file_path)"),
        {"user_id": user_id, "filename": filename, "file_path": file_path}
    )
    db.commit()
    return db.execute(text("SELECT LAST_INSERT_ID()")).fetchone()[0]

def store_encrypted_index(db: Session, file_id: int, encrypted_words: list):
    if encrypted_words:
        keyword_values = [{"keyword": e_word, "file_id": file_id} for e_word in encrypted_words]
        db.execute(
            text("INSERT INTO encrypted_index (keyword, file_id) VALUES (:keyword, :file_id)"),
            keyword_values
        )
        db.commit()


def delete_temp_file(file_path: str):
    """Deletes the temporary file after response is sent."""
    if os.path.exists(file_path):
        os.remove(file_path)

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
async def upload_and_encrypt(file: UploadFile = File(...), user_id: int = Depends(get_current_user_info), db: Session = Depends(get_db)):
    # Validate file extension
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ["txt", "pdf", "mp4"]:
        raise HTTPException(
            status_code=400, 
            detail="Unsupported file type. Only .txt, .pdf, and .mp4 are allowed."
        )
    
    key_hex = db.execute(text("SELECT shared_key FROM users WHERE id = :user_id"), {"user_id": user_id}).fetchone()[0]
    key = bytes.fromhex(key_hex)
    user = db.query(User).filter(User.id == user_id).first()
    encrypted_file_path = os.path.join(ENCRYPTED_DIR, f"{user.username}_{file.filename}")
    # Handle MP4 files differently

    # encrypted_filename = f"{user.username}_{file.filename}"
    if file_extension == "mp4":
        try:
            # Save the MP4 file first
            file_content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False) as temp_video:
                temp_video.write(file_content)
                temp_video_path = temp_video.name
            
            mp4_enc.des_encrypt_file(temp_video_path, encrypted_file_path, key)
            
            
            file_id = store_encrypted_metadata(db, user_id, file.filename, encrypted_file_path)
            try:
                # Try to extract transcript - but continue even if this fails
                transcript = extract_transcript(temp_video_path)
                print(transcript)
                words = tokenize_document(transcript)
                encrypted_words = encrypt_keywords(words, key)
                store_encrypted_index(db, file_id, encrypted_words)
                os.remove(temp_video_path)  # Remove temporary file
                return {"message": "MP4 uploaded, transcript processed, and keywords indexed.", "filename": file.filename}
            
            except Exception as transcript_error:
                # If transcription fails, still keep the file but log the error
                print(f"Transcription error: {str(transcript_error)}")
                # Store the file with empty keywords
                os.remove(temp_video_path)  # Remove temporary file
                return {"message": "MP4 uploaded successfully, but transcript extraction failed.", "filename": file.filename}
        
        except Exception as e:
            # Handle any other errors
            raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
    
    else:
        # Handle TXT and PDF files as before
        try:
            file_content = await file.read()
            if file_extension == "txt":
                plain_text = file_content.decode("utf-8")
            elif file_extension == "pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                    temp_pdf.write(file_content)
                    temp_pdf_path = temp_pdf.name
                
                pdf_doc = fitz.open(temp_pdf_path)
                plain_text = "\n".join([page.get_text("text") for page in pdf_doc])
                pdf_doc.close()
                os.unlink(temp_pdf_path)  # Clean up temp file
            
            encrypted_text = des_encrypt(plain_text, key)
            encrypted_file_path = os.path.join(ENCRYPTED_DIR, f"{user.username}_{file.filename}")
            
            with open(encrypted_file_path, "w", encoding="utf-8") as enc_file:
                enc_file.write(encrypted_text)
            
            file_id = store_encrypted_metadata(db, user_id, file.filename, encrypted_file_path)
            words = tokenize_document(plain_text)
            encrypted_words = encrypt_keywords(words, key)
            store_encrypted_index(db, file_id, encrypted_words)
            
            return {"message": "File encrypted & indexed successfully", "filename": file.filename}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/files/")
async def list_files(user_id: int = Depends(get_current_user_info), db: Session = Depends(get_db)):
    try:
        files = db.execute(
            text("SELECT file_path FROM encrypted_files WHERE user_id = :user_id"),
            {"user_id": user_id}
        ).fetchall()
        
        return {"files": [file[0] for file in files]}
    except Exception as e:
        # Improved error handling
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving files: {str(e)}"
        )


@app.get("/search/")
async def search_keyword(keyword: str = Query(...),user_id :int = Depends(get_current_user_info),db : Session= Depends(get_db)):
    key_hex = db.execute(text("SELECT shared_key FROM users WHERE id =:user_id"),{"user_id":user_id}).fetchone()[0]
    key = bytes.fromhex(key_hex) 
    encrypt_keyword = generate_search_token(keyword, key)
    print(encrypt_keyword)
    matching_files = db.execute(
        text("SELECT file_id FROM encrypted_index WHERE keyword = :keyword"),
        {"keyword": encrypt_keyword}
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

@app.delete("/delete/")
async def delete_file(request: FileDeleteRequest, db: Session = Depends(get_db)):
    file_path = request.file_path
    base_dir = "encrypted_files/"
    
    if not file_path.startswith(base_dir):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find the file entry first
    file_entry = db.query(EncryptedFile).filter(EncryptedFile.file_path == file_path).first()
    
    if not file_entry:
        raise HTTPException(status_code=404, detail="File not found in database")
    
    # Remove physical file
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Explicitly handle related EncryptedIndex entries
    db.query(EncryptedIndex).filter(EncryptedIndex.file_id == file_entry.id).delete(synchronize_session=False)
    
    # Then delete the file entry
    db.delete(file_entry)
    db.commit()

    return {"message": "File deleted successfully"}


@app.get("/download/{file_path:path}")
async def download_file(file_path: str = Path(...),user_id :int = Depends(get_current_user_info),db: Session = Depends(get_db)):
    print(file_path)
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        

        file_extension = file_path.split(".")[-1].lower()

        key_hex = db.execute(text("SELECT shared_key FROM users WHERE id =:user_id"), {"user_id": user_id}).fetchone()[0]
        key = bytes.fromhex(key_hex)

        if file_extension == "mp4":
            # Decrypt video file into memory
            decrypted_video = BytesIO()
            
            # Create a temporary file to hold decrypted video
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                temp_file_path = temp_file.name

            mp4_enc.des_decrypt_file(file_path, temp_file_path, key)  # Decrypt the file
            
            # Read the decrypted file into memory
            with open(temp_file_path, "rb") as temp_file:
                decrypted_video.write(temp_file.read())

            decrypted_video.seek(0)  # Reset pointer
            os.remove(temp_file_path)  # Clean up temporary file after reading

            return StreamingResponse(decrypted_video, media_type="video/mp4", headers={
                "Content-Disposition": f"attachment; filename={os.path.basename(file_path)}"
            })

        with open(file_path, "r", encoding="utf-8") as enc_file:
            encrypted_data = enc_file.read()

        decrypted_text = des_decrypt(encrypted_data, key)

        decrypted_file_extension = "txt" if file_path.endswith(".txt") else "pdf"
        temp_suffix = f".{decrypted_file_extension}"

        with tempfile.NamedTemporaryFile(delete=False, suffix=temp_suffix) as temp_file:
            temp_file_path = temp_file.name
            if decrypted_file_extension == "txt":
                temp_file.write(decrypted_text.encode("utf-8"))
            else:  # Convert decrypted text back to a PDF
                pdf_doc = fitz.open()
                page = pdf_doc.new_page()
                page.insert_text((50, 50), decrypted_text)
                pdf_doc.save(temp_file_path)

        return FileResponse(temp_file_path, filename=os.path.basename(file_path), media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

