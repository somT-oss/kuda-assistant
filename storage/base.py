import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


engine = create_engine(os.getenv("DATABASE_URL"))
Session = sessionmaker(bind=engine)

Base = declarative_base()