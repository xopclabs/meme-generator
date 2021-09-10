from sqlalchemy import Column, Integer, String, Text, \
    ForeignKey, ForeignKeyConstraint, desc
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import relationship
from database.engine import Base, engine


class Public(Base):
    __tablename__ = 'public'

    id = Column(String(15), primary_key=True)
    domain = Column(String(50), primary_key=True)

    def __repr__(self):
        return f'<Public: id={self.id}, domain={self.domain}>'


class Post(Base):
    __tablename__ = 'post'

    public_id = Column(String(15), ForeignKey('public.id'), primary_key=True)
    post_id = Column(String(10), primary_key=True)
    date = Column(String(30), nullable=False)
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


class Meme(Base):
    __tablename__ = 'meme'

    id = Column(Integer, primary_key=True)
    public_id = Column(String(15), nullable=False)
    post_id = Column(String(10), nullable=False)
    picture = Column(BLOB, nullable=False)
    index = Column(Integer)
    crop_positions = Column(BLOB)

    post = relationship('Post', back_populates='pictures')

    __table_args__ = (ForeignKeyConstraint(
        ['public_id', 'post_id'], ['post.public_id', 'post.post_id'],
        onupdate='CASCADE', ondelete='CASCADE'
    ), {})

    def __repr__(self):
        return (f'<Meme: id={self.id}, post_db_id={self.post_db_id}, picture_index={self.picture_index}, '
                f'crop_positions={self.crop_positions}>')


class Crop(Base):
    __tablename__ = 'crop'

    id = Column(Integer, primary_key=True)
    meme_id = Column(Integer, ForeignKey('meme.id'))
    picture = Column(BLOB)
    index = Column(Integer)
    text = Column(Text)

    base = relationship('Meme', back_populates='crops')

    def __repr__(self):
        return f'<Crop: id={self.id}, meme_id={self.meme_id}, crop_index={self.crop_index}>'


# Set up relationships
Public.posts = relationship('Post', order_by=desc(Post.date), back_populates='public')
Post.pictures = relationship('Meme', order_by=Meme.index, back_populates='post')
Meme.crops = relationship('Crop', order_by=Crop.index, back_populates='base')

Base.metadata.create_all(engine)
