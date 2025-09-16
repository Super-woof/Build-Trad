import multiprocessing
import os, sys, argparse, logging
import rich
from rich.prompt import Prompt
from rich.logging import RichHandler

from src.interface import Config, FilmInfos
from src.sub_traductor import translate_subs_treaded, translate_subs_single_thread,print_cut_timecodes
from src.config_actions import load_config, generate_config
from src.tools.archive_rename import ask_for_unzip
from src.tools.mkvAddSub import ask_for_mkv_merge
from src.tools.sync_subs import sync_subs
from src.tools.mkvExtract import ask_for_extract
from src.one_piece_helper import one_piece_v2_helper

title = '''
 ____        _   _____              _            _              __     _______ 
/ ___| _   _| |_|_   _| __ __ _  __| |_   _  ___| |_ ___  _ __  \\ \\   / /___ / 
\\___ \\| | | | '_ \\| || '__/ _` |/ _` | | | |/ __| __/ _ \\| '__|  \\ \\ / /  |_ \\ 
 ___) | |_| | |_) | || | | (_| | (_| | |_| | (__| || (_) | |      \\ V /  ___) |
|____/ \\__,_|_.__/|_||_|  \\__,_|\\__,_|\\__,_|\\___|\\__\\___/|_|       \\_/  |____/                    
'''

