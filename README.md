# DSSES Backend

## Overview
DSSES (Dynamic Searchable Symmetric Encryption) is a backend system designed to securely store, encrypt, and search text and PDFs while ensuring data integrity and confidentiality. This project is implemented using **FastAPI** for the backend and integrates encryption mechanisms to provide dynamic and efficient search capabilities.

## Features ✨
- **Encryption & Decryption** 🔐
  - Implements DES in ECB mode for encrypting text and PDF files.
  - Supports **PDF**, **text**, and **MP4** file encryption.
  - Ensures exact decryption without data loss.
- **Dynamic Searchable Encryption** 🔍
  - Enables efficient keyword-based searching within encrypted files.
- **User Authentication** 👥
  - Each user has separate storage for encrypted files.
- **FastAPI Backend** ⚡
  - A robust API built using **FastAPI**.
- **Hosted Online** 🌍
  - Access the service via:
    ```
    dssesbackend-production.up.railway.app
    ```

## Installation & Setup 🛠️
### 1. Clone the Repository
```bash
git clone https://github.com/Ashish0417/DSSES_backend.git
cd DSSES_backend
```

### 2. Install Dependencies
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file and add your configurations (like database credentials).

### 4. Run the Server
```bash
uvicorn main:app --reload
```

## Tech Stack
- **Backend**: FastAPI (Python)
- **Encryption**: DES (ECB Mode)
- **Database**: MySQL (Railway App Hosted)
- **Deployment**: Railway App

## Installation

### Prerequisites
Ensure you have the following installed:
- Python 3.10+
- MySQL
- pip (Python package manager)

### Setup Instructions
1. Clone the repository:
   ```sh
   git clone https://github.com/Ashish0417/DSSES_backend.git
   cd DSSES_backend
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   Create a `.env` file and add the necessary database credentials:
   ```env
   DATABASE_URL=mysql://<username>:<password>@<host>:<port>/<database>
   SECRET_KEY=your_secret_key
   ```
4. Run database migrations:
   ```sh
   alembic upgrade head
   ```
5. Start the FastAPI server:
   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Endpoints
### **Authentication**
- `POST /register/` - Register a new user
- `POST /login/` - Authenticate user and obtain token

### **File Management**
- `POST /upload/` - Upload and encrypt a file
- `GET /download/{file_id}/` - Decrypt and download a file

### **Search**
- `POST /search/` - Perform secure search on encrypted data

## Usage
After starting the server, open the FastAPI documentation:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Deployment
1. Deploy using **Railway** or any cloud provider:
   ```sh
   railway up
   ```
2. Ensure database credentials are correctly set in Railway’s environment variables.

## Contributing
Feel free to contribute! Fork the repo, create a new branch, and submit a pull request.

## License
This project is licensed under the MIT License.

---
Maintained by **Ashish0417** and contributors.


