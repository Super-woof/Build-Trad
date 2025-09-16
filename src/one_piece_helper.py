import os, logging, sys
from typing import List


from src.interface import Config, Timecode, Time, Stats, Cut
from src.timecode_finder import TimecodesFinder
from src.constants import MS_TEN_S


logger = logging.getLogger(__name__) 

EDL_HEADER = '"ID";"Track";"StartTime";"Length";"PlayRate";"Locked";"Normalized";"StretchMethod";"Looped";"OnRuler";"MediaType";"FileName";"Stream";"StreamStart";"StreamLength";"FadeTimeIn";"FadeTimeOut";"SustainGain";"CurveIn";"GainIn";"CurveOut";"GainOut";"Layer";"Color";"CurveInR";"CurveOutR";"PlayPitch";"LockPitch";"FirstChannel";"Channels"'

def edl_line(id:int, track_id:int, start_time: float, length: float, media_type: str, path: str, stream_start:float) -> str:
    if media_type == "VIDEO":
        end_options = "0.0000; 0.0000; 1.000000; 4; 0.000000; 4; 0.000000; 0; -1; 4; 4; 0.000000; FALSE; 0; 0"
    elif media_type == "AUDIO":
        end_options = "0.0000; 0.0000; 1.000000; 2; 0.000000; -2; 0.000000; 0; -1; -2; 2; 0.000000; FALSE; 0; 0"
    return f'{id}; {track_id}; {start_time}; {length}; 1.000000; FALSE; FALSE; 0; TRUE; FALSE; {media_type}; "{path}"; 0; {stream_start}; {length}; {end_options}'

def one_piece_v2_helper(config: Config):
    results: List[Stats] = []

    for film_sub_name in os.listdir(config.films_path):
        if not film_sub_name.endswith(".ass") or not config.is_to_build(film_sub_name):
            logger.info(f"{film_sub_name} is not a .ass or not in config")
            continue
        try:
            finder: TimecodesFinder = TimecodesFinder(config, film_sub_name)
            timecodes, stats = finder.find_timecodes(0)
            
            results.append(stats)
        except FileNotFoundError as e:
            logger.warning(e)
            return Stats(str(config.get_film_info(film_sub_name).number), -1)
        except Exception as e:
            logger.rich(e, level=logging.ERROR)
            return
        
        cuts_time = process_timecodes(timecodes)
        save_timecodes_txt(film_sub_name, cuts_time)
        save_edl(film_sub_name, cuts_time)

    Stats.print_stats(results)
    sys.exit(0)

def process_timecodes(timecodes: List[Timecode]) -> List[Cut]:
    cuts_time: List[Cut] = []

    for timecode in timecodes:
        cuts_time.append(Cut(timecode))

    cuts_time.sort(key=lambda t: t.film_time)


    for i in range(len(cuts_time) - 1, 0, -1):
        if abs(cuts_time[i].ep_start - cuts_time[i - 1].ep_end) < MS_TEN_S:
            if cuts_time[i].episode_number == cuts_time[i - 1].episode_number:
                cuts_time[i - 1].ep_end = cuts_time[i].ep_end
                del cuts_time[i]  

    return cuts_time

def save_timecodes_txt(film_sub_name: str, cuts_time: List[Cut]):
    if not os.path.exists("./One Piece V2"):
        try:
            os.makedirs("One Piece V2")
        except:
            logger.error("Can't create One Piece V2 folder in current path")
            sys.exit(1)

    with open(f"./One Piece V2/{film_sub_name}.txt", "w", encoding='utf-8') as f:
        for time in cuts_time:
            logger.info(f"{time}")
            f.write(f"{time}\n")

def save_edl(film_sub_name: str, cuts_time: List[Cut]):
    if not os.path.exists("./One Piece V2"):
        try:
            os.makedirs("One Piece V2")
        except:
            logger.error("Can't create One Piece V2 folder in current path")
            sys.exit(1)

    print("Le nom des fichiers audio et vidéo utilisés dans l'EDL seront les mêmes que ceux des sous-titres associés")
    v_path = input("Entrer le chemin vers le dossier des vidéos (C:/path/to/videos/): ").replace("\"", "")
    while not os.path.exists(v_path):
        v_path = input("Le chemin n'existe pas, veuillez entrer un chemin valide: ").replace("\"", "")

    a_path = input("Entrer le chemin vers le dossier des audios (C:/path/to/audios/): ").replace("\"", "")
    while not os.path.exists(a_path):
        a_path = input("Le chemin n'existe pas, veuillez entrer un chemin valide: ").replace("\"", "")

    with open(f"./One Piece V2/{film_sub_name}.edl", "w", encoding='utf-8') as f:
        f.write(EDL_HEADER + "\n")
        id = 1
        for time in cuts_time:
            f.write(edl_line(id=id, track_id=1, start_time=time.film_time.time, length=time.ep_end.time - time.ep_start.time, media_type="VIDEO", path=os.path.join(v_path, time.file_name+".mp4"), stream_start=time.ep_start.time) + "\n")
            id += 1
        for time in cuts_time:
            f.write(edl_line(id=id, track_id=0, start_time=time.film_time.time, length=time.ep_end.time - time.ep_start.time, media_type="AUDIO", path=os.path.join(a_path, time.file_name+".flac"), stream_start=time.ep_start.time) + "\n")
            id += 1
    print(f"EDL file saved in One Piece V2/{film_sub_name}.edl")