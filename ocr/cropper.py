import easyocr
import numpy as np
from PIL import Image
from PIL.JpegImagePlugin import JpegImageFile as Jpeg
from sqlalchemy import func
import json
from io import BytesIO
from typing import Tuple, List, Dict, Union
from database.models import Post, Meme, Crop
from database.engine import Session


Bounds = List[Tuple[List[int], str]]
BboxList = List[Dict[str, List[int]]]


class Cropper:

    def __init__(self, session: Session = None):
        self._session = session if session is not None else Session()
        self._uncropped = self._get_uncropped_memes()
        self.reader = easyocr.Reader(['ru', 'en'])

    def _get_image(self, meme: Meme) -> Jpeg:
        return Image.open(BytesIO(meme.picture))

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

    def _delete_post(self, post_id: str) -> None:
        self._session.query(Post).filter(Post.id == post_id).delete()
        self._session.commit()

    def _delete_crop(self, crop: Crop) -> None:
        self._session.delete(crop)
        self._session.commit()

    def _filter_bounds(self, bounds: List[Bounds]) -> None:
        filters = ['comicbook', 'wowlol']
        for f in filters:
            bounds = list(filter(lambda x: f not in x[1], bounds))
        return bounds

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

    def process_meme(self, meme: Meme) -> None:
        img = self._get_image(meme)
        # Feed img into ocr
        bounds = self.reader.readtext(
            img, paragraph=True, y_ths=0.25
        )
        # If meme doesn't contain any text (or contain too much), delete post
        if len(bounds) == 0 or len(bounds) > 10:
            self._delete_post(meme.post_id)
            return
        # Filter out watermarks, etc
        bounds = self._filter_bounds(bounds)
        # Translate bbox from rectangle coords to x,y min-max
        bounds = self._translate_bounds(bounds, img.size)
        # Get crop images
        crop_imgs = self._crop(img, bounds)
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

    def _get_uncropped_memes(self) -> List[Meme]:
        memes = self._session.query(Meme).join(Crop, isouter=True) \
                                         .group_by(Meme.id) \
                                         .having(func.count(Crop.id) == 0) \
                                         .all()
        return memes

    def crop(self) -> None:
        memes = self._get_uncropped_memes()
        for i, meme in enumerate(memes):
            print(f'[{i}/{len(memes)}]: {meme}')
            try:
                self.process_meme(meme)
            except KeyboardInterrupt:
                raise
            except:
                print('Error!')
