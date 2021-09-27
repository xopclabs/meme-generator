# meme-generator

A basic (yet) system that generates random *abstract* memes from data scraped on VK.

<p float="left">
  <img src="/pics/moral.jpg" width="300" /> 
  <img src="/pics/bro.jpg" width="300" />
  <img src="/pics/good_job.jpg" width="300" />
</p>

## Usage

Install requirements
 ``` shell
pip install -r requirements.txt
```
For scraping to work, one should set VKAPI_TOKEN environment variable
``` shell
export VKAPI_TOKEN=%your_token_here%
```
Below is an example of scraping, cropping and generating a new meme
``` python
from scraper.parallelscraper import ParallelScraper
from ocr.cropper import Cropper
from database.utils import add_public
from database.models import *


# Add a new public to the database (parameters are domain name and str id)
add_public(id='-95648824', domain='memy_pro_kotow')

# Create a plan (domain name: number of posts to scan through)
plan = {
  'memy_pro_kotow': 500,
  # add more publics
}

# Scrape data and save it to the database according to plan
scraper = ParallelScraper()
scraper.scrape(plan)

# Crop uncropped data in the database
cropper = Cropper()
cropper.crop()

# Create new Mixer instance
mixer = Mixer()
# Create a random mix 
#   from 'memy_pro_kotow' 
#   with exactly 1 picture in post
#   with number of crops limited to 2
# (for more customization, refer to this method's docstring)
base_post, crops = mixer.random_mix(
    include_publics=['memy_pro_kotow'],
    exact_pics=1,
    max_crops=2
)
# Compose a new picture from a random mix
memes = mixer.compose(base_post, crops)
# Save results to the database and to a file
mixer.save_to_database(base_post, crops, memes)
mixer.save_to_file(memes, 'test.jpg')
```

## Project roadmap
- [x] Sqlite database for storing posts, pictures, crops and generated memes
- [x] Robust VK scraper that runs in parallel
- [x] OCR for text detection using **easyocr**
- [x] Mixer that combines crops
- [ ] [In progress] Better image stitching
- [ ] [In progress] Better filtering crops
- [ ] [In progress] Wider variety of options to mix memes with
- [ ] GUI for scraping, cropping, mixing and picking memes
- [ ] Improve OCR pipeline by using **CRAFT + Tesseract** trained on custom fonts
- [ ] Make use of text data by embedding and clustering crop texts
  
