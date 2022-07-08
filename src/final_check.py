import hashlib, os
import pandas as pd
import numpy as np
from generate import random_attr, df_pac
from config import IMAGES, START_ID, CHECK_DUPLICATE_TRAITS_INDEX, SHUFFLE


def remove_duplicate_by_traits(
    root: str, trait_col_index: list = CHECK_DUPLICATE_TRAITS_INDEX
):
    file_list = list(filter(lambda f: f.split(".")[1] == "png", os.listdir(root)))
    duplicates = []
    hash_keys = dict()
    for index, filename in enumerate(file_list):
        if len(trait_col_index) == 0:
            trait_col_index = [i + 1 for i in range(len(df_pac.index.levels[1]))]
        try:
            unique_traits_list = [filename.split("-")[i] for i in trait_col_index]
        except:
            print(f"{filename} is not valid")
            print(f"{trait_col_index} is not valid")
            break
        unique_traits = "-".join(unique_traits_list)
        traits_hash = hashlib.sha1(unique_traits.encode("utf-8")).hexdigest()
        if traits_hash not in hash_keys:
            hash_keys[traits_hash] = index
        else:
            duplicates.append((index, hash_keys[traits_hash]))
    if len(duplicates) > 0:
        print(f"have {len(duplicates)} duplicate images by traits, deleted")
    else:
        print("no duplicate images by traits")
    for index in duplicates:
        os.remove(os.path.join(root, file_list[index[0]]))


def generate_csv(sort=True) -> pd.DataFrame:
    cols = ["index", "path"] + [i["trait_type"] for i in random_attr()]
    all_data = []
    n = START_ID
    for root, _, files in os.walk(IMAGES):
        files.sort(
            key=lambda a: int(a.split("-")[0])
            if a != "attr.csv" and a != ".DS_Store"
            else 0
        )
        for file in files:
            if os.path.splitext(file)[1] == ".png":
                old_path = os.path.join(root, file)
                new_file = str(n) + "-" + "-".join(file.split("-")[1:])
                path = os.path.join(IMAGES, new_file)
                index, *args, _ = new_file.replace(".", "-").split("-")
                os.rename(old_path, path)
                all_data.append([int(index), path, *args])
                n += 1
    if sort:
        all_data.sort(key=lambda i: i[0])
    else:
        print("images not sort")
    df = pd.DataFrame(all_data, columns=cols).drop(columns=["index"])
    df.to_csv(os.path.join(IMAGES, "attr.csv"), index=False)
    return df


remove_duplicate_by_traits(IMAGES)
RENAME_DF = generate_csv(SHUFFLE)


if __name__ == "__main__":
    df_pac["actual"] = 0.0
    # show porperty ratio, if not satisfied, delete some or regenerate
    for col in [i["trait_type"] for i in random_attr()]:
        array = RENAME_DF[col]
        uniques, counts = np.unique(array, return_counts=True)
        percentages = dict(zip(uniques, counts / len(array)))
        prop_df = pd.DataFrame.from_dict(percentages, orient="index", columns=[col])
        with pd.option_context(
            "display.max_rows",
            None,
            "display.max_columns",
            None,
            "display.precision",
            4,
            "display.float_format",
            "{:.2%}".format,
        ):
            print(prop_df)
        print("\n")
