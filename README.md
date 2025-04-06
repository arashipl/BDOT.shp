Użycie: python BDOT.shp.py [-h] [-all] lub BDOT.shp.exe [-h] [-all]

Scala pliki shapefile z katalogu 'bdot.shp' na podstawie sufiksów, scalając pola o tej samej nazwie.  
Opcje:  
&emsp;-h: Wyświetla tę wiadomość pomocy.  
&emsp;-all: Uwzględnia pliki zawierające '_KUxx', '_ADxx' , '_TCON' i '_SKDR' podczas przetwarzania (normalnie nie scalane ze względu na małą użyteczność w trakcie kreślenia mapy).  

Skrypt oczekuje katalogu o nazwie 'bdot.shp' w bieżącym katalogu roboczym.  
Pliki shapefile obszarów (z sufiksem _A) są scalane do area_merged.shp.  
Pliki shapefile linii (z sufiksem _L) są scalane do line_merged.shp.  
Pliki shapefile punktów (z sufiksem _P) są scalane do point_merged.shp.  

Do prawidłowego działania skrypt skompilowany do pliku exe wymaga pliku proj.db dostępnego np. jako część pakietu OSGeo4Win.

Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
