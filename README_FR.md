# SubTraductorV3
defaut value in conf

attention path par defaut pas ./
## Instructions

### 0. Télécharger des sous-titres de la série
   - Télécharger des sous-titre des épisodes Français de la série
   - Téléchargez les fichiers de sous-titres dans d'autre langues
     - ⚠ Il est important que ces sous-titres soit synchronisés avec ceux en Français   
            Si ce n'est pas le cas voir : [synchroniser les fichiers]()
   - Il est possible de trouver simplement les sous-titres de plusieurs langues et synchronisés depuis **[Erai-raws](https://www.erai-raws.info/)**

### 1. Extraire les sous-titres des films (VOST)
   - Extraire les sous-titre avec avec SubTraductorV3
      - Executer SubTraductorV3.exe et entrer `0` pour l'option `Extract Subtitles` puis suivez les étapes du programme

   - Extraire les sous-titre ASS avec ffmpeg

cmd/Bat file
```bat
    for %%f in (*.mkv) do (
        @REM Décommenter la ligne qui correspond au type de fichier du film
        @REM ffmpeg -y -i "%%~nf.mkv" -map 0:s:<TODO id de la piste de sous titre vost> -c:s copy "%%~nf.ass"
        
        @REM Si le fichier de sub du mkv est un srt, on le convertie 
        @REM ffmpeg -y -i "%%~nf.mkv" -map 0:s:<TODO id de la piste de sous titre vost> -c:s ass "%%~nf.ass"
    )
``` 

powershell (coller)
```pwsh
foreach ($f in Get-ChildItem -r *.mkv) {ffmpeg -i $f.Name -map 0:s:<TODO id de la piste de sous titre vost> -c:s copy "$($f.BaseName).ass"}
foreach ($f in Get-ChildItem -r *.mkv) {ffmpeg -i $f.Name -map 0:s:<TODO id de la piste de sous titre vost> -c:s copy "$($f.BaseName).srt"}
```

Les mettres dans un dossier, ex:

```
Dossier racine/
    SubTraductorV3.exe

    films/
        fichier ass des films 
``` 



### 2. Extraction et renommage rapide des sous-titres (optionnel)
Pour simplifier la traduction et il est recommandé que les fichiers de sous-titre utilise une numérotation absolue et non relative a la saison   

- Pour simplement renommer tout les fichiers et les séparer par langue, il faut organiser les fichier de cette manière  
(Si les sous-titres ne sont pas dans des archives il faut les créer)
```
Dossier racine/
    SubTraductorV3.exe

    Saison 1/
        langue1.7z ou .zip 
        langue2.7z ou .zip
    Saison 2/
        langue1.7z ou .zip
        langue2.7z ou .zip
``` 

<p float="left">
  <img src="./images/base-folder.png" width="49%" />
  <img src="./images/zip-folder.png" width="49%" /> 
</p>

  
- **Executer** `SubTraductorV3.exe` et entrer `3` pour l'option `Extract and rename`  
  
    - Suivez les étapes du programme (notamment le choix du début de la numérotation des épisodes par saison).
  
Après exécution un nouveau dossier **`to-translate`** à la racine

Pour éviter de retraduire en Français, déplacer le dossier avec les sous-titres Français dans un autre dossier.

**Vous devriez avoir une structure de dossier comme celle-ci:**
```
Dossier racine/
    SubTraductorV3.exe
    
    films/
        .ass des sous-titres des films

    Sub-Français/
        .ass des sous-titres Français
    
    to-translate/
        langue1/  
            tout les .ass de langues 1  
        langue2/  
            tout les .ass de langues 2  
```

#### ⚠ Pour la création du mkv les dossiers de `to-translate` ne doivent avoir que le nom de la langue dans leur nom (ex: "Portuguese(Brazil)" doit être renommé en "Portuguese")

### 3. Génération du fichier de configuration
 
- **Executer** `SubTraductorV3.exe` et entrer `2` pour l'option `Generate Config`  

If faut ensuite suivre les étapes du programme:  
1. Entrer le chemin vers les .ass des films  
2. (optionnel) Essayer de remplir les infos des films à partir du fandom
3. Entrer le chemin vers les .ass des sous-titres Français des épisodes
4. Entrer le chemin vers le dossier avec les langues a traduire (ex: `to-translate`)
5. Enter le chemin ou sauvegarder les fichiers traduit
6. Regarder les Messages du tableau **Configuration Information**
7. Vérifier que tout est correct, notamment les épisodes couvert si le fandom à été utilisé ([wiki fandom](https://fan-kai.fandom.com/fr/wiki/Guide_des_%C3%A9pisodes)) 

### 4. Traduction

- **Executer** `SubTraductorV3.exe` et entrer `1` pour l'option `Translate` 

1. Entrer le nom du fichier de configuration, celui-ci doit être au même endroit que l’exécutable
2. Use multithread for translation: `Y` sauf si besoin de débogage
3. Vérifier que la config est toujours bonne dans le cas ou elle à été modifié
4. Entrer le numéro (ex: "1,5,6") des films à traduire ou "Entrer" pour tout traduire
5. Une fois la traduction terminé un tableau s'affiche pour donner le % de sous-titre retrouvé dans les épisodes français
6. Si le % est rouge ou orange pour un film:
     -  Vérifier si il ne manque pas un épisode dans la config, le texte de 3 sous-titres manquant sera affiché pour crtl f avec **vscode** dans tout les .ass si nécessaire
     -  Vérifier que vos sous-titres et ceux du film soit de la même source, il peut exister plusieurs version (crunshyroll vs wakanime)

#### ⚠ Seul la présence du fichier .ass dans la langue à traduire est vérifié, si il y a une mauvaise correspondance entre les numéros des épisodes entre les fichiers français et ceux en dans la langue à traduire. Le seul moyen de le determiner d'importer le fichier traduit à la lecture avec VLC


### 5. Ajout des nouveaux sous-titres au fichier `.mkv`
#### Une copie des fichiers mkv de base va être crée.

- **Executer** `SubTraductorV3.exe` et entrer `4` pour l'option `Create MKV Files` 
   
   1. Entrer le chemin vers le dossier qui contient les traductions (Un dossier par langue à cette emplacement)
    ```
    translated/
        English/
            *.ass
        Spanish/
            *.ass
    ```
   2. Entrer le chemin du dossier avec les MKV
   3. Vérifier que le la correspondance est bonne 
   4. `Y` pour continuer, `N` pour annuler
   5. Les fichiers seront crées dans un dossier `Translated Films` à la racine du dossier ou se trouvent les mkv


### Synchroniser les subs
- **Executer** `SubTraductorV3.exe` et entrer `5` pour l'option `Sync Subs` 
- Suivre les étapes
  - Fonctionne mieux pour des fichiers de même langue mais peut fonctionner avec des langues différentes
  - Cette option fonctionne que les il y un seul décalage dans le fichier mais permet d'évaluer les décalages

# Voir demo.mp4 pour exemple d'exécution
<video width="50%" height="auto" controls>
  <source src="./Demo.mp4" type="video/mp4">
</video>

## Build :
```powershell
pip install -r requirements.txt
pyinstaller --onefile --noupx --icon "./images/icon.ico" --clean --add-data "./assets/*;assets/" --name "SubTraductorV3" ./main.py
```

## Un problème ?
[discord](https://discordapp.com/users/1012763202137882754)