from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
import random
import string


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    picture = Column(String)
    email = Column(String, index=True, nullable=False)
    password_hash = Column(String(64))

    # def hash_password(self, password):
    #     self.password_hash = pwd_context.encrypt(password)

    # def verify_password(self, password):
    #     return pwd_context.verify(password, self.password_hash)

    # def generate_auth_token(self, expiration=600):
    #     s = Serializer(secret_key)
    #     return s.dumps({'id': self.id})

    # @staticmethod
    # def verify_auth_token(token):
    #     s = Serializer(secret_key)
    #     try:
    #         data = s.loads(token)
    #     except SignatureExpired:
    #         return None
    #     except BadSignature:
    #         return None
    #     user_id = data['id']
    #     return user_id


class Book(Base):
    __tablename__ = 'book'
    picture = Column(String)
    name = Column(String, nullable=False)
    author = Column(String)
    description = Column(String, nullable=False)
    link = Column(String)
    category = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'author': self.author,
        }


class Interaction(Base):
    __tablename__ = 'interaction'
    id = Column(Integer, primary_key=True)
    like = Column(Integer, default=0)
    book_id = Column(Integer, ForeignKey('book.id'))
    user_id = Column(Integer)
    marker = Column(String, default='0;')
    book = relationship(Book)


class Rating(Base):
    __tablename__ = 'rating'
    id = Column(Integer, primary_key=True)
    feedback = Column(String)
    star = Column(Integer)
    book_id = Column(Integer, ForeignKey('book.id'))
    user_id = Column(Integer)
    book = relationship(Book)


engine = create_engine('sqlite:///lan5.db')
Base.metadata.create_all(engine)
