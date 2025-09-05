import os
from pathlib import Path

class DataLoader:
    def __init__(self, folder_dir, silent=False):
        self.folder_dir = folder_dir
        self.silent = silent
        self.retrieve = False
        self.exclusions = {
            "admin": [],
            "non_faculty": ["admin"],
            "teaching_faculty": ["admin", "non_faculty"],
            "guest": ["admin", "non_faculty", "teaching_faculty"]
        }

    def log(self, message):
        if not self.silent:
                print(message)
                
    def access_folder(self, assign):
        return [access.lower() for access in assign]

    def load_data(self, role="guest", assign=None):

        uploads_dir = self.folder_dir
        
        folder_path = []

        for folder in os.listdir(uploads_dir):
                    
            if folder.lower() in self.exclusions.get(role.lower(), []):
                self.log(f"Skipping restricted folder: {folder}")
                continue

            folder_dir = os.path.join(uploads_dir, folder)
            if not os.path.isdir(folder_dir):
                continue

            for subfolder in os.listdir(folder_dir):
                if subfolder.lower() in self.access_folder(assign):
                    self.log(f"accessing folder: {subfolder}")
                
                    file_path = os.path.join(folder_dir, subfolder)
                    folder_path.append(file_path)
            
            if folder.lower() == "guest" and not self.retrieve:
                self.log(f"Loading folder: {folder}\n\n")
                folder_path.append(folder_dir)
                retrieve = True
        
        return folder_path
                    