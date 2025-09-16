import os, logging, re, shutil
import py7zr, rich, zipfile

from rich.text import Text
import rich.prompt as prompt

logger = logging.getLogger(__name__)

def unzip_all(path):
    # Iterate over all directories and files in the given path
    for root, dirs, files in os.walk(path):
        # Filter the files that have the ".zip" or ".7z" extensions
        archive_files = [f for f in files if f.endswith((".zip", ".7z"))]
        
        # Unzip each archive file
        for file in archive_files:
            file_path = os.path.join(root, file)
            # Create a new directory name based on the archive file name (remove extension)
            dir_name = os.path.splitext(file)[0]
            dir_path = os.path.join(root, dir_name)

            # Check if the directory exists, if not create it
            try:
                if os.path.exists(dir_path):
                    shutil.rmtree(dir_path)
                os.makedirs(dir_path)
            except Exception as e:
                logger.warning(e)
                continue
            
            # Handle .7z files
            if file.endswith(".7z"):
                with py7zr.SevenZipFile(file_path, 'r') as archive_ref:
                    archive_ref.extractall(path=dir_path)
                    rich.print(f"Unzipped {file_path} to [green]{dir_path}[/green]")
            # Handle .zip files
            elif file.endswith(".zip"):
                with zipfile.ZipFile(file_path, 'r') as archive_ref:
                    archive_ref.extractall(path=dir_path)
                    rich.print(f"Unzipped {file_path} to [green]{dir_path}[/green]")


def rename_ass_files(path, start_value):
    # Iterate over all directories and files in the given path
    rich.print(f"[orange3]{path}[/orange3]")
    for root, dirs, files in os.walk(path):
        # Filter the files that have the ".ass" extension
        logger.debug(f"\nroot: {root}")
        logger.debug(f"dirs: {dirs}")

        ass_files = [f for f in files if f.endswith(".ass")]
        value = start_value
        previous = ""
        # Rename each .ass file
        for file in ass_files:
            if re.search(r'(\d+)_(\d)', file):
                choice = prompt.Prompt.ask(Text(f"[orange3 bold]{file}[/orange3 bold] seems to be a recap episode, skip it ?"), choices=["y", "n", ""])

                if not choice.lower().strip() == 'n':
                    continue

            if previous[:-10] == file[:-10]:
                value -=1
            
            old_file_path = os.path.join(root, file)
            # Create a new file name based on the start_value
            new_file_name = f"{value}.ass"
            new_file_path = os.path.join(root, new_file_name)


            # Rename the file
            if os.path.exists(new_file_path):
                os.remove(new_file_path)
            os.rename(old_file_path, new_file_path)
            rich.print(f"Renamed [red]{old_file_path}[/red] to [green]{new_file_path}[/green]")
            
            # Increment the start_value after renaming each file
            previous = file
            value += 1


def move_extracted_folders(extracted_root, destination):
    # Iterate over all directories in the extracted_root
    for root, dirs, files in os.walk(extracted_root):
        for dir_name in dirs:
            if dir_name == "to-translate":
                continue

            src_dir_path = os.path.join(root, dir_name)
            dest_dir_path = os.path.join(destination, dir_name)
            
            logger.rich(src_dir_path)
            logger.rich(dest_dir_path)

            # Move the directory to the destination
            shutil.copytree(src_dir_path, dest_dir_path, dirs_exist_ok=True)

            try:
                shutil.rmtree(src_dir_path)
            except:
                logger.warning(f"Couldn't remove {src_dir_path}")

            rich.print(f"Moved [blue]{src_dir_path}[/blue] to [green]{dest_dir_path}[/green]")
        
        # Stop walking deeper, we only want the first level of directories
        break

def ask_for_unzip():
    # Ask for the base directory path
    base_path = input("Enter the base directory path to search for .zip or .7z file: ")
    
    try:
        if not os.path.exists(base_path):
            raise FileNotFoundError(f"Directory not found: {base_path}")
    except FileNotFoundError as e:
        logger.warning(e)
        return
    
    try: 
        if os.path.isdir(os.path.join(base_path, "to-translate")):
            rich.print(f"[orange3]:warning: Current {base_path}/to-translate directory will be deleted[/orange3]")
            choice = prompt.Prompt.ask(Text("Do you want to rename old one ?", style="bold"), choices=["y", "n"], default="n")
            if choice.lower().strip() == 'n':
                shutil.rmtree(os.path.join(base_path, "to-translate"))
            else:
                os.rename(os.path.join(base_path, "to-translate"), os.path.join(base_path, "to-translate_old"))
            
        os.makedirs(os.path.join(base_path, "to-translate"))
    except Exception as e:
        logger.warning(e)
        return

    # Iterate through the base path and look for folders containing .zip or .7z files
    for root, dirs, files in os.walk(base_path):
        archive_files = [f for f in files if f.endswith((".zip", ".7z"))]
        # If there are any archive files in the directory
        if archive_files:
            # Ask the user for a starting number specific to the current directory
            rich.print(f"[magenta3]Found archives in directory[/magenta3]: {root}")
            start_value = int(input(f"Enter the starting number for {root}: "))
            # Unzip the files in the current directory
            unzip_all(root)
            # Rename .ass files in the current directory
            rename_ass_files(root, start_value)

            move_extracted_folders(root, os.path.join(base_path, "to-translate"))

    rich.print("[bold]Check that all episode subtitles of language are in the same folder[/bold] (ex: to-translate/[green bold]Language[/green bold]) ")
    rich.print("[bold]and remove French sub folder from it[/bold]")


if __name__ == "__main__":

    def rich_fct(m, l=logging.INFO):
        rich.print(m)

    logger.rich = rich_fct
    ask_for_unzip()
    input("Press Enter...")
