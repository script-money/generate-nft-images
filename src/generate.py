import os
from PIL import Image
import pandas as pd
import numpy as np
import random
from numpy.random import choice
from get_table import files_path
from config import (
    W,
    H,
    PARTS_DICT,
    FOLDERS,
    WEIGHTS,
    IMAGES,
    QUALITY,
    AMOUNT,
    START_ID,
)
from multiprocessing import Pool, cpu_count


def get_ratio(x):
    folder_name = x["folder"].values[0]
    custom_ratio = x["ratio"].values[0]
    folder_ratio = PARTS_DICT[folder_name]
    return custom_ratio * folder_ratio


# modify table data first
df_csv = pd.read_csv("./ratio.csv")
df_group = df_csv.groupby(["folder", "prop", "value"]).apply(get_ratio).to_frame()
df_pac = (
    df_group.groupby(level=["folder", "prop"])
    .apply(lambda x: x / float(x.sum()))
    .rename(columns={0: "ratio"})
)


props = df_csv["prop"].unique()

# get random attributes
def random_attr():
    attributes = []
    select_folder = choice(FOLDERS, p=WEIGHTS)
    for prop in props:
        k = random.random()
        ratio_arr = df_pac.query(
            f"(folder == '{select_folder}') & (prop == '{prop}')"
        ).ratio.values
        cum_arr = np.cumsum(ratio_arr) - k
        first_index = next(x[0] for x in enumerate(cum_arr) if x[1] > 0)
        value = df_pac.loc[(select_folder), (prop), :].index[
            first_index
        ]  # in pandas 1.4, loc is not return tuple but single element
        if type(value) is str:
            attributes.append(
                {"value": (select_folder, prop, value), "trait_type": prop}
            )
        else:
            attributes.append({"value": value, "trait_type": prop})
    return attributes


used_attributes = {}
save_folder: str = IMAGES


def generate_func(
    start_index, end_index, start_id=0,
):
    cols = ["path"] + [i["trait_type"] for i in random_attr()]
    df_batch = pd.DataFrame(columns=cols)
    for i in range(start_index, end_index):
        # avoid duplicate
        index = i + start_id
        attributes = random_attr()
        key = hash(str(attributes))
        while key in used_attributes:
            attributes = random_attr()
            key = hash(str(attributes))
        used_attributes[key] = attributes
        # Get the images to be read in the order of overlay
        paths = [
            next(
                path
                for path in files_path
                if attr["trait_type"] in path.split(os.sep)[1]
                and attr["value"][0] in path.split(os.sep)[0]
                and attr["value"][2] in path.split(os.sep)[2]
            )
            for attr in attributes
        ]
        base_img = Image.new("RGB", (W, H), (0, 0, 0))
        for path in paths:
            img = Image.open(path, "r")
            base_img.paste(img, (0, 0), mask=img)
        # save images
        filename = (
            f"{index}-{'-'.join(list(map(lambda i: i['value'][-1] ,attributes)))}.png"
        )
        base_img.save(
            os.path.join(save_folder, filename), format="jpeg", quality=QUALITY,
        )
        # add porpety
        row_dict = {"path": os.path.join(save_folder, filename)} | {
            i["trait_type"]: i["value"][-1] for i in attributes
        }
        new_row_df = pd.DataFrame.from_dict(row_dict, orient="index").T
        df_batch = pd.concat([df_batch, new_row_df], ignore_index=True,)
    return df_batch


def generate_images(
    df_csv: pd.DataFrame, amount: int, save_folder: str = "./images", start_id: int = 0,
) -> pd.DataFrame:
    prop_count_df = df_csv.groupby(["folder", "prop"]).count()
    sum_count = 0
    for _folder in FOLDERS:
        folder_df = prop_count_df.query(f"folder == '{_folder}'")["ratio"]
        max_count = folder_df.values.cumprod()[-1]
        sum_count += max_count
    assert (
        amount <= sum_count
    ), "Generate too much, there will be duplicate generation, should increase the number of material or reduce the total amount"
    assert (
        np.min(df_pac["ratio"]) * amount >= 1
    ), "The number generated is too small to reflect the minimum probability and the total should be increased"
    assert (
        len(list(filter(lambda f: f.split(".")[1] == "png", os.listdir(save_folder))))
        == 0
    ), f"{save_folder} folder is not empty, backup the original data and tables first"

    processes = cpu_count() - 1
    pool = Pool(processes=processes)
    start_end_indexs = list(
        map(
            lambda x: (
                x * amount // processes,
                (x + 1) * amount // processes,
                start_id,
            ),
            range(processes),
        )
    )

    df_attr = pool.starmap(generate_func, start_end_indexs)
    pd.concat(df_attr, ignore_index=True).to_csv(
        os.path.join(save_folder, "attr.csv"), index=False
    )
    return df_attr


if __name__ == "__main__":
    print(f"generating... check images in {save_folder} folder")
    print(f"quality is {QUALITY}")
    print("PS: you can press Ctrl+C to stop the process")
    generate_images(df_csv, AMOUNT, start_id=START_ID)
    print(f"generate images in {save_folder} folder success")
