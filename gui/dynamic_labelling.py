import pandas as pd
import os
from statistics import median
import ui_config

# Use saved output from flex_collect.py
csv_file_path = ui_config.FilePaths.flex_collect_csv_path.value  # Change this to the path of the csv file

filename = os.path.basename(csv_file_path)
timestamp = filename.split('_')[2].split('.')[0]

df = pd.read_csv(csv_file_path)
df = df.dropna(subset=['Sensor 2', 'Sensor 4'])
df['Sensor4_2_diff'] = df['Sensor 4'] - df['Sensor 2']

df_ne = df[df['Posture'].str.startswith('ne')]
df_pc = df[df['Posture'].str.startswith('pc')]

median_values = df.groupby('Posture')['Sensor4_2_diff'].median()

global flex_median_g, ne_median_g, pc_median_g

ne_postures = ['ne65', 'ne70', 'ne80']
ne_values = [median_values[posture] for posture in ne_postures]
ne_median_g = median(ne_values)

pc_postures = ['pc65', 'pc70', 'pc80']
pc_values = [median_values[posture] for posture in pc_postures]
pc_median_g = median(pc_values)

df['Sensor4_2_diff'] = df['Sensor 4'] - df['Sensor 2']

def print_posture_values(grouped, postures, label):
    for posture in postures:
        key = f'{label}{posture}'
        if key in grouped.groups:
            print(f"All Sensor4_2_diff values for {key}:")
            print(grouped.get_group(key)['Sensor4_2_diff'].values)
        else:
            print(f"No data for posture {key}.")

postures = ['65', '70', '80']
grouped = df.groupby('Posture')

print_posture_values(grouped, postures, 'pc')
print_posture_values(grouped, postures, 'ne')

result = pc_median_g - ne_median_g
print(f"Flex{postures} = {result}")

flex_values = [median_values[f'pc{posture}'] - median_values[f'ne{posture}'] for posture in postures]
flex_median_g = pc_median_g - ne_median_g

print(f"\nPC values: {pc_values}")
print(f"Median of pc65, pc70, pc80 = {pc_median_g}")

print(f"\nNE values: {ne_values}")
print(f"Median of ne65, ne70, ne80 = {ne_median_g}")

print(f"\nFlex values: {flex_values}")
print(f"flex_median_g = {flex_median_g}")

def use_flex_median():
    global flex_median_g
    if flex_median_g is not None:
        print(f"Using global median value: {flex_median_g}")
    else:
        print("Global median value is not set.")

