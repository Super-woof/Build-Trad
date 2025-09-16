import logging
import os, re, string
from difflib import SequenceMatcher
import pysubs2
from typing import List, Tuple
from tqdm import tqdm

from src.interface import Config, SubFile, Timecode, FilmInfos, Time, Stats
from src.helpers import right_shift
from src.sub_files_loader import load_sub_files


# TODO in conf ?
AVG_SIM = 0.75
REQ_SIM = 0.8
NOTFOUND_SIM = 0.65
SINGLE_SIM = 0.98


# Disable
COMBINE_SIM = 0.94
TEST_COMBINE_REQ = 1.2# 0.35 #1

logger = logging.getLogger(__name__)

class TimecodesFinder:
    def __init__(self, config: Config, film_sub_name: str):        
        self.config = config
        film_sub_path = os.path.join(config.films_path, film_sub_name)
        self.films_subs = pysubs2.load(film_sub_path, encoding="utf-8")
        self.film_sub_name = film_sub_name
        self.film_infos: FilmInfos = config.get_film_info(film_sub_name)

        self.fr_subs: List[SubFile] = load_sub_files(config.fr_subs_path, self.film_infos.covered_episodes)

    def find_timecodes(self, progressbarPosition: int) -> Tuple[List[Timecode], Stats]:
        i = len(self.film_sub_name)//2
        printName = self.film_sub_name[0:(len(self.film_sub_name)//2)]
        
        logger.info(f"Finding timecodes for {self.film_sub_name}")

        timecodes: List[Timecode] = []
        stats: Stats = Stats(str(self.film_infos.number), len(self.films_subs))

        previous_not_found_sub: str = ""
        single_sub_best_sim: tuple[pysubs2.SSAEvent, float, str] = (None, -1, None)
        
        # bool correspond to skip next film_sub because it was already found using combine
        combine_sim_best: tuple[pysubs2.SSAEvent, float, str, int, bool] = (None, -1, None, 0, False)
        self.films_subs.events.sort(key=lambda e: e.start)

        progressBar = tqdm(total=len(self.films_subs), desc=f"Find timecodes {printName}", unit="sub", position=progressbarPosition, leave=False)

        i = 0
        while i < len(self.films_subs):

            film_sub = self.films_subs[i]
            match_found = False
            single_sub_best_sim = (None, -1, None)
            combine_sim_best = (None, -1, None, 0, False)

            logger.info(f"Looking for: {film_sub.text}")

            for sub_file in self.fr_subs:
                ep_fr_sub = sub_file.pysub_file
                ep_fr_sub.events.sort(key=lambda e: e.start)
                looking_sub_midle_time = film_sub.start + (film_sub.end - film_sub.start) // 2

                j = 0
                while j < len(ep_fr_sub):
                    ep_sub = ep_fr_sub[j]

                    current_sim = self.srt_similarity(film_sub.text, ep_sub.text)
                    
                    if current_sim > TEST_COMBINE_REQ:
                        combine_sim1 = None
                        combine_sim2 = None
                        combine_sim = 0
                        if j + 1 < len(ep_fr_sub):
                            combine_sim1 = self.srt_similarity(film_sub.text.replace("\\N", ""), f"{ep_sub.text}{ep_fr_sub[j + 1].text}".replace("\\N", ""))
                            combine_end1 = ep_fr_sub[j + 1].end
                        
                        if i + 1 < len(self.films_subs):
                            combine_sim2 = self.srt_similarity(f"{film_sub.text}{self.films_subs[i+1].text}".replace("\\N", ""), ep_sub.text.replace("\\N", ""))
                            conbine_end2 = ep_sub.end

                        combine_sim = max(combine_sim1 if combine_sim1 else 0, combine_sim2 if combine_sim2 else 0)
                        if combine_sim1 == combine_sim:
                            conbine_end = combine_end1
                            is_skipy = False
                        else:
                            conbine_end = conbine_end2
                            is_skipy = True

                        if combine_sim > COMBINE_SIM and combine_sim > combine_sim_best[1]:
                            combine_sim_best = (ep_sub, combine_sim, sub_file.path, conbine_end, is_skipy)

                    if  current_sim > REQ_SIM:

                        if single_sub_best_sim[1] < current_sim:
                            single_sub_best_sim = (ep_sub, current_sim, sub_file.path)

                        _, avg_similarity = self.next_five_similarity(i, self.films_subs, j, ep_fr_sub)
                        
                        if avg_similarity > AVG_SIM:
                            start = j
                            sub_shift = looking_sub_midle_time - (ep_fr_sub[start].start + (ep_fr_sub[start].end - ep_fr_sub[start].start) // 2)
                            
                            matching = True
                            match_using_shift = 0

                            while matching and i < len(self.films_subs) and j < len(ep_fr_sub):
                                film_sub = self.films_subs[i]
                                ep_sub = ep_fr_sub[j]
                                
                                if self.srt_similarity(film_sub.text, ep_sub.text) > REQ_SIM and right_shift(film_sub, ep_sub, sub_shift):
                                    logger.info(f"Found sub in {sub_file.path} at {Time(ep_sub.start)} : \"{film_sub.text}\"")
                                    stats.found += 1

                                    if previous_not_found_sub != "":
                                        if self.srt_similarity(previous_not_found_sub, ep_fr_sub[j - 1].text) > NOTFOUND_SIM or right_shift(film_sub, ep_fr_sub[j - 1], sub_shift):
                                            start = j - 1
                                        previous_not_found_sub = ""
                                    
                                    progressBar.update(1)
                                    i += 1
                                    j += 1
                                elif right_shift(film_sub, ep_sub, sub_shift) and match_using_shift < 3:
                                    match_using_shift += 1
                                    stats.found += 1
                                    i += 1
                                    j += 1
                                    progressBar.update(1)
                                else:
                                    matching = False

                            end = j - 1  # j is incremented one extra time
                            
                            timecodes.append(Timecode(
                                start=ep_fr_sub[start].start,
                                end=ep_fr_sub[end].end,
                                sub_file_name=os.path.basename(sub_file.path),
                                ms_shift=sub_shift,
                            ))

                            match_found = True
                            break  

                    j += 1

                if match_found:
                    break

            if not match_found:
                previous_not_found_sub, is_skip = self.handle_no_match(single_sub_best_sim, combine_sim_best, film_sub, timecodes, stats)
                progressBar.update(1)
                if is_skip:
                    i += 1
                    stats.found += 1
                
                i += 1
            

        return timecodes, stats

    def handle_no_match(self, single_sub_best_sim: Tuple[pysubs2.SSAEvent, float, str], combine_sim_best: Tuple[pysubs2.SSAEvent, float, str, int, bool], film_sub: pysubs2.SSAEvent, timecodes: List[Timecode], stats: Stats) -> tuple[str, bool]:
        if single_sub_best_sim[1] >= SINGLE_SIM:
            timecodes.append(Timecode(
                start=single_sub_best_sim[0].start,
                end=single_sub_best_sim[0].end,
                sub_file_name=os.path.basename(single_sub_best_sim[2]),
                ms_shift=film_sub.start - single_sub_best_sim[0].start,
            ))
            stats.found += 1
            logger.info(f"Single found sub \"{film_sub.text}\" in {single_sub_best_sim[2]} at {Time(single_sub_best_sim[0].start)}")
            return "", False
        elif combine_sim_best[1] > COMBINE_SIM:
            timecodes.append(Timecode(
                start=combine_sim_best[0].start,
                end=combine_sim_best[3],
                sub_file_name=os.path.basename(combine_sim_best[2]),
                ms_shift=film_sub.start - combine_sim_best[0].start,
            ))
            stats.found += 1
            logger.info(f"Combine found sub \"{film_sub.text}\" in {combine_sim_best[2]} at {Time(combine_sim_best[0].start)}")
            return "", combine_sim_best[4]
        else:
            stats.not_found += 1
            stats.subs_not_found.append(film_sub.text)
            logger.warning(f"Sub \"{film_sub.text}\" not found")
            previous_not_found_sub = film_sub.text

        return previous_not_found_sub, False

    def next_five_similarity(self, i: int, films_subs: List[pysubs2.SSAFile], j: int, ep_fr_sub: pysubs2.SSAFile) -> Tuple[int, float]:
        total_similarity = 0
        nb = min(5, len(films_subs) - i, len(ep_fr_sub) - j)

        for k in range(nb):
            similarity = self.srt_similarity(films_subs[i + k].text, ep_fr_sub[j + k].text)
            
            if (similarity < 0.70 and self.is_all_upper_or_number(ep_fr_sub[j + k].text)):
                nb -= 1
                i -= 1
                continue
            
            total_similarity += similarity

        nb = max(1, nb)
        return nb, total_similarity / nb

    def srt_similarity(self, s1: str, s2: str) -> float:
        s1 = re.sub(r'\{.*?\}', '', s1).lower().strip().translate(str.maketrans('', '', string.punctuation))
        s2 = re.sub(r'\{.*?\}', '', s2).lower().strip().translate(str.maketrans('', '', string.punctuation))
        
        # s1 = re.sub(r'\{.*?\}', '', s1).lower().strip().translate(str.maketrans('', '', string.punctuation+"’…"))
        # s2 = re.sub(r'\{.*?\}', '', s2).lower().strip().translate(str.maketrans('', '', string.punctuation+"’…"))
        return SequenceMatcher(None, s1, s2).quick_ratio()
    
    def is_all_upper_or_number(self, s: str):
        s =  re.sub(r'\{.*?\}', '', s)
        return all((c.isupper() or c.isdigit() or not c.isalpha()) for c in s)
