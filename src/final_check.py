import hashlib, os
import pandas as pd
import numpy as np
from generate import random_attr, df_pac
from get_table import IMAGES


def remove_duplicate_images(root: str):
    file_list = list(filter(lambda f: f.split(".")[1] == "png", os.listdir(root)))
    duplicates = []
    hash_keys = dict()
    for index, filename in enumerate(file_list):
        with open(os.path.join(root, filename), "rb") as f:
            filehash = hashlib.md5(f.read()).hexdigest()
        if filehash not in hash_keys:
            hash_keys[filehash] = index
        else:
            duplicates.append((index, hash_keys[filehash]))
    if len(duplicates) > 0:
        print(f"have {len(duplicates)} duplicate images, deleted")
    for index in duplicates:
        os.remove(os.path.join(root, file_list[index[0]]))


def generate_csv() -> pd.DataFrame:
    cols = ["index", "imagehash", "path"] + [i["trait_type"] for i in random_attr()]
    all_data = []
    n = 0
    for root, _, files in os.walk(IMAGES):
        for file in files:
            if os.path.splitext(file)[1] == ".png":
                old_path = os.path.join(root, file)
                imagehash = None
                new_file = str(n) + "-" + "-".join(file.split("-")[1:])
                path = os.path.join(IMAGES, new_file)
                index, *args, extension = new_file.replace(".", "-").split("-")
                os.rename(old_path, path)
                all_data.append([int(index), imagehash, path, *args])
                n += 1
    all_data.sort(key=lambda i: i[0])
    df = pd.DataFrame(all_data, columns=cols).drop(columns=["index"])
    df.to_csv(os.path.join(IMAGES, "attr.csv"), index=False)
    return df


remove_duplicate_images(IMAGES)
RENAME_DF = generate_csv()

if __name__ == "__main__":
    df_pac["actual"] = 0.0
    # show porperty ratio, if not satisfied, delete some or regenerate
    for col in [i["trait_type"] for i in random_attr()]:
        array = RENAME_DF[col]
        uniques, counts = np.unique(array, return_counts=True)
        percentages = dict(zip(uniques, counts / len(array)))
        for k, v in percentages.items():
            df_pac.loc[df_pac.index.get_level_values("value") == k, "actual"] = v

    print(df_pac)
