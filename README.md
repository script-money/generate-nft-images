# Generate NFT images

## install

1. install dependencies `pip install -r requirements.txt`
2. modify configs in `src/config.py`
3. run `python src/get_table.py`, this will generate a table called ratio.csv, you can modify probability of feature occurrence in the ratio column or add rules in `rules.csv` to limit the coexistence or mutual exclusion.
4. run `python src/generate.py` to generate images.
5. `python src/final_check.py`, remove the duplicates and view the current probability distribution, which can be adjusted again.
6. (can skip) `python src/upload_mystery_box.py` push mystery box metadata to IPFS
7. `python src/upload.py` push data to IPFS
8.  (if need) `python src/fresh_metadata.py` to refresh opensea metadata to show new images

## features

- [x] Generate a template: reads the parts folders, reads the files inside, checks the format and size, and generates a csv

- [x] Generate image: Fill in the probability of reading the csv and generate the image

- [x] Rename images: Support to delete some of the generated images and rename others

- [x] Upload image: upload image and metadata to ipfs and generate hash of tokenURL

- [x] Multiple folder support: Rare features can be placed in separate folders for generate

- [x] Upload mystery box data: generate mystery box metadata and upload

- [x] Generate images by attr.csv, it's use for update old images

- [x] Refresh metadata: query ipfs and opensea api to refresh metadata, need opensea apikey

- [x] Using rule files to limit the coexistence or mutual exclusion of generated elements
