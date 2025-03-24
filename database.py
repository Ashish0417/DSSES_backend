from sqlalchemy import create_engine, Column , Integer, String ,Text
from sqlalchemy.orm import declarative_base ,sessionmaker

DATABASE_URL = "mysql+pymysql://root:@localhost/dsse_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autoflush= False, autocommit= False, bind = engine)
Base = declarative_base()

class EncryptedFile(Base):
    __tablename__ = "encrypted_files"
    id = Column(Integer, primary_key=True , index = True)
    filename = Column(String(255),unique=True)
    file_path = Column(String(255),nullable = False)

class EncryptedIndex(Base):
    __tablename__ = "encrypted_index"
    id = Column(Integer, primary_key=True , index = True)
    keyword = Column(String(255),index=True)
    file_id = Column(Integer)

Base.metadata.create_all(bind = engine)

