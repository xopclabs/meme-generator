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
