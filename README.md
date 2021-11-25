# Generate images

## 安装

推荐用 [miniconda](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/) 来进行环境运行管理，安装完 miniconda 后，运行下面指令生成环境并运行

1. `conda create --name generate python=3.9 pillow pandas requests jupyterlab`
2. `conda activate generate`
3. `pip install python-dotenv` and `pip install py-cid`
4. 运行`python src/get_table.py`，会生成一个叫 ratio.csv 的表格，对里面的内容进行修改
5. 运行`python src/generate.py`，生成图片
6. (可省略) `python src/final_check.py`，删除重复并查看当前的概率分布，可以再做调整。
7. `python src/upload.py` 上传数据到 ipfs

## 特性

- [x] 生成模版: 读取 parts 文件夹，读取里面的文件，检验格式和尺寸，生成一个 csv

- [x] 生成图片: 填写读取 csv 里面的概率，生成图片

- [x] 重命名图片: 支持删除部分生成的图片，并重命名

- [x] 上传图片: 上传图片和 metadata 到 ipfs，并生成 tokenURL 的 hash
