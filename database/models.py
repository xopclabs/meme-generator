from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker


engine = create_engine('sqlite:///memes.db', echo=True)
DeclarativeBase = declarative_base()
Session = sessionmaker(bind=engine)


class Public(DeclarativeBase):
    __tablename__ = 'public'

    id = Column(String(15), primary_key=True)
    domain = Column(String(50))

    def __repr__(self):
        return f'<Public: id={self.id}, domain={self.domain}>'


class Post(DeclarativeBase):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    public_id = Column(String(15), ForeignKey('public.id'))
    post_id = Column(String(10))
    date = Column(String(30))
    text = Column(Text)
    comments = Column(Integer)
    likes = Column(Integer)
    reposts = Column(Integer)
    views = Column(Integer)

    public = relationship('Public', back_populates='posts')

    def __repr__(self):
        return (f'<Post: id={self.id}, public_id={self.public_id}, post_id={self.post_id}, '
                f'date={self.date}, text={self.text}, comments={self.comments}, '
                f'likes={self.likes}, reposts={self.reposts}, views={self.views}>')


class Picture(DeclarativeBase):
    __tablename__ = 'picture'

    id = Column(Integer, primary_key=True)
    post_db_id = Column(String(10), ForeignKey('post.id'))
    picture = Column(BLOB)
    picture_index = Column(Integer)
    crop_positions = Column(Text)

    post = relationship('Post', back_populates='pictures')

    def __repr__(self):
        return (f'<Picture: id={self.id}, post_db_id={self.post_db_id}, picture_index={self.picture_index}, '
                f'crop_positions={self.crop_positions}>')


class Crop(DeclarativeBase):
    __tablename__ = 'crop'

    id = Column(Integer, primary_key=True)
    picture_id = Column(Integer, ForeignKey('picture.id'))
    picture = Column(BLOB)
    crop_index = Column(Integer)

    base = relationship('Picture', back_populates='crops')

    def __repr__(self):
        return f'<Crop: id={self.id}, picture_id={self.picture_id}, crop_index={self.crop_index}>'


# Set up relationships
Public.posts = relationship('Post', order_by=Post.date, back_populates='public')
Post.pictures = relationship('Picture', order_by=Picture.picture_index, back_populates='post')#, foreign_keys=[Post.post_id, Post.public_id])
Picture.crops = relationship('Crop', order_by=Crop.crop_index, back_populates='base')

DeclarativeBase.metadata.create_all(engine)
