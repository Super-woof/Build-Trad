import subprocess, logging
import os, rich, sys, json
import pysubs2


logger = logging.getLogger(__name__)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

MKV_EXTRACT = resource_path("./assets/mkvextract.exe")
MKV_MERGE = resource_path("./assets/mkvmerge.exe")


def print_mkvmerge_json_info(file_path):
    additional_infos: dict[dict] = {}
    try:
        # Run mkvmerge command to get detailed info in JSON format
        command = [MKV_MERGE, '-i', '-F', 'json', file_path]

        logger.debug(command)

        result = subprocess.run(command, 
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        logger.debug(result)

        if result.returncode == 0:
            # Load the JSON output
            info = json.loads(result.stdout)
            
            # Print relevant track information
            tracks = info.get('tracks', [])
            for track in tracks:
                logger.rich("-" * 40)
                track_id = track.get('id', 'N/A')
                
                additional_infos[track_id] = {
                    'id': track_id,
                    'codec': track.get('codec', 'N/A'),
                    'language': track.get('properties', {}).get('language', 'N/A'),
                    'type': track.get('type', 'N/A'),
                    'name': track.get('properties', {}).get('track_name', 'N/A'),
                    'codec_id': track.get('properties', {}).get('codec_id', 'N/A')
                }

                logger.rich(f"Track ID: [green bold]{additional_infos[track_id]['id']}[/green bold]")
                logger.rich(f"Name: [orange3]{additional_infos[track_id]['name']}[/]")
                logger.rich(f"Codec: {additional_infos[track_id]['codec']} ({additional_infos[track_id]['codec_id']})")
                logger.rich(f"Language: {additional_infos[track_id]['language']}")
                logger.rich(f"Type: {additional_infos[track_id]['type']}")
        else:
            print(f"Error: {result.stderr}")
    except FileNotFoundError:
        print("Can't found embedded mkvextract.exe")
    except json.JSONDecodeError:
        print("Error: Failed to parse JSON output.")
    return additional_infos

def mkv_infos(mkv_files_path: list[str]):
    additional_infos = print_mkvmerge_json_info(mkv_files_path[0])
    if len(additional_infos) == 0:
        logger.rich("[red]No track information found[/]")
        return

    logger.rich("Enter [green]trackId[/] of subtitle track you want to extract in all films")

    track_id = input("Track ID: ").strip()
    while not track_id.isdigit() or int(track_id) not in additional_infos:
        logger.rich("[red]Track ID must be a number or an existing Id[/]")
        track_id = input("Track ID: ").strip()

    track_id = int(track_id)

    track_info = additional_infos[track_id]
    logger.rich("-" * 40)
    logger.rich(f"Track ID: [green bold]{track_info['id']}[/green bold]")
    logger.rich(f"Name: [orange3]{track_info['name']}[/]")
    logger.rich(f"Codec: {track_info['codec']} ({track_info['codec_id']})")
    logger.rich(f"Language: {track_info['language']}")
    logger.rich(f"Type: {track_info['type']}")
    
    return track_info


def extract_subtitles(mkv_files_path: list[str], track_info: dict, output_path: str):
    if 'SubRip' in track_info['codec']:
        srt_extract = True
    else:
        srt_extract = False
    
    for file in mkv_files_path:
        try:
            file_basename = os.path.join(output_path, os.path.basename(file)).replace('.mkv', '')
            
            if srt_extract:
                command = [MKV_EXTRACT, file, f"tracks", f"{track_info['id']}:{file_basename}.srt"]
            else:
                command = [MKV_EXTRACT, file, f"tracks", f"{track_info['id']}:{file_basename}.ass"]
            
            logger.debug(command)
            result = subprocess.run(command, check=True, text=True, encoding='utf-8')
            logger.debug(result)

            try:
                if srt_extract:
                    sub = pysubs2.load(f"{file_basename}.srt")
                    sub.save(f"{file_basename}.ass")

                    try:
                        os.remove(f"{file_basename}.srt")
                    except:
                        logger.error("Can't remove srt file")
            except FileNotFoundError as e:
                logger.error(f"Can't found {file_basename}.srt")
                logger.error(e)

            if result.returncode == 0:
                logger.rich(f"Subtitles extracted from {file} !")
            else:
                logger.rich(f"Error: {result.stderr}")
        except FileNotFoundError:
            logger.rich("Can't found embedded mkvextract.exe")
        except json.JSONDecodeError:
            logger.rich("Error: Failed to parse JSON output.")
        except Exception as e:
            logger.rich(f"Error: {e}")

    logger.rich("Subtitles extraction completed !")
    

def ask_for_extract():
    mkv_path = input("Enter the path to the MKV video folder: ").strip()
    while True:
        if not os.path.exists(mkv_path):
            logger.rich("[red]MKV file path does not exist[/]")
        elif not any(file.endswith(".mkv") for file in os.listdir(mkv_path)):
            logger.rich("[red]No .mkv files found in the directory[/]")
        else:
            break
        mkv_path = input("Enter the path to the MKV folder: ").strip()

    logger.rich(f"MKV path: {mkv_path}")

    mkv_files_path = [os.path.join(mkv_path, file) for file in os.listdir(mkv_path) if file.endswith(".mkv")]

    logger.rich(f"MKV files found:\n[green]{"\n".join(mkv_files_path)}[/]")

    track_info = mkv_infos(mkv_files_path)

    logger.rich("Enter the path to save the extracted subtitles")
    output_path = input("Output path: ").strip()
    if not os.path.exists(output_path):
        try:
            os.makedirs(output_path)
            logger.rich("[orange3]Output has been created[/]")
        except:
            logger.rich("[red]Failed to create output folder[/]")
            return
        
    extract_subtitles(mkv_files_path, track_info, output_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def rich_fct(e, l=logging.INFO):
        rich.print(f"[{l}] {e}")

    logger.rich = rich_fct

    ask_for_extract()













