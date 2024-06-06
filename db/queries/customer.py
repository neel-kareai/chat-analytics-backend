from sqlalchemy.orm import Session
from db.models.customer import Customer
from helper.security import get_hashed_password, verify_password


class CustomerQuery:

    @staticmethod
    def create_customer(db: Session, name: str, email: str, password: str):
        hashed_password = get_hashed_password(password)
        customer = Customer(name=name, email=email, password=hashed_password)
        db.add(customer)
        db.flush()

        return customer

    @staticmethod
    def get_customer_by_email(db: Session, email: str):
        return db.query(Customer).filter(Customer.email == email).first()

    @staticmethod
    def get_customer_by_uuid(db: Session, uuid: str):
        return db.query(Customer).filter(Customer.uuid == uuid).first()

    @staticmethod
    def get_customer_by_email_password(db: Session, email: str, password: str):
        customer = CustomerQuery.get_customer_by_email(db, email)
        if not customer:
            return None

        if not verify_password(password.encode("utf-8"), customer.password):
            return None

        return customer
