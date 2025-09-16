import pysubs2, string, os, rich
import numpy as np
import logging
import re
from difflib import SequenceMatcher
import rich.logging


MAX_SHIFT = 5000
THRESHOLD = 0.60

logger = logging.getLogger(__name__)

def time_round(sub: pysubs2.SSAEvent) -> pysubs2.SSAEvent:
    lastD = sub.start % 10
    if lastD > 4:
        sub.start -= lastD
        sub.start += 10
    else:
        sub.start -= lastD
    
    lastD = sub.end % 10
    if lastD > 4:
        sub.end -= lastD
        sub.end += 10
    else:
        sub.end -= lastD

    return sub


def shift(sub: pysubs2.SSAEvent, ms_shift: int):
    sub.start += ms_shift
    sub.end += ms_shift
    return time_round(sub)


def match_fr(s1, s2):
    s1 = re.sub(r'\{.*?\}', '', s1).lower().replace("\\n", "").strip().translate(str.maketrans('', '', string.punctuation+"’…"))
    s2 = re.sub(r'\{.*?\}', '', s2).lower().replace("\\n", "").strip().translate(str.maketrans('', '', string.punctuation+"’…"))
    return SequenceMatcher(None, s1, s2).quick_ratio() > 0.9

def match_lgdiff(str1, str2):
    str1 = str1.lower()
    str2 = str2.lower()

    # Calculate text length and punctuation similarity
    length_match = abs(len(str1) - len(str2)) / max(len(str1), len(str2))
    punc_match = abs(sum(c in string.punctuation for c in str1) - sum(c in string.punctuation for c in str2)) / max(1, max(sum(c in string.punctuation for c in str1), sum(c in string.punctuation for c in str2)))
    
    # Check special conditions for matching
    question_mark_match = 0 if '?' in str1 and '?' in str2 else 1
    styles_mark = 0 if '{\\' in str1 and '{\\' in str2 else 1
    space_match = abs(str1.count(' ') - str2.count(' ')) / max(1, max(str1.count(' '), str2.count(' ')))

    # Overall match score
    match_score = (length_match + punc_match + space_match + question_mark_match + styles_mark) / 5
    similarity = 1 - match_score
    return similarity >= THRESHOLD


def match_events(sync_file: pysubs2.SSAFile, unsync: pysubs2.SSAFile, match: callable) -> tuple:
    fr_matches, unsync_matches = [], []
    unsync_index = 0  # To keep track of the last processed unsynced subtitle index
    
    for fr_event in sync_file:
        # Search for potential matches within the time window
        potential_matches = []
        
        # Skip searching if previous matches cover this range
        if unsync_index < len(unsync):
            potential_matches = [event for event in unsync[unsync_index:] 
                                 if abs(event.start - fr_event.start) <= MAX_SHIFT]
        
        if potential_matches:
            for unsync_event in potential_matches:
                if match(fr_event.text, unsync_event.text):
                    fr_matches.append(fr_event)
                    unsync_matches.append(unsync_event)
                    unsync_index = unsync.index(unsync_event) + 1  # Update index to the next unprocessed event
                    logger.debug(f"Matched: {fr_event.text} - {unsync_event.text}")
                    break  # Found a match, move to the next `fr_event`

    return fr_matches, unsync_matches

def middle_time(event: pysubs2.SSAEvent) -> int:
    return (event.start + event.end) // 2

def compute_average_shift(fr_matches, unsync_matches) -> int:
    if not fr_matches or not unsync_matches:
        logger.warning("No matching events found for shift computation.")
        return 0

    # Calculate shifts
    shifts = [middle_time(fr_event) - middle_time(unsync_event) for fr_event, unsync_event in zip(fr_matches, unsync_matches)]
    
    # Convert shifts to a NumPy array for easier statistical analysis
    shifts_array = np.array(shifts)

    # Filter out outliers using the 1.5 * IQR method (Interquartile Range)
    Q1 = np.percentile(shifts_array, 25)
    Q3 = np.percentile(shifts_array, 75)
    IQR = Q3 - Q1
    filtered_shifts = shifts_array[(shifts_array >= (Q1 - 1.5 * IQR)) & (shifts_array <= (Q3 + 1.5 * IQR))]

    mid_index = len(filtered_shifts) // 2
    first_half = filtered_shifts[:mid_index]
    second_half = filtered_shifts[mid_index:]

    average_shift = np.mean(filtered_shifts) if filtered_shifts.size > 0 else 0
    avg_first_half = np.mean(first_half) if first_half.size > 0 else 0
    avg_second_half = np.mean(second_half) if second_half.size > 0 else 0

    logger.rich(f"Base on {len(fr_matches)} correspondences")
    logger.rich(f"Average shift (filtered): {average_shift:.2f} ms")
    logger.rich(f"Average shift (first 50%): {avg_first_half:.2f} ms")
    logger.rich(f"Average shift (second 50%): {avg_second_half:.2f} ms")
    if abs(avg_first_half - avg_second_half) > 500:
        logger.rich("[red]Shifts are not consistent between the two halves.[/]")
        return 0
    if average_shift > MAX_SHIFT:
        logger.rich(f"[red]Average shift exceeds the maximum allowed value ({MAX_SHIFT} ms).[/]")
        return 0
    if len(filtered_shifts) < 10:
        logger.rich("[red]Not enough data points for reliable shift calculation.[/]")
        return 0

    return int(average_shift)


def load_files(sync_file, unsync_file):
    try:
        fr_subs = pysubs2.load(sync_file, encoding='utf-8')
        unsync_subs = pysubs2.load(unsync_file, encoding='utf-8')
    except Exception as e:
        logger.error(f"Error loading subtitle files: {e}")
        return None, None
    
    fr_subs.sort()
    unsync_subs.sort()

    return fr_subs, unsync_subs

def sync_sub(sync_file, unsync_file, match: callable):
    
    fr_subs, unsync_subs = load_files(sync_file, unsync_file)
    if not fr_subs or not unsync_subs:
        return

    fr_matches, unsync_matches = match_events(fr_subs, unsync_subs, match)
    avg_shift = compute_average_shift(fr_matches, unsync_matches)

    return avg_shift



def apply_shift(sync_file, unsync_file, avg_shift):
    
    fr_subs, unsync_subs = load_files(sync_file, unsync_file)
    if not fr_subs or not unsync_subs:
        return

    # move unsynced subs to unsynced_subs folder thene same the synced subs
    unsynced_subs_folder = os.path.join(os.path.dirname(unsync_file), "unsynced_subs")
    unsynced_file = os.path.join(unsynced_subs_folder, os.path.basename(unsync_file))

    try:
        unsync_subs.save(unsynced_file, overwrite=True)
        logger.rich(f"Unsynced subtitles saved to: {unsynced_file}")
    except Exception as e:
        logger.error(f"Error moving unsynced subtitles: {e}")
        return
    
    # Apply the computed average shift to the unsynced subtitles
    for event in unsync_subs:
        shift(event, avg_shift)

    try:
        unsync_subs.save(unsync_file, overwrite=True)
        logger.rich(f"Synced subtitles saved to: {unsync_file}")
    except Exception as e:
        logger.error(f"Error saving synced subtitles: {e}")
        return


def sync_subs():

    sync_subs_folder = input("Enter the folder path of synced subtitles: ")
    while not os.path.exists(sync_subs_folder):
        sync_subs_folder = input("Invalid folder, Enter the folder path of synced subtitles: ")

    unsync_subs_folder = input("Enter the folder path of unsynced subtitles: ")
    while not os.path.exists(unsync_subs_folder):
        unsync_subs_folder = input("Invalid folder, Enter the folder path of unsynced subtitles: ")

    same_lg = input("Are the subtitles in the same language? (y/n): ")
    while same_lg not in ['y', 'n']:
        same_lg = input("Invalid input, Are the subtitles in the same language? (y/n): ")
    
    max_shift = input("Enter the maximum shift value (default 2500 ms): ")
    try:
        global MAX_SHIFT
        MAX_SHIFT = int(max_shift) * 2
    except ValueError:
        pass

    if same_lg == 'y':
        match = match_fr
    else:
        match = match_lgdiff

    sync_subs_files = [file for file in os.listdir(sync_subs_folder) if file.endswith(".ass")]
    unsync_subs_files = [file for file in os.listdir(unsync_subs_folder) if file.endswith(".ass")]

    if len(sync_subs_files) != len(unsync_subs_files):
        logger.error(f"The number of files in folder doesn't match ({len(sync_subs_folder)} vs {len(unsync_subs_folder)})")
        return
    
    
    avg_shifts = {}

    for sync_file, unsync_file in zip(sync_subs_files, unsync_subs_files):
        logger.rich(f"\nFile: {sync_file} - {unsync_file}")
        avg_shifts[unsync_file] = sync_sub(os.path.join(sync_subs_folder, sync_file), os.path.join(unsync_subs_folder, unsync_file), match)


    logger.rich("\n[orange3]If any red message is written for a file no shift will be applied[/]")
    apply = input("Apply the computed shift? (y/n): ")
    while apply not in ['y', 'n']:
        apply = input("Invalid input, Apply the computed shift? (y/n): ")

    if apply == 'n':
        return
    
    try:
        os.makedirs(os.path.join(unsync_subs_folder, "unsynced_subs"), exist_ok=True)
    except Exception as e:
        logger.error(f"Error creating output folder: {e}")
        return

    for sync_file, unsync_file in zip(sync_subs_files, unsync_subs_files):
        apply_shift(sync_file, unsync_file, avg_shifts[unsync_file])
        

if __name__ == '__main__':
    logger.setLevel(logging.INFO)

    # sync_file = "sync_test/fr.ass"
    # UNSYNC_EN = "sync_test/unsynced/en.ass"
    
    # sync_subs(sync_file, UNSYNC_EN)
    def rich_print(m, l=logging.INFO):
        rich.print(m)

    logger.rich = rich_print

    sync_subs_folder = "D:\\sub\\sub\\fairy-tail-fear-teiru-complete-series_french-1660430"
    unsync_subs_folder =  "D:\\sub\\sub\\FT_English"

    sync_subs()
