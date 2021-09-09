from sqlalchemy import or_, desc
from database.models import Session, Public, Post


def add_public(id: str, domain: str) -> Public:
    '''Adds public with given id and domain'''
    public = Public(id=id, domain=domain)
    session = Session()
    session.add(public)
    session.commit()
    session.close()
    return public


def get_public(id: str=None, domain: str=None) -> Public:
    '''Returns public with given id or domain'''
    session = Session()
    public = session.query(Public).filter(
        or_(Public.id == id, Public.domain == domain)
    ).one()
    session.close()
    return public


def filter_posts(ids, public_id, limit=100):
    '''Filters out existing post ids from a list'''
    session = Session()
    post_ids = session.query(Post.post_id).filter(Post.public_id == public_id) \
                                  .order_by(desc(Post.date)) \
                                  .limit(limit) \
                                  .all()

    post_ids = set(map(lambda x: int(x[0]), post_ids))
    filtered = list(filter(lambda x: x not in post_ids, ids))
    return filtered
