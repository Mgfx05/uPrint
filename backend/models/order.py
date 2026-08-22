from sqlalchemy import Column, Integer, String, Float

from models.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(String, unique=True, index=True)

    file_id = Column(String)

    pages = Column(Integer)

    copies = Column(Integer)

    print_type = Column(String)

    paper_size = Column(String, default="A4")

    sides = Column(String, default="single")

    orientation = Column(String, default="portrait")

    amount = Column(Float)

    payment_status = Column(
        String,
        default="pending"
    )

    print_status = Column(
        String,
        default="pending"
    )