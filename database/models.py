from sqlalchemy import Column, Integer, String, Text, \
    ForeignKey, ForeignKeyConstraint, desc
from sqlalchemy.dialects.sqlite import BLOB
from sqlalchemy.orm import relationship
from database.engine import Base, engine


class Public(Base):
    __tablename__ = 'public'

    id = Column(String(15), primary_key=True)
    domain = Column(String(50), nullable=False)

    posts = relationship(
        'Post',
        order_by=desc('Post.date'),
        backref='public',
        cascade='all, delete',
    )

    def __repr__(self):
        return f'<Public: id={self.id}, domain={self.domain}>'


class Post(Base):
    __tablename__ = 'post'

    id = Column(String(10), primary_key=True)
    public_id = Column(String(15), ForeignKey('public.id'), primary_key=True)
    date = Column(String(30), nullable=False)
    text = Column(Text)
    comments = Column(Integer)
    likes = Column(Integer)
    reposts = Column(Integer)
    views = Column(Integer)

    # public = relationship('Public', backref='posts')
    pictures = relationship(
        'Meme',
        order_by='Meme.index',
        backref='post',
        cascade='all, delete',
    )

    def __repr__(self):
        return (f'<Post: id={self.id}, public_id={self.public_id}, '
                f'date={self.date}, text={self.text}, comments={self.comments}, '
                f'likes={self.likes}, reposts={self.reposts}, views={self.views}>')


class Meme(Base):
    __tablename__ = 'meme'

    id = Column(Integer, primary_key=True)
    public_id = Column(String(15), nullable=False)
    post_id = Column(String(10), nullable=False)
    picture = Column(BLOB, nullable=False)
    index = Column(Integer)
    crop_positions = Column(Text)

    # post = relationship('Post', backref='pictures')
    crops = relationship(
        'Crop',
        order_by='Crop.index',
        backref='base',
        cascade='all, delete',
    )

    __table_args__ = (ForeignKeyConstraint(
        ['public_id', 'post_id'], ['post.public_id', 'post.id'],
        # onupdate='CASCADE', ondelete='CASCADE'
    ), {})

    def __repr__(self):
        return (f'<Meme: id={self.id}, public_id={self.public_id}, post_id={self.post_id}, '
                f'index={self.index}, crop_positions={self.crop_positions}>')


class Crop(Base):
    __tablename__ = 'crop'

    id = Column(Integer, primary_key=True)
    meme_id = Column(Integer, ForeignKey('meme.id'))
    picture = Column(BLOB)
    index = Column(Integer)
    text = Column(Text)

    # base = relationship('Meme', backref='crops', passive_deletes='all')

    def __repr__(self):
        return (f'<Crop: id={self.id}, meme_id={self.meme_id}, index={self.index}, '
                f'text={self.text}>')


Base.metadata.create_all(engine)
