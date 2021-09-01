# Generate images

## 安装

推荐用 [miniconda](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/) 来进行环境运行管理，安装完miniconda后，运行下面指令生成环境并运行

1. `conda create --name generate python=3.9 pillow pandas requests jupyterlab`
2. `conda activate generate`
3. `pip install python-dotenv`
4. `cd generate-nft-images`
5. `jupyter lab .` 然后打开research.ipynb运行即可 (或者用 vscode 运行 `research.ipynb`)

## 特性

- [x] 生成模版: 读取 parts 文件夹，读取里面的文件，检验格式和尺寸，生成一个 csv

- [x] 生成图片: 填写读取 csv 里面的概率，生成图片

- [x] 重命名图片: 支持删除部分生成的图片，并重命名

- [x] 上传图片: 上传图片和 metadata 到 ipfs，并生成 tokenURL 的 hash
