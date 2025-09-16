import pysubs2, os, logging
from typing import List
from src.helpers import shift
from copy import deepcopy
from tqdm import tqdm

from src.interface import Config, Timecode, SubFile, Time, FilmInfos
from src.sub_files_loader import load_sub_files

logger = logging.getLogger(__name__)

class SubBuilder:
    def __init__(self, config: Config, current_to_build_path: str, film_file_name: str, timecodes: list[Timecode]) -> None:
        self.config = config
        self.current_to_build_path = current_to_build_path
        self.film_file_name = film_file_name
        self.toBuild_subs: list[SubFile] = []
        self.timecodes = timecodes
        
        film_infos: FilmInfos = config.get_film_info(film_file_name)

        self.toBuild_subs: List[SubFile] = load_sub_files(current_to_build_path, film_infos.covered_episodes, to_build=True)

    def build_subs(self, progressbarPosition: int) -> None:
        printName = self.film_file_name[0:(len(self.film_file_name)//2)]

        result_ass = pysubs2.SSAFile()

        logger.info(f"loaded subs files : {len(self.toBuild_subs)}")

        progressBar = tqdm(total=len(self.timecodes), desc=f"Build sub {printName}", unit="timecode", position=progressbarPosition, leave=False)

        for timecode in self.timecodes:
            currentSub_file = deepcopy(next((s for s in self.toBuild_subs if s.episode_number == timecode.episode_number), None))
            
            if currentSub_file is None:
                logger.rich(f"[red]No subtitle file found for episode {timecode.episode_number}[/]", logging.ERROR)
            
            logger.info(f"timecode {timecode.episode_number} {timecode.sub_file_name}: {Time(timecode.start)} - {Time(timecode.end)} : shift {timecode.shift.time}")

            for sub in currentSub_file.pysub_file:
                if sub.end > timecode.end:
                    if sub.start < timecode.end:
                        sub.end = timecode.end
                        sub = shift(sub, timecode.shift.time)
                        result_ass.append(sub)
                        progressBar.update(1)
                    break
                
                if sub.end >= timecode.start:
                    if sub.start < timecode.start:
                        sub.start = timecode.start
                    sub = shift(sub, timecode.shift.time)
                    result_ass.append(sub)
                    progressBar.update(1)

        self.remove_duplicate(result_ass)
        result_ass.events.sort(key=lambda e: e.start)

        ep_sub = self.toBuild_subs.pop().pysub_file

        if not "PlayResY" in ep_sub.info:
            ep_sub = self.toBuild_subs.pop(0).pysub_file

        try:
            if "PlayResX" not in ep_sub.info:
                self.default_1080_style(result_ass)
            else: 
                result_ass.styles = ep_sub.styles
                result_ass.info["PlayResX"] = ep_sub.info["PlayResX"]
                result_ass.info["PlayResY"] = ep_sub.info["PlayResY"]
        except:
            pass

        if not os.path.exists(self.config.save_path):
            os.makedirs(self.config.save_path)
        

        full_save_path = os.path.join(self.config.save_path, f"{os.path.basename(self.current_to_build_path)}", f"{self.film_file_name}")
        try:
            if not os.path.exists(os.path.dirname(full_save_path)):
                os.makedirs(os.path.dirname(full_save_path))
        except:
            pass
        
        remove_unused_styles(result_ass)

        logger.info(f"Result file saved: {full_save_path}")
        result_ass.save(full_save_path, overwrite=True, encoding='utf-8')


    def remove_duplicate(self, subs: pysubs2.SSAFile):
        subs.events.sort(key=lambda e: (e.text, e.start, e.end))
        
        sub_to_remove: list[pysubs2.SSAEvent] = []

        for i in range(len(subs) - 1):
            current = subs[i]
            next_sub = subs[i + 1]

            # Check for exact duplicate
            if current.text == next_sub.text and current.start == next_sub.start and current.end == next_sub.end:
                sub_to_remove.append(next_sub)
                continue
            
            # Check for overlapping subtitles with the same text
            if current.text == next_sub.text:
                if (current.start <= next_sub.start < current.end) or (next_sub.start <= current.start < next_sub.end):
                    # Remove the one with the shorter duration
                    if (current.end - current.start) >= (next_sub.end - next_sub.start):
                        sub_to_remove.append(next_sub)
                    else:
                        sub_to_remove.append(current)
                    continue

            # Remove less than 100 ms subs
            if (current.end - current.start) < 80:
                sub_to_remove.append(current)
                continue
        
        sub_to_remove = sorted(sub_to_remove, reverse=True)

        for sub in sub_to_remove:
            logger.info(f"Duplicate removed: {sub.text} {Time(sub.start)}")
            if sub in subs.events:
                subs.events.remove(sub)


    def default_1080_style(self, subs: pysubs2.SSAFile):
        subs.info["PlayResY"] = 1080
        subs.info["PlayResX"] = 1920

        for style in subs.styles:
            subs.styles[style].fontname = "Arial"
            subs.styles[style].fontsize = 60
            subs.styles[style].outline = 3
            subs.styles[style].shadow = 2
            subs.styles[style].marginv = 70
            subs.styles[style].marginl = 70
            subs.styles[style].marginr = 70
            subs.styles[style].marginb = 70

def remove_unused_styles(subs: pysubs2.SSAFile):
    used_styles = set()
    for event in subs.events:
        used_styles.add(event.style)

    unused_styles = set(subs.styles.keys()) - used_styles

    for style in unused_styles:
        del subs.styles[style]
                        



               

            


