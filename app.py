import os
import csv

import os
import csv

# CSV file containing image names in column A
csv_file = "data/input1.csv"
# Directory where images are stored
image_directory = "data/images"
# New CSV file with available images
output_csv = "data/output.csv"
available_images = set(os.listdir(image_directory))
with open(csv_file, mode="r", newline="") as infile, open(output_csv, mode="w", newline="") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)

    # Read and write header
    header = next(reader)
    header.append("image")
    writer.writerow(header)

    for row in reader:
        image_name = row[0].strip()
        print(image_name)
        image_name = f'{image_name}.jpg'
        print(image_name)
        if image_name in available_images:
            row.append(image_name)
        else:
            row.append("")
        writer.writerow(row)

print(f"Processed CSV file saved as '{output_csv}'.")
print(f"Processed CSV file saved as '{output_csv}'.")