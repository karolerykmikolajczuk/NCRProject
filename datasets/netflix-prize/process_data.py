import csv
import re
from datetime import datetime
from tqdm import tqdm

files_list: list[str] = [
    "netflix-prize-data/combined_data_1.txt",
    "netflix-prize-data/combined_data_2.txt",
    "netflix-prize-data/combined_data_3.txt",
    "netflix-prize-data/combined_data_4.txt"
]

target_file: list = ["userID,itemID,rating,timestamp\n"]

for f in tqdm(files_list, desc="Collecting data from text files"):
    with open(f, "r") as fp:
        for line in fp:
            match = re.match(r"(\d+):", line)
            if match:
                itemID: str = match.group(1)
            else:
                line_splitted: list = line.split(',')
                # also indexing from 0, so we have to decrease userID by 1
                new_line: str = ",".join([str(int(line_splitted[0])-1), itemID, line_splitted[1], str(int(datetime.strptime(line_splitted[2].strip(), "%Y-%m-%d").timestamp()))]) + "\n"
                #print(new_line, end="")
                target_file.append(new_line)

with open("output.csv", "w", newline="") as file:
    writer = csv.writer(file)
    for row in tqdm(target_file, desc="Putting data into .csv file"):
        writer.writerow(row.split(","))

