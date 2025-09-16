import datetime, logging
import sys
import os
import subprocess
import rich

logger = logging.getLogger(__name__)


LG = {
    "french" : "fr",
    "english" : "en",
    "spanish" : "es",
    "german" : "de",
    "italian" : "it",
    "portuguese" : "pt",
    "russian" : "ru",
    "japanese" : "ja",
    "chinese" : "zh",
    "korean" : "ko",
    "arabic" : "ar",
    "polish" : "pl",
    "dutch" : "nl",
}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

MKV_MERGE = resource_path("./assets/mkvmerge.exe")

def separator():
    return f"\n[green]{'=' * 56}{str(datetime.datetime.now().strftime('%H:%M:%S'))}{'=' * 56}[/]"

            
def multiplexMLK(films_subs_path: str, mkv_path: str):
    subsFolders = os.listdir(films_subs_path)
    folder_files = [list(filter(lambda x: x.endswith(".ass"), os.listdir(os.path.join(films_subs_path, subsFolder)))) for subsFolder in subsFolders]
    folder_files = list(filter(lambda x: len(x) > 0, folder_files))
    
    films = list(filter(lambda x: x.endswith(".mkv"), os.listdir(mkv_path)))
    logger.rich(films)
    c = 0
    for files in zip(*folder_files):
        logger.rich(separator())
        logger.rich("Multiplex of: \n")
        try:
            logger.rich(f"[green]Film: [/]" + films[c])
        except:
            pass
        c += 1
        for index, lang in enumerate(os.listdir(films_subs_path)):
            logger.rich(f"[orange3]{lang}[/]: {files[index]}")


    rep = input("\nIs that right ? [Y/N] ").lower()
    while (rep != "y" and rep != "n"):
        rep = input("Is that right ? [Y/N] ").lower()

    if rep == "n":
        logger.rich("[orange3]Cancel multiplex...[/]")
        return

    print('\n\033[32mStart multiplex...\033[0m')

    for files in zip(*folder_files):
        if not all(".ass" in file for file in files):
            continue

        logger.rich(separator())
        logger.rich("Multiplexing of: \n")
        logger.rich(f"[green]Film: [/]" + films[0])
        output_video = os.path.join(mkv_path, 'Translated Films', films[0])
        
        mkvmerge_command = [
            MKV_MERGE,
            '-o', output_video,
            os.path.join(mkv_path, films[0]),
        ]

        for index, file in enumerate(files):
            languageData = (LG[subsFolders[index].strip().lower()], subsFolders[index])

            mkvmerge_command.extend([
                "--language",
                f"0:{languageData[0].strip()}"
            ])

            mkvmerge_command.extend([
                "--track-name",
                f"0:VO - {languageData[1].strip()} [ASS]"
            ])

            mkvmerge_command.extend([
                "--default-track",
                "0:0"
            ])

            subpath = os.path.join(films_subs_path, subsFolders[index], file)
            mkvmerge_command.append(subpath)

        try:
            # Run the mkvmerge command
            subprocess.run(mkvmerge_command, check=True)
            print(f"Subtitles added to {output_video} !")
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

        films.pop(0)

        if len(films) == 0:
            return


def checkIfSameNumberOfFiles(films_subs_path: str, mkv_path: str):
    logger.rich(f"Language Subtitles Folders found:\n{"\n".join(os.listdir(films_subs_path))}")

    films = list(filter(lambda x: x.endswith(".mkv"), os.listdir(mkv_path)))
    for folder in os.listdir(films_subs_path):
        files = list(filter(lambda x: x.endswith(".ass"), os.path.join(films_subs_path, folder)))
        if len(files) == 0:
            continue
        if len(files) != len(films):
            logger.rich("Folder don't have same number of files (mkv vs ass)", logging.ERROR)
            logger.rich(f"{films_subs_path}: {len(films)} mkv files")
            logger.rich(f"{os.path.join(films_subs_path, folder)}: {len(files)} ass files")
            input("Enter quit...")
            sys.exit(0)
    

def ask_for_mkv_merge():
    films_subs_path = input("Enter the path to films translated subtitles folder: ").strip()
    while True:
        if not os.path.exists(films_subs_path):
            print("File path does not exist")
        else:
            break
        films_subs_path = input("Enter the path to films translated subtitles folder: ").strip()

    mkv_path = input("Enter the path to the MKV video folder: ").strip()
    while True:
        if not os.path.exists(mkv_path):
            print("MKV file path does not exist")
        elif not any(file.endswith(".mkv") for file in os.listdir(mkv_path)):
            print("No .mkv files found in the directory")
        else:
            break
        mkv_path = input("Enter the path to the MKV folder: ").strip()

    print(f"Subtitles path: {films_subs_path}")
    print(f"MKV path: {mkv_path}")

    checkIfSameNumberOfFiles(films_subs_path, mkv_path)
    
    try:
        os.makedirs(os.path.join(mkv_path, "Translated Films"))
    except:
        logger.rich(f"Folder {os.path.join(mkv_path, "Translated Films")} already exists, fils will be overwritten", logging.WARNING)
    
    multiplexMLK(films_subs_path, mkv_path)

if __name__ == '__main__':

    def rich_fct(e, l=logging.INFO):
        logger.log(l, e)
    
    logger.rich = rich_fct

    checkIfSameNumberOfFiles()
    multiplexMLK()

    # Replace 'your_video.mkv' with the name of your MKV video file
    