
# Ru_Const

- Корпус с разметкой по связям, составляющим, морфологии и т.п.
- Корпус получен на данных Lenta.ru, для каждого примера доступна ссылка на оригинал в интернете
- В корпусе на данный момент 628.173 предложений, в которых 6.857.935 слов, средняя длина предложения 10,9 слова
- В корпусе еще имеются в некотором количестве ошибки в разметке, прежде всего связанные с типом синтаксической связи
- Поиск по корпусу осуществляется при помощи прилагаемого скрипта, см. ниже
- Первая версия поискового скрипта была написана для другого проекта при участии [Ильи Козиева](https://github.com/Koziev)

### Копирование поискового скрипта и датасета с корпусом

1. Скачиваем архив или клонируем данный репозиторий - он содержит поисковые скрипты и примеры правил

2. Загружаем и распаковываем в папку с файлом EX_tractor_N.N.py (текущая версия - EX_tractor_1.3.py) архив с данными корпуса [отсюда](https://disk.yandex.ru/d/5s9PFzZ2cOSoEQ)

### Настройка скрипта для извлечения примеров (Ex_Extractor):

### Запуск

Из корневой папки с файлом EX_tractor_N.N.py
```
python3 EX_tractor_1.3.py
```
После этого необходимо дождаться, пока будут загружены все данные корпуса.

В поисковом запросе необходимо задать параметры. Параметры задают место расположения правил (--rules по умолчанию: Rules/23), директорию с текущими примера в формате json (--dir_in, по умолчанию: Input/main), файл с текстовым результатом (--output_txt, по умолчанию: Output/search_result.txt), файл с результатом в csv (--output_csv, по умолчанию: Output/search_result.csv), выдачу текстового (--verbosity) и csv (--csv_verbosity) файлов (по умолчанию оба 1)
```
usage: EX_tractor_1.3.py [-h] [--rules RULES] [--dir_in DIR_IN] [--output_txt OUTPUT_TXT]
                           [--verbosity VERBOSITY] [--output_csv OUTPUT_CSV]
                           [--csv_verbosity CSV_VERBOSITY]
```
**NB** Для того, чтобы данные в таблицах csv можно было фильтровать, правила для некоторого запроса на одну и ту же тему должны иметь один и тот же набор обязательных участников! В противном случае данные будут попадать в разные столбцы


Поисковый скрипт считывает все правила в формате yaml из указанной папки. Если файл имеет расширение не yaml, правила считаны не будут.

#### Пример запуска
```
...#Sandbox% python3 EX_tractor_1.3.py --dir_in Input_ --rules 24

```
Запуск с поиском по папке Input_ (куда можно положить подкорпус для какого-либо эксперимента), правила будут браться из директории 'Rules/23/' (она же установлена по умолчанию)


#### Для извлечения примеров используются:

1. Предложение, его ID
1. Все составляющие с такой информацией:  
   1.1. Тип (NP, VP, ...)  
   1.2. Вершина  
   1.3. Морфологические характеристики
2. Все словоформы с такой информацией:  
   2.1. В какую непосредственную составляющую входит (AP, NP, VP, ...): тип фразы, текст  
   2.2. Является ли вершиной  
   2.3. Морфологические характеристики  
   2.4. Тип входящей зависимости


### Инпут:

Корпус состоит из двух больших частей: 1-4 и хранится в json-файлах.
Каждый файл является списком питоновских словарей, содержащих предложение с разметкой. В словаре указывается ID, длина, скобочное представление и ссылка на предложение в интернете (на сайте Lenta.ru). Кроме этого словарь содержит детальную информацию о токенах и составляющих.
Примеры отдельных словарей можно посмотреть в папке ```Input/Examples``` или получить словарь с конкретным примером с помощью скрипта show_json.py, см. ниже. Изучение того, как хранятся отдельные примеры может помочь понять, как задавать поиск по разным критериям (Morph, Links, Lex, LexNonHead). В целом знать структуру корпуса не обязательно.


### Выдача, просмотр результата: json с исходным примером, html с лингвистической информацией
#### json с исходным примером

После получения и отсмотра результата в текстовом или csv формате может возникнуть необходимость в коррекции правил поиска. В этом случае рекомендуется вывести в папку с результатами конкретный интересующий пример в формате json-файла. Для этого нужно задать команду

```
python3 show_json.py --exnum 1_4
```
где --exnum - параметр для задания ID примера, а "1_4" - само ID (ID после параметра exnum всегда пишем без "#")
ID всегда имеет в составе разделитель "_" между двумя цифрами, его можно посмотреть в текстовом или csv файлах:

```
=>из предложения #153316_5
```

```
ex_id	id...
1	84457_13
```

Кроме exnum how_json.py имеет параметры dir_in (по умолчанию Input/main), outdir (по умолчанию Output)

Если файл csv нужно открыть в Excel, при импорте внешних данных выбираем кодировку UTF-8  


#### html с лингвистической информацией

Запуск
```
python3 show_morphosynt.py --exnum 1_4
```

Параметры для входных файлов и т.п. - те же, что в 'show_json.py'. 
Выдает синтаксическую структуру в виде дерева разбора и скобочного представления и список всех слофоморм с их грамматическими значениями.
Для работы html c демонстрацией деревьев в командной строке нужно установить следующие пакеты:

```
pip install nltk
pip install svgling
```

## Формат и примеры правил:

Правила задаются в .yaml - файлах.
См. примеры на отдельные запросы в папке ```Rules```

### Файл с правилами имеет структуру:  

```
ExampleName: Coord_SG_post
Priority: 1
SubExamples
Name: Rule1
Participants:
  - Obligatory: <List>
  - Optional: <List>
..  
Name: Rule2  
```

Правила для одних и тех же типов примеров располагаются внутри одной и той же секции.  
Структура примера, т.е. наличие у него определенных участников, их название и обязательность/факультативность -- задаются на уровне SubExamples.  

Отдельные ExampleName лучше заводить в отдельных файлах. При этом файлов для поиска может быть более одного.

### Синтаксис правил:  

```
ExampleName: MyExample
SubExamples:
Name: MySubExample
Participants:  
  - Obligatory: Ob1, Ob2, ...  
  - Optional: Op1, Op2, ...  
Items:
  - A: ItemName/Dummy
    (Restriction1)
    (Restriction2) ...  
  - B: ItemName/Dummy
    (Restriction1)
    (Restriction2) ...  
...  
Links:
  - B,A: <link>
  - B,C: <link>
  ...  
Constraints:
    - Order: B, A
...
```


'#' - комментарии  
MyExample - имя группы правил для извлечения примера
MySubExample - имя конкретного правила для извлечения примера

**Items**: составляющая/вершина или другой элемент. Item может быть необходимой для вывода и анализа единицей, но может использоваться и просто для ограничений синтаксической конструкции, в последнем случае (когда не надо выводить в аутпут) напротив ярлыка данного Item (A, B,...) ставим Dummy
Другие типы элементов:
Obligatory -- обязательный элемент, без него пример не будет выделяться  
Optional -- в этом случае пример будет выделяться в отсутствие данного элемента   
Key -- сам пример (этим типом можно не пользоваться)

В каждом правиле должен быть как минимум один обязательный элемент.  

**Links**: типы связи в формате дерева зависимостей согласно нотации UD, см. [сайт UD](https://universaldependencies.org/u/dep/all.html).
Кроме перечисленных там допустима также произвольная связь any (иногда работает некорректно на данном этапе).  

Пример: связь из вершины B в субъектную именную группу A   
```
Links:
  - B,A: nsubj
```

NB! В данном корпусе направление связи -- от предлога к существительному (а не наоборот, как в UD)

#### Синтаксис ограничений на элементы примеров (Restriction)

**ConstituentType**: тип составляющей (NP, VP, ...)

Освновные типы составляющих:
'NP' (именная группа), 'VP' (глагольная группа и предложение), 'AP' (группа прилагательного), 'PP' (предложная группа), 'AdvP' (группа наречия), 'NumP' (группа числительного), 'PartP' (группа причастия)
Вспомогательные составляющие, возглавляемые союзами, междометиями, частицами и т.п.
'CCONJP', 'INTJP', 'Particle', 'SCONJP', 'SYMP', 'XP'

**Morph**: Граммемы в нотации [UD](https://universaldependencies.org/cop/morphology.html), [more](https://universaldependencies.org/u/feat/all.html).  
Все значения пишутся после названия категории и знака "=", без пробелов (например, Variant=Short - для краткой формы прилагательного). Частеречные теги пишутся капслоком отдельно ('VERB'; NB: бытийная связка - AUX).
Кроме этого добавлена информация о переходности, она также задается при поиске отдельно ('tran', 'intran')

**Lex**: нормальная форма, являющаяся вершиной (таких большинство, is_head	true).  

**LexNonHead**: нормальная форма словоформы, не являющейся вершиной (is_head	false). Метка такого лексического ограничения используется всегда, когда словоформа не является ничьей вершиной

**List**: список нормальных форм, выделенный в отдельный файл (лексикон), имя в квадратных скобках совпадает с именем файла типа *.txt - без расширения (NB)

**|** -- логическое "или"
**NOT=>** -- логическое "нет", пока реализовано только для морфологии

Примеры:

```
ConstituentType: NP | AP | VP | AdvP | PP
```

```
Lex: мочь|смочь
```

```
Morph: NOT => Case=Nom
```