logger = logging.getLogger(__name__)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler('SubTraductorV3.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Log messages of level DEBUG and above to the file

    # Create rich console handler
    console_handler = RichHandler(rich_tracebacks=True)
    console_handler.setLevel(logging.ERROR)  # Log messages of level ERROR and above to the console

    # Create a formatter for the file handler
    file_formatter = logging.Formatter(
        '%(levelname)-8s | %(message)s | %(funcName)s:%(lineno)d | %(name)s | %(asctime)s',
        datefmt='%H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    def log_rich(self, message, level=logging.INFO):
        rich.print(message) 
        self.log(level, message)

    logging.Logger.rich = log_rich


def show_menu(args):
    options = [
        "Extract ASS/SRT Subtitles from MKV",
        "Extract 7z/zip and Rename Subtitles",
        "Generate Config",
        "Translate",
        "Create MKV Files with translated subtitles",
        "Sync Subs",
        "Help",
        "One Piece V2 - Helper",
        "Quit"
    ]

    logger.rich("Select an option:")
    for i, option in enumerate(options, 0):
        logger.rich(f"[bold]{i}[/bold]) {option}")

    choice = input("\nEnter the number of your choice: ")
    while not (choice.isdigit() and 0 <= int(choice) <= len(options)):
        choice = input("Invalid choice. Enter the number of your choice: ")

    choice = int(choice)
    
    if choice == 0:
        args.mkv_extract = True
        logger.rich("Extraction ASS/SRT Subtitles from MKV...")
    elif choice == 3:
        config_filename = input("Enter the config filename or 'enter' to use default SubTraductorV3.conf: ")
        while not config_filename.strip() == "" and not (os.path.exists(config_filename) or os.path.exists(config_filename+".conf")):
            config_filename = input(f"{config_filename} doesn't exist in current dir, Enter the config filename: ")

        args.config_filename = config_filename if not config_filename.strip() == "" else "SubTraductorV3.conf"
        if not args.config_filename.endswith(".conf"):
            args.config_filename += ".conf"

        logger.rich(f"Translation with config file: [green bold]{args.config_filename}[/]")

        use_multithread = input("Use multithread for translation (faster)? ([y]/n): ")
        if use_multithread.lower() == 'n':
            args.single_thread = True
            logger.rich("Translation will be done in a single thread")
    elif choice == 2:
        config_filename = input("Enter the config filename or 'enter' to use default SubTraductorV3.conf: ")
        if config_filename.isspace():
            config_filename = "SubTraductorV3.conf"
        
        args.generate_config = config_filename if not config_filename.strip() == "" else "SubTraductorV3.conf"
        logger.rich(f"Generation of [green bold]{config_filename}[/] config file")
    elif choice == 1:
        args.extract_rename = True
        logger.rich("Extracting and renaming subtitles from 7z/zip...")
    elif choice == 4:
        args.mkv_create = True
        logger.rich("MKV files will be created with new translated subs")
    elif choice == 5:
        args.sync_sub = True
        logger.rich("Syncing subtitles...")
    elif choice == 6:
        args.help = True
        return
    elif choice == 7:
        logger.rich("One Piece V2 - Helper...")
        config_filename = input("Enter the config filename or 'enter' to use default SubTraductorV3.conf: ")
        while not config_filename.strip() == "" and not (os.path.exists(config_filename) or os.path.exists(config_filename+".conf")):
            config_filename = input(f"{config_filename} doesn't exist in current dir, Enter the config filename: ")

        args.config_filename = config_filename if not config_filename.strip() == "" else "SubTraductorV3.conf"
        if not args.config_filename.endswith(".conf"):
            args.config_filename += ".conf"
        args.v2 = True
    elif choice == 8:
        logger.rich("Exiting...")
        sys.exit(0)
    else:
        logger.rich("[red]Invalid choice[/red]")
        return
    

def main():
    setup_logging()
    logger.rich(f"[red bold]{title}[/red bold]\n")

    parser = argparse.ArgumentParser(description="Subtitle Translator Utility")
    parser.add_argument("--generate-config", nargs='?', const="SubTraductorV3.conf",
                        help="Regenerate the configuration file. Optionally specify a filename. (default SubTraductorV3.conf)")
    parser.add_argument("--config-filename", type=str, nargs='?', default="SubTraductorV3.conf", 
                        help="Filename of the config file to use. (default SubTraductorV3.conf)")
    parser.add_argument("--extract-rename", nargs='?', const=True, type=bool, 
                        help="Extract and rename subtitles.")
    parser.add_argument("--mkv-create", nargs='?', const=True, type=bool, 
                        help="Create mkv files with new translated subs.")
    parser.add_argument("--cut", nargs='?', type=str, const="SubTraductorV3.conf", help=argparse.SUPPRESS)
    parser.add_argument("--single-thread", nargs='?', const=True, type=bool, help="Run the translation in a single thread.")
    parser.add_argument("--sync-sub", nargs='?', const=True, type=bool, help="Tool to help Sync subtitles. can display the shift and apply it.\nWork for only 1 shift between files.\nBetter performance with same language subs but can work with different language subs.")
    parser.add_argument("--mkv-extract", nargs='?', const=True, type=bool, help="Extract ASS/SRT subtitles from MKV files.\nIn case of SRT the file will be convert to ASS")
    parser.add_argument("--v2", nargs='?', const=True, type=bool, help="One Piece V2 helper for Livai")

    args = parser.parse_args()
    args.help = None
    
    if len(sys.argv) <= 1:
        show_menu(args)

    # better args logging
    logger.rich(args)

    if args.help is not None:
        parser.print_help()
        return
    
    if args.mkv_extract is not None:
        ask_for_extract()
        return

    if args.sync_sub is not None:
        sync_subs()
        return

    if args.extract_rename is not None:
        ask_for_unzip()
        return
    
    if args.mkv_create is not None:
        ask_for_mkv_merge()
        return

    if args.generate_config is not None:
        generate_config(args.generate_config)
        return
    
    config = load_config(args.config_filename)
    
    if config is None:
        logger.error("Failed to load config file")
        return

    if args.v2 is not None:
        one_piece_v2_helper(config)

    if args.cut is not None:
        print_cut_timecodes(config, args.cut)
        return
    
    logger.debug(config.log())

    numbers = input("Enter films to translate (1,2,3), nothing for all films: ").replace(" ", "").split(",")
    if len(numbers) > 0 and numbers[0] != "":
        config.films_to_build = [film for film in config.films_to_build if str(film.number) in numbers]
    
    if args.single_thread is not None:
        translate_subs_single_thread(config)
    else:
        translate_subs_treaded(config)
    

if __name__ == '__main__':
    multiprocessing.freeze_support()
    while True:
        main()
        input("Enter to continue...")