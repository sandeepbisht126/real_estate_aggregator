from sqlalchemy import create_engine
from models import Base

DATABASE_URL = (
    "postgresql://postgres:postgres@localhost:5432/properties"
)

engine = create_engine(DATABASE_URL)

def create_tables():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    create_tables()
    print("Tables created")