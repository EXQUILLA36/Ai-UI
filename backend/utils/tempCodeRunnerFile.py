from pathlib import Path
from Restrict import DataLoader

def main():
    folder_path = db_dir = Path(__name__).resolve().parent.parent / 'database' / 'chroma_store'
    role = "teaching_faculty" # change the role base on user authority
    assign = ["Department_CCS", "Department_CHTM"]

    loader = DataLoader(folder_path, silent=False)
    file_path = loader.load_data(role=role, assign=assign)
    
    for i in file_path:
        print(f"{i}\n")

if __name__ == "__main__":
    main()
