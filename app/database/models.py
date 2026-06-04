from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
try:
    from .config import *
except ImportError:
    from config import *

Base = declarative_base()


class Group(Base):
    __tablename__ = 'group'
    id = Column(Integer, primary_key=True)
    name = Column(String(OBJECT_NAME_LENGTH), nullable=False, unique=True)
    students = relationship('Student', back_populates='group')
    rooms = relationship('Room', back_populates='group')


class Student(Base):
    __tablename__ = 'student'
    id = Column(Integer, primary_key=True)
    name = Column(String(OBJECT_NAME_LENGTH), nullable=False)
    tg_id = Column(BigInteger, unique=True)
    id_group = Column(Integer, ForeignKey('group.id'))
    group = relationship('Group', back_populates='students')
    queues = relationship('Queue', back_populates='student')


class Room(Base):
    __tablename__ = 'room'
    id = Column(Integer, primary_key=True)
    name = Column(String(OBJECT_NAME_LENGTH), nullable=False)
    id_group = Column(Integer, ForeignKey('group.id'))
    group = relationship('Group', back_populates='rooms')
    questions = relationship('Question', back_populates='room')
    queues = relationship('Queue', back_populates='room')


class Question(Base):
    __tablename__ = 'question'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    correct_answer = Column(Text, nullable=False)
    wrong_answer1 = Column(Text, nullable=False)
    wrong_answer2 = Column(Text, nullable=False)
    wrong_answer3 = Column(Text, nullable=False)
    id_room = Column(Integer, ForeignKey('room.id'))
    room = relationship('Room', back_populates='questions')


class Queue(Base):
    __tablename__ = 'queue'
    id = Column(Integer, primary_key=True)
    id_student = Column(Integer, ForeignKey('student.id'))
    position = Column(Integer, nullable=False)
    id_room = Column(Integer, ForeignKey('room.id'))
    points = Column(Integer, default=0)
    student = relationship('Student', back_populates='queues')
    room = relationship('Room', back_populates='queues')


class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, nullable=False, unique=True)
