from sqlalchemy import desc, or_
from typing import List
from database.engine import Session
from database.models import Public, Post


def add_public(id: str, domain: str) -> Public:
    '''Adds public with given id and domain'''
    public = Public(id=id, domain=domain)
    session = Session()
    session.add(public)
    session.commit()
    session.expunge_all()
    session.close()
    return public


def get_public(id: str = None, domain: str = None) -> Public:
    '''Returns public with given id or domain'''
    with Session() as session:
        public = session.query(Public).filter(
            or_(Public.id == id, Public.domain == domain)
        ).one()
    return public


def get_existing_posts(public_id: str) -> List[str]:
    '''Returns id's of existing posts'''
    session = Session()
    post_ids = session.query(Post.id).filter(Post.public_id == public_id).all()
    post_ids = set(map(lambda x: int(x[0]), post_ids))
    return post_ids
