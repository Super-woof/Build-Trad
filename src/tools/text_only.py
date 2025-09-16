import pysubs2, os

def text_only(file1, file2):

    ass1 = pysubs2.load(file1, encoding='utf-8')
    ass1.events.sort(key=lambda e: e.start)
    with open(os.path.join(os.curdir, "temp", "text1.txt"), 'w', encoding='utf-8') as f:
        for line in ass1:
            f.write(line.text + "\n")

    ass2 = pysubs2.load(file2, encoding='utf-8')
    ass2.events.sort(key=lambda e: e.start)
    with open(os.path.join(os.curdir, "temp", "text2.txt"), 'w', encoding='utf-8') as f:
        for line in ass2:
            f.write(line.text + "\n")


if __name__ == '__main__':

    file1 = "G:\\Animé\\FanKai\\Black Clover Kaï - Saison 1 [Livaï]\\[Livaï] Black Clover Kaï Saison 2\\Saison 2\\translated\English\\[Livaï] Black Clover Kaï - 09 - La sélection des chevaliers royaux - 1080p.MULTI.x264.ass"
    file2 = "G:\Animé\\FanKai\\Black Clover Kaï - Saison 1 [Livaï]\\[Livaï] Black Clover Kaï Saison 2\\Saison 2\\translated\\English\\23.ass"

    try: 
        os.mkdir("temp")
    except Exception:
        pass

    text_only(file1, file2)

