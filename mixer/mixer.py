from sqlalchemy.sql.elements import BinaryExpression as Predicate
from sqlalchemy.sql.selectable import Subquery
from sqlalchemy.exc import NoResultFound
from sqlalchemy import func, and_, or_
from PIL.JpegImagePlugin import JpegImageFile as Jpeg
from PIL import Image

from typing import List, Union, Dict, Tuple, Callable
from operator import le, ge, eq, ne
from io import BytesIO
import json

from database.engine import Session
from database.models import Public, Post, Meme, Crop

Operator = Union[le, ge, eq, ne]
Subqueries = Union[Subquery, List[Subquery]]
JsonDict = Dict[str, int]
BaseJpegs, CropJpegs, PositionJsonDicts = List[Jpeg], List[List[Jpeg]], List[List[JsonDict]]


class Mixer:

    def __init__(self):
        self._session = Session()

    def __del__(self):
        self._session.close()

    def _get_image(self, obj: Union[Meme, Crop]) -> Jpeg:
        return Image.open(BytesIO(obj.picture))

    def _get_json(self, json_string: str) -> JsonDict:
        return json.loads(json_string)

    def _count_crops(self, meme: Meme) -> int:
        return self._session.query(Meme)\
                             .join(Crop) \
                             .filter(Meme.post_id == meme.post_id) \
                             .count()

    def _n_pics_filter(self, n_pics: int = 1, op: Operator = eq) -> Subquery:
        return self._session.query(
            Post.public_id,
            Post.id
        ) \
         .join(Meme) \
         .group_by(Meme.post_id) \
         .having(op(func.count(Meme.id), n_pics)) \
         .subquery()

    def _n_crops_filter(self, n_crops: int = 1, op: Operator = eq) -> Subquery:
        return self._session.query(
            Post.public_id,
            Post.id
        ) \
         .join(Meme) \
         .join(Crop) \
         .group_by(Crop.meme_id) \
         .having(op(func.count(Crop.id), n_crops)) \
         .subquery()

    def _get_random_post(
        self,
        public_predicate: Predicate = None,
        post_predicate: Predicate = None,
        meme_predicate: Predicate = None,
        crop_predicate: Predicate = None,
        subquery_filters: Subqueries = []
    ) -> Post:
        # If only one suquery is passed, wrap it in list
        if type(subquery_filters) is Subquery:
            subquery_filters = [subquery_filters]

        # Construct query
        q = self._session.query(Post)
        if public_predicate is not None:
            q = q.join(Public).filter(public_predicate)
        if post_predicate is not None:
            q = q.filter(post_predicate)
        if meme_predicate is not None:
            q = q.join(Meme).filter(meme_predicate)
        if crop_predicate is not None:
            q = q.join(Meme).join(Crop).filter(crop_predicate)
        for subq in subquery_filters:
            q = q.join(
                subq,
                and_(subq.c.public_id == Post.public_id, subq.c.id == Post.id)
            )
        post = q.order_by(func.random()).limit(1).one()
        return post

    def _stack_predicates(
            self,
            predicate: Union[Predicate, None],
            new_predicate: Predicate,
            method: Callable = and_
    ) -> Predicate:
        if predicate is None:
            return new_predicate
        return method(predicate, new_predicate)

    def _get_pics_filters(self, exact_pics, min_pics, max_pics) -> Subqueries:
        pics_filters = []
        if exact_pics is not None:
            pics_filters.append(self._n_pics_filter(n_pics=exact_pics))
        if min_pics is not None:
            pics_filters.append(self._n_pics_filter(n_pics=min_pics, op=ge))
        if max_pics is not None:
            pics_filters.append(self._n_pics_filter(n_pics=max_pics, op=le))
        return pics_filters

    def _get_crops_filters(self, exact_crops, min_crops, max_crops) -> Subqueries:
        crops_filters = []
        if exact_crops is not None:
            crops_filters.append(self._n_crops_filter(n_crops=exact_crops))
        if min_crops is not None:
            crops_filters.append(self._n_crops_filter(n_crops=min_crops, op=ge))
        if max_crops is not None:
            crops_filters.append(self._n_crops_filter(n_crops=max_crops, op=le))
        return crops_filters

    def _get_public_predicate(self, include_publics, exclude_publics) -> Predicate:
        public_predicate = None
        if include_publics is not None:
            public_predicate = self._stack_predicates(
                public_predicate,
                Public.domain.in_(include_publics)
            )
        if exclude_publics is not None:
            public_predicate = self._stack_predicates(
                public_predicate,
                ~Public.domain.in_(exclude_publics)
            )
        return public_predicate

    def _get_post_predicate(
            self, include_posts, exclude_posts, from_date, to_date
    ) -> Predicate:
        post_predicate = None
        if include_posts is not None:
            post_predicate = self._stack_predicates(
                post_predicate,
                Post.id.in_(include_posts)
            )
        if exclude_posts is not None:
            post_predicate = self._stack_predicates(
                post_predicate,
                ~Post.id.in_(exclude_posts)
            )
        if from_date is not None:
            post_predicate = self._stack_predicates(
                post_predicate,
                Post.date >= from_date
            )
        if to_date is not None:
            post_predicate = self._stack_predicates(
                post_predicate,
                Post.date <= to_date
            )
        return post_predicate

    def _get_crop_predicate(self, include_text, exclude_text) -> Predicate:
        crop_predicate = None
        if include_text is not None:
            if type(include_text) is str:
                include_text = [include_text]
            for text in include_text:
                crop_predicate = self._stack_predicates(
                    crop_predicate,
                    Crop.text.like(text)
                )
        if exclude_text is not None:
            if type(exclude_text) is str:
                exclude_text = [exclude_text]
            for text in exclude_text:
                crop_predicate = self._stack_predicates(
                    crop_predicate,
                    ~Crop.text.like(text)
                )
        return crop_predicate

    def _resize(self, to_resize: Jpeg, size: Tuple[int, int]) -> Tuple[Jpeg, float, float]:
        w, h = to_resize.size
        # If horizontal image is stretched mostly vertically,
        # limit horizontal shrink
        w_ratio, h_ratio = size[0] / w, size[1] / h
        new_w, new_h = size
        if w_ratio > 2 and h_ratio < 1:
            new_w *= 2
            new_h *= 0.5
            resized = to_resize.resize((min(int(new_w), size[0]), max(int(new_h), size[1])), Image.ANTIALIAS)
            return resized, new_w, new_h
        # If image is shrinked too much, limit shrinkage
        if w_ratio < 0.5 or h_ratio < 0.5:
            new_w *= 0.5
            new_h *= 0.5
            resized = to_resize.resize((max(int(new_w), size[0]), max(int(new_h), size[1])), Image.ANTIALIAS)
            return resized, new_w, new_h
        resized = to_resize.resize(size, Image.ANTIALIAS)
        return resized, new_w, new_h

    def random_mix(
            self,
            include_publics: List[str] = None,
            exclude_publics: List[str] = None,
            include_posts: List[str] = None,
            exclude_posts: List[str] = None,
            from_date: str = None,
            to_date: str = None,
            include_text: Union[str, List[str]] = None,
            exclude_text: Union[str, List[str]] = None,
            exact_pics: int = None,
            min_pics: int = None,
            max_pics: int = None,
            exact_crops: int = None,
            min_crops: int = None,
            max_crops: int = None
    ) -> Tuple[BaseJpegs, CropJpegs, PositionJsonDicts]:
        '''
        Creates random mix of pictures and location given an exhaustive selection list

        Params:
            include_publics: list of publics to select from
            exclude_publics: list of publics to drop from selection
            include_publics: list of post id's to select from
            exclude_publics: list of post id's to drop from selection
            from_date: limit selection to posts newer than this date
            to_date: limit selection to posts older than this date
            include_text: list of string to include matches using LIKE in crop texts
            exclude_text: list of string to exclude matches using LIKE in crop texts
            exact_pics: exact number of pics in post to look for
            min_pics: minimum number of pics in post to look for
            max_pics: maximum number of pics in post to look for
            exact_crops: exact number of crops in meme to look for
            min_crops: minimum number of crops in meme to look for
            max_crops: maximum number of crops in meme to look for
        Returns:
            bases: list of base pictures in post
            crops: list of crops for each base picture in post
            positions: list of json dicts with positions for each post
        '''
        # Create picture count filter subqueries
        pics_filters = self._get_pics_filters(exact_pics, min_pics, max_pics)
        # Create crop count filter subqueries
        crops_filters = self._get_crops_filters(exact_crops, min_crops, max_crops)
        # Combine filters
        filter_sqs = pics_filters + crops_filters

        # Create public predicate
        public_predicate = self._get_public_predicate(include_publics, exclude_publics)
        # Create post predicate
        post_predicate = self._get_post_predicate(
            include_posts, exclude_posts, from_date, to_date
        )
        # Create crop predicate
        crop_predicate = self._get_crop_predicate(
            include_text, exclude_text
        )

        # Get a random base post with all the pictures
        base_post = self._get_random_post(
            public_predicate=public_predicate,
            post_predicate=post_predicate,
            crop_predicate=crop_predicate,
            subquery_filters=filter_sqs
        )
        # Fetch random crops
        crops = []
        # For each picture in base post
        for i, base_picture in enumerate(base_post.pictures):
            picture_crops = []
            # and for each crop in picture
            for j, crop in enumerate(base_picture.crops):
                # Sample a random post that is:
                # - not from base post
                # - from/not from certain public
                # - has the same number of pictures in post as base post
                # - has the same number of crops as the current picture
                base_post_predicate = self._stack_predicates(
                    post_predicate,
                    Post.id != base_post.id
                )
                base_crops_count_f = self._n_crops_filter(self._count_crops(base_picture))
                try:
                    sample = self._get_random_post(
                        public_predicate=public_predicate,
                        post_predicate=base_post_predicate,
                        crop_predicate=crop_predicate,
                        subquery_filters=filter_sqs + [base_crops_count_f]
                    )
                except NoResultFound:
                    # If none posts can be found, filter on number of pictures is dropped
                    sample = self._get_random_post(
                        public_predicate=public_predicate,
                        post_predicate=base_post_predicate,
                        crop_predicate=crop_predicate,
                        subquery_filters=crops_filters + [base_crops_count_f]
                    )
                # Append j'th crop from j'th sample
                crop = sample.pictures[min(i, len(sample.pictures)) - 1].crops[j]
                picture_crops.append(self._get_image(crop))
            # Save crop
            crops.append(picture_crops)

        # Load base images and convert json strings with positions
        bases = [self._get_image(m) for m in base_post.pictures]
        positions = [[self._get_json(c.position) for c in m.crops]
                     for m in base_post.pictures]
        return bases, crops, positions

    def compose(
            self,
            bases: BaseJpegs,
            all_crops: CropJpegs,
            all_positions: PositionJsonDicts
    ) -> List[Jpeg]:
        '''
        Composes a post given random bases, crops and positions

        Params:
            bases: list of base pictures in post
            crops: list of crops for each base picture in post
            positions: list of json dicts with positions for each post
        Returns:
            outputs: list of composed pictures
        '''
        outputs = []
        for base, crops, positions in zip(bases, all_crops, all_positions):
            out = base.copy()
            for crop, pos in zip(crops, positions):
                x1, x2 = pos['x']
                y1, y2 = pos['y']
                w, h = x2 - x1, y2 - y1
                resized, w_r, h_r = self._resize(crop, (w, h))
                # resized = resize(crop, (w, h))
                # w_r, h_r = resized.size
                # offset_x, offset_y = max(0, (w_r - w) / 2), max(0, (h_r - h) / 2)
                # new_pos = [
                #  max(min(int(x1 - offset_x), base.size[0]), 0),
                #  max(min(int(y1 - offset_y), base.size[1]), 0),
                #  max(min(int(x2 + offset_x), base.size[0]), 0),
                #  max(min(int(y2 + offset_y), base.size[1]), 0),
                # ]
                # print(f'x1 {x1}, y1 {y1}, x2 {x2}, y2 {y2}')
                # print(f'w, h: {w, h}')
                # print(f'w_r, h_r: {w_r, h_r}')
                # print(f'offset_x, offset_y: {offset_x, offset_y}')
                # print(new_pos[2] - new_pos[0], new_pos[3] - new_pos[1])
                # print('x1 {}, y1 {}, x2 {}, y2 {}'.format(*new_pos))
                # print()
                # out.paste(resized, new_pos)
                out.paste(resized, (x1, y1, x2, y2))
            outputs.append(out)
        return outputs
