# meme-generator

A basic (yet) system that generates random *abstract* memes from data scraped on VK.

## Project roadmap
* Done
  - Sqlite database for storing posts, pictures and crops
  - Robust VK scraper that runs in parallel
  - OCR for text detection using *easyocr*
  - Mixer that combines crops
* In progress
  - Better image stitching
  - Better filtering crops
  - Wider variety of options to mix memes with
* Planned
  - GUI for scraping, cropping, mixing and picking memes
  - Improve OCR pipeline by using CRAFT + Tesseract trained on custom fonts
  - Make use of text data by embedding and clustering crop texts
  
