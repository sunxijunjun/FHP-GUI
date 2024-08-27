import os
import pandas as pd
import glob
from logger import Logger


def integrate_csv_files(folder_path: str, session_id: str):
    """
    Integrates and sorts all CSV files associated with a specific session ID within a given folder.

    Args:
        folder_path (str): The path to the folder containing the CSV files.
        session_id (str): The session ID to filter the CSV files.
    Returns:
        pandas.DataFrame: A DataFrame containing the integrated and sorted data from all matching CSV files.
    """

    file_pattern = os.path.join(folder_path, f"data_*_{session_id}.csv")
    matching_files = glob.glob(file_pattern)
    all_data = []

    for file in matching_files:
        df = pd.read_csv(file)
        if df.shape[0] > 0:
            all_data.append(df)

    integrated_df = pd.concat(all_data, ignore_index=True)
    integrated_df.sort_values(by='timestamp', inplace=True)

    return integrated_df


def get_saved_notes(folder_path: str, session_id: str) -> pd.DataFrame:
    file_name = f'notes_{session_id}_all.csv'
    path = os.path.join(folder_path, file_name)
    print(path)
    return pd.read_csv(path, index_col=False)


def save_integrated_csv(folder_path: str, session_id: str):
    """
    Integrates CSV files for a session and saves the result to a new CSV file.

    Args:
        folder_path (str): Folder of log files
        session_id (str): The session ID to filter the CSV files. The folder path is constructed using this ID.
    """
    integrated_data = integrate_csv_files(folder_path, session_id)
    output_filename = os.path.join(folder_path, f"integrated_data_{session_id}.csv")
    notes = get_saved_notes(folder_path, session_id)
    integrated_data = Logger.post_process_df(df=integrated_data, notes=notes)
    integrated_data = integrated_data.drop_duplicates()
    integrated_data.to_csv(output_filename, index=False)
    print(f"Integrated data saved to: {output_filename}")


if __name__ == "__main__":
    session_id_input = input("Please input the session ID: ")
    save_integrated_csv(folder_path = os.path.join("data", "logs", f"session_{session_id_input}"),
                        session_id = session_id_input)