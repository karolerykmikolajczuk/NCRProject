import csv
import math
from tqdm import tqdm

files_list: list[str] = ["ml-10M100K/ratings.dat"]
target_file: list[str] = ["userID,itemID,rating,timestamp"]

for f in tqdm(files_list, desc="Collecting data from text files"):
    with open(f, "r") as fp:
        for line in tqdm(fp, desc="Iterating through each line of file"):
            splitted: list[str] = line.split('::')
            splitted[0] = str(math.floor(float(splitted[0]))-1) # indexing from 0 instead of 1
            splitted[2] = str(math.floor(float(splitted[2]))) # rounding 0.5 to 0
            new_line: str = ",".join(splitted).strip()
            target_file.append(new_line)

with open("output.csv", "w", newline="") as file:
    writer = csv.writer(file)
    for row in tqdm(target_file, desc="Putting data into .csv file"):
        writer.writerow(row.split(","))

