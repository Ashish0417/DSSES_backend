from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "mysql+pymysql://root:yourpassword@mysql:3306/dsse_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # Store hashed passwords
    shared_key = Column(Text, nullable=False)  # Store encryption key for user
    files = relationship("EncryptedFile", back_populates="owner")  # Relationship to files

class EncryptedFile(Base):
    __tablename__ = "encrypted_files"
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    indexes = relationship("EncryptedIndex", back_populates="file")  # Relationship to indexes
    owner = relationship("User", back_populates="files")

class EncryptedIndex(Base):
    __tablename__ = "encrypted_index"
    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    file_id = Column(Integer, ForeignKey("encrypted_files.id"), nullable=False)
    keyword = Column(String(255), index=True, nullable=False)
    file = relationship("EncryptedFile", back_populates="indexes")

Base.metadata.create_all(bind=engine)
