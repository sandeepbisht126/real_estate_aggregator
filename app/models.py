from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text
)
from sqlalchemy import DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Property(Base):

    __tablename__ = "properties"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    source = Column(String)

    title = Column(Text)

    price = Column(Float)

    living_space = Column(Float)

    rooms = Column(Float)

    bedrooms = Column(Float)

    bathrooms = Column(Float)

    floor = Column(String)

    property_type = Column(String)

    year_built = Column(Integer)

    hausgeld = Column(Float)

    provision = Column(Text)

    available_from = Column(String)

    balcony = Column(Boolean)

    city = Column(String)

    area = Column(String)

    energy_class = Column(String)

    posted_date = Column(DateTime)

    description = Column(Text)

    url = Column(Text, unique=True)