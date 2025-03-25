from fastapi import FastAPI, File,UploadFile,Query,Depends
import os
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal
from week1_dsse_txt import des_encrypt, des_decrypt, generate_key, tokenize_document, encrypt_keywords, build_index, generate_search_token
app = FastAPI()

UPLOAD_DIR = "uploads"
ENCRYPTED_DIR = "encrypted_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ENCRYPTED_DIR, exist_ok=True)

key = generate_key()  # Generate DES key
encrypted_docs = []  # Store encrypted documents
index = {}  # Store encrypted keyword index

@app.get("/")
def read_root():
    return {"message": "Hello Ashish !"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/upload-text-file/")
async def upload_etxt_file(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_location,"wb") as buffer:
        buffer.write(await file.read())

    return {"filename": file.filename , "message":"File Uploaded sucessfully"}

@app.post("/upload-and-encrypt/")
async def upload_and_encrypt(file: UploadFile = File(...),db: Session = Depends(get_db)):
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
        {"user_id":1,"filename":file.filename, "file_path":encrypted_file_path}
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




