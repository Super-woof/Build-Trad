import os, sys, logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.interface import Config, Timecode, Time, Stats, Cut
from src.timecode_finder import TimecodesFinder
from src.sub_builder import SubBuilder
from src.constants import MS_TEN_S

logger = logging.getLogger(__name__) 

def process(config: Config, film_sub_name: str, position: int, is_thread=True) -> Stats:
    if is_thread:
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)
        def log_rich(message, level=logging.INFO):
            pass
        logger.rich = log_rich
    try:
        finder: TimecodesFinder = TimecodesFinder(config, film_sub_name)
        timecodes, stats = finder.find_timecodes(position)
    except FileNotFoundError as e:
        logger.warning(e)
        return Stats(str(config.get_film_info(film_sub_name).number), -1)
    except Exception as e:
        logger.rich(e, level=logging.ERROR)
        return

    # TODO mettre dans le log file
    if not os.path.exists(config.subs_to_translate_path):
        logger.rich(f"[red][bold]subs-to-translate-path ({config.subs_to_translate_path})[/bold] is not a valid path[/red]")
        return

    for lg_sub_toBuild in os.listdir(config.subs_to_translate_path):
        current_to_build_path = os.path.join(config.subs_to_translate_path, lg_sub_toBuild)
        
        if os.path.isdir(current_to_build_path):
            builder = SubBuilder(config, current_to_build_path, film_sub_name, timecodes)
            builder.build_subs(position)
        
        if lg_sub_toBuild.endswith(".ass"):
            current_to_build_path = config.subs_to_translate_path
            builder = SubBuilder(config, current_to_build_path, film_sub_name, timecodes)
            builder.build_subs(position)
            break
    return stats


def translate_subs_treaded(config: Config):
    # avoid logs in multithread
    with ThreadPoolExecutor() as executor:
        futures = []
        results: list[Stats] = []
        position = 0
        for film_sub_name in os.listdir(config.films_path):
            if not film_sub_name.endswith(".ass") or not config.is_to_build(film_sub_name):
                continue

            futures.append(executor.submit(process, config, film_sub_name, position))
            position += 1

        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"Task generated an exception: {e}")

        Stats.print_stats(results)

def translate_subs_single_thread(config: Config):
    position = 0
    results = []
    for film_sub_name in os.listdir(config.films_path):
        if not film_sub_name.endswith(".ass") or not config.is_to_build(film_sub_name):
            continue

        stats = process(config, film_sub_name, position, False)
        results.append(stats)
    
    Stats.print_stats(results)


def print_cut_timecodes(config: Config, film_name: str):
    timecodes: list[Timecode] = None

    film_name = film_name.replace("./", "").replace(".\\", "")
    
    for film_sub_name in os.listdir(config.films_path):
        if not film_sub_name.endswith(".ass"):
            continue
        if not film_name or film_name == film_sub_name:
            try:
                finder: TimecodesFinder = TimecodesFinder(config, film_sub_name)
                timecodes, stats = finder.find_timecodes(0)
            except Exception as e:
                logger.error(e)
                sys.exit(1)
            
            break
    Stats.print_stats([stats])
    
    cut_times: List[Cut] = []

    for time in timecodes:
        cut_times.append(Cut(time))

    cut_times.sort(key=lambda t: t.film_time)

    # for i in range(len(cut_times) - 1, 0, -1):
    #     if abs(cut_times[i][0].time - cut_times[i - 1][0].time) < MS_TEN_S:
    #         del cut_times[i]

    for i in range(len(cut_times) - 1, 0, -1):
        if abs(cut_times[i].ep_start - cut_times[i - 1].ep_end) < MS_TEN_S:
            if cut_times[i].episode_number == cut_times[i - 1].episode_number:
                cut_times[i - 1].ep_end = cut_times[i].ep_end
                del cut_times[i]

    with open(f"{film_name}.txt", "w") as f:
        for time in cut_times:
            logger.info(f"{time}")
            f.write(f"{time}\n")
