# Generate NFT images

## install

It is recommended to use [miniconda](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/) to manage the environment. After installing miniconda, run the following command to generate the environment and run it

1. `conda create --name generate python=3.9 pillow pandas requests jupyterlab`
2. `conda activate generate`
3. `pip install python-dotenv py-cid`
4. put your images parts folder at project root. Then modify config in `get_table.py` 
5. run `python src/get_table.py`, this will generate a table called ratio.csv, you can modify probability of feature occurrence in the ratio column.
6. (can skip) `python src/final_check.py`, remove the duplicates and view the current probability distribution, which can be adjusted again.
7. `python src/upload.py` push data to IPFS via infura

## features

- [x] Generate a template: reads the parts folders, reads the files inside, checks the format and size, and generates a csv

- [x] Generate image: Fill in the probability of reading the csv and generate the image

- [x] Rename images: Support to delete some of the generated images and rename others

- [x] Upload image: upload image and metadata to ipfs and generate hash of tokenURL

- [x] Multiple folder support: Rare features can be placed in separate folders for generate
