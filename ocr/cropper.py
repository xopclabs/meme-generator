import easyocr
import numpy as np
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile as Jpeg
from sqlalchemy import func
import json
from io import BytesIO
from typing import Tuple, List, Dict
from database.models import Post, Meme, Crop
from database.engine import Session


Bounds = List[Tuple[List[int], str]]
BboxList = List[Dict[str, List[int]]]


class Cropper:

    def __init__(self, session: Session = None):
        self._session = session if session is not None else Session()
        self.reader = easyocr.Reader(['ru', 'en'])

    def _get_uncropped_memes(self) -> List[Meme]:
        memes = self._session.query(Meme).join(Crop, isouter=True) \
                                         .group_by(Meme.id) \
                                         .having(func.count(Crop.id) == 0) \
                                         .all()
        return memes

    def _get_image(self, meme: Meme) -> Jpeg:
        return Image.open(BytesIO(meme.picture))

    def _delete_post(self, post_id: str) -> None:
        post = self._session.query(Post).filter(Post.id == post_id).one()
        self._session.delete(post)
        self._session.commit()

    def _translate_bounds(self, bounds: Bounds, shape: Tuple[int, int]) -> Bounds:
        def translator(bound):
            b = bound[0]
            xmin, xmax = [max(min(x, shape[0]), 0) for x in (b[0][0], b[1][0])]
            ymin, ymax = [max(min(y, shape[1]), 0) for y in (b[0][1], b[-1][1])]
            return [[[xmin, xmax], [ymin, ymax]], bound[1]]
        return list(map(translator, bounds))

    def _crop(self, img: Jpeg, bounds: Bounds) -> List[Jpeg]:
        img = np.asarray(img)
        crops = []
        for b in bounds:
            bbox = b[0]
            xmin, xmax = bbox[0]
            ymin, ymax = bbox[1]
            crop = img[ymin:ymax, xmin:xmax]
            crop = Image.fromarray(crop)
            crops.append(crop)
        return crops

    def _filter_bounds(self, bounds: List[Bounds]) -> None:
        filters = ['comicbook', 'wowlol', 'Класс!']
        for f in filters:
            bounds = filter(lambda x: f not in x[1], bounds)
        bounds = filter(lambda x: len(x[1]) > 1, bounds)
        bounds = filter(lambda x: x[0] != '@', bounds)
        return list(bounds)

    def _filter_crops_by_size(self, crops: List[Jpeg], image: Jpeg) -> List[Jpeg]:
        def relative_size(c: Jpeg) -> bool:
            area = c.size[0] * c.size[1]
            ratio = area / image_area
            if ratio < 0.0005 or ratio > 0.6:
                return False
            return True

        def absolute_size(c: Jpeg) -> bool:
            w, h = c.size
            if w < 20 or h < 20:
                return False
            return True

        image_area = image.size[0] * image.size[1]
        crops = filter(relative_size, crops)
        crops = filter(absolute_size, crops)
        return list(crops)

    def _image_to_bytes(self, image: Jpeg) -> bytes:
        buf = BytesIO()
        image.save(buf, format='JPEG')
        return buf.getvalue()

    def _update_meme_crops_location(self, meme: Meme, bboxes: str) -> None:
        self._session.query(Meme).filter(Meme.id == meme.id) \
                           .update({Meme.crop_positions: bboxes})
        self._session.commit()

    def _save_crops(self, crops: List[Crop]) -> None:
        self._session.add_all(crops)
        self._session.commit()

    def crop_meme(self, meme: Meme) -> None:
        # Check if meme wasn't deleted
        if not self._session.query(Meme).filter(Meme.id == meme.id).all():
            return
        # Load picture
        img = self._get_image(meme)
        # Feed img into ocr
        try:
            bounds = self.reader.readtext(
                img, paragraph=True, x_ths=2, y_ths=0.25
            )
        except RuntimeError as e:
            print(e)
            self._delete_post(meme.post_id)
            return

        # Filter out watermarks, etc
        bounds = self._filter_bounds(bounds)
        # If meme doesn't contain any text (or contain too much), delete post
        if len(bounds) not in range(1, 7):
            self._delete_post(meme.post_id)
            return
        # Translate bbox from rectangle coords to x,y min-max
        bounds = self._translate_bounds(bounds, img.size)
        # Get crop images
        crop_imgs = self._crop(img, bounds)
        # Filter crops by size and delete post if nothing left
        crop_imgs = self. _filter_crops_by_size(crop_imgs, img)
        if not crop_imgs:
            self._delete_post(meme.post_id)
            return
        # Create Crop objects and gather all crops information
        crops = []
        bboxes = []
        for i, (crop_img, (bbox, text)) in enumerate(zip(crop_imgs, bounds)):
            crop = Crop(
                meme_id=meme.id,
                picture=self._image_to_bytes(crop_img),
                index=i,
                text=text
            )
            crops.append(crop)
            bboxes.append(bbox)
        # Add crop locations to meme
        bboxes = json.dumps([dict(zip(['x', 'y'], b)) for b in bboxes])
        self._update_meme_crops_location(meme, bboxes)
        # Add crops
        self._save_crops(crops)

    def crop(self) -> None:
        memes = self._get_uncropped_memes()
        for i, meme in enumerate(memes):
            print((f'[{i + 1}/{len(memes)}] public_id: {meme.public_id[1:]}, '
                   f'post_id: {meme.post_id}'))
            self.crop_meme(meme)
