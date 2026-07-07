# Набор данных для оценки скорости модулей обработки PDF

## Что тестируется

1. Предобработка
    1. бинаризация (binarize)
    2. исправление ориентации страницы (orient)
    3. исправление поворота < 45° (skew)
2. Обработка
    1. детекция и распознавание таблиц (table)
    2. детекция изображений (layout)
    3. распознавание текста (ocr)

## Документы

| Тип                       | Количество документов      | Количество страниц     | Описание                                      |
|---------------------------|----------------------------|------------------------|-----------------------------------------------|
| binarize                  | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | сложный/цветной фон (real)                    |
| orient                    | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | повороты кратно 90° (real)                    |
| skew                      | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | повороты < 45° (real)                         |
| ocr                       | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | только текст (gen)                            |
| table                     | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | только таблицы на странице (gen)              |
| layout                    | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | только картинки на странице (gen)             |
| ocr + table + layout      | 30 каждого вида            | 1, 5, 10, 25, 50, 100  | текст + таблицы + картинки (gen)              |
| ocr + layout              | 35 каждого вида            | 1, 5, 10, 25, 50, 100  | текст + картинки (real)                       |
| ocr + table               | 30 (1-50 стр), 1 (100 стр) | 1, 5, 10, 25, 50, 100  | текст + таблицы с границами (real)            |
| ocr + hard table          | 23 каждого вида            | 1, 5, 10, 25, 50, 100  | текст + сложные таблицы (real)                |
| ocr + layout + table      | 60 (1-50 стр), 2 (100 стр) | 1, 5, 10, 25, 50, 100  | текст + картинки + таблицы с границами (real) |
| ocr + layout + hard table | 7 каждого вида             | 1, 5, 10, 25, 50, 100  | текст + картинки + сложные таблицы (real)     |


### Binarize

Rosatom docs (2026) (`rosatom_docs`):

1. DAE (India) Annual Report 2020-21.pdf
2. DAE (India) Annual Report 2021-22.pdf
3. DAE (India) Annual Report 2022-23.pdf
4. DAE (India) Annual Report 2023-24.pdf
5. NNSA Annual Report 2020.pdf
6. NNSA Annual Report 2021.pdf
7. NNSA Annual Report 2022.pdf
8. NNSA Annual Report 2023.pdf
9. NNSA Annual Report 2024.pdf
10. World Nuclear Industry Status Report 2024.pdf
11. World Nuclear Industry Status Report 2025.pdf

Fintoc 2022 (spanish) (`fintoc/sp`):

12. 7-AENA_Informe_Anual_2015.pdf
13. 12-Endesa_Informe_de_Actividades_2016.pdf
14. 12-Endesa_Informe_de_Actividades_2017.pdf
15. 14-Ferrovial_Informe_Anual_2014.pdf
16. 15-Bankia_Informe_ Anual_2015.pdf
17. 15-Bankia_Informe_Anual_2015.pdf
18. 15-Bankia_Informe_Anual_2017.pdf
19. 20-Mapfre_Informe_Integrado_2017.pdf
20. 26-CatalanaOccidente_Informe_Anual_2016.pdf
21. 33-CIEAutomotive_Informe_Anual_2015.pdf
22. 33-CIEAutomotive_Informe_Anual_2016.pdf
23. 38-Alba_Informe_Anual_2015.pdf
24. 40-Logista_Informe_Anual_2017.pdf
25. 82-Pharma_Mar_Informe_Anual_2016.pdf
26. 115-Abengoa_Informe_Anual_2016.pdf
27. 114-Abengoa_Informe Anual_2017.pdf
28. 60-CAF_Informe_Anual_2014.pdf
29. 60-CAF_Informe_Anual_2015.pdf
30. 72-Realia_Informe_Anual_2017.pdf

### Orient / skew

Rosatom docs (2025) (`pdf_china`):

1. CIAE_Annual Report_2014en.pdf
2. CIAE_Annual Report_2016en.pdf
3. CIAE_Annual Report_2012en.pdf
4. CIAE_Annual Report_2017en.pdf
5. CIAE_Annual Report_2015en.pdf
6. CIAE_Annual Report_2011en.pdf
7. CIAE_Annual Report_2013en.pdf
8. CIAE_Annual Report_2020en.pdf
9. CIAE_Annual Report_2019en.pdf
10. CIAE_Annual Report_2018en.pdf

Fintoc 2022 (english) (`fintoc/en`):

11. LU0705072691-LU0705072345-LU0705072188_English_2015_RAM-LUX-Long-Sh-EmergingMarktesEq-.pdf
12. HSBC_Global_Investment_Funds_2017_X_P_X_A.pdf
13. LU0424369923-LU0424369766-LU0114314536-LU0063949068-LU0686792812-LU0061927850-LU0686794354_English_2013_ManConvertibles.pdf
14. LU0800341645-LU0800341132-LU0800341991-LU0800341215-LU0800341058-LU0800341488-LU0800341306_English_2012_FranklinBrazilOpportunities.pdf
15. FU_BF097_EN_2019-05-13_a5585d06-b4df-4b1e-bf30-3c1b5615cf74.pdf
16. LU1057354992_English_2016_EchiquierEuropeanBondsAEUR.pdf
17. LU0589944569-LU0348788117-LU1156968403-LU1254141333-LU0348791418_English_2011_AllianzEm-AsiaEq-.pdf
18. LU0462973008-LU0512124362_English_2015_DNCAInvestMiura.pdf
19. LU0309082104-LU0309082799-LU0309082369_English_2015_DNCAInvest-Infrastructures.pdf
20. LU0949250459-LU0645132902-LU0229041164-LU0390138864-LU0188151251-LU0543370943-LU0195951883-LU0152904719-LU0188151095-LU0543370513-LU0889566138-LU0229948244-LU0229948087-LU0122613572-LU0229949648_English_2012_Franklin.pdf
21. Prospectus-2016-02-01.pdf
22. LU0641972152-LU0641972079_English_2015_DBPWMIGlobalAllocationTracker-.pdf
23. LU0289452210_English_2015_DBPWMIIGISUSEquityPortfolioB.pdf
24. LU0178440839-LU0178439401-LU0178439310-LU0178439666_English_2012_AllianzBestSty-Eu-Eq-.pdf
25. LU0375979613-LU0375979290_English_2015_GISDyn-ControlPFCo.pdf
26. LU0734574329-LU0734574162-LU0333227550-LU0333226230-LU0571576585-LU1039626509-LU0333227394-LU0333226826-LU0734574246-LU0333227048_English_2015_ML.pdf
27. LU0881817786-LU0881818081-LU0881817430-LU0881817190_English_2014_OddoBondsHighYieldEurope.pdf
28. LU0575375588-LU0493852429-LU0261074230-LU0640453774-LU0860716223-LU0575374698-LU0493865678-LU0860715415-LU0493851454-LU0160485420-LU0493867534-LU0860716140-LU0953070868-LU0956110364-LU0688432862_English_2016_AshmoreS.pdf
29. LU1252823262-LU0482498846-LU0482498762-LU0955861710-LU0955867758-LU0955867915-LU0432616810-LU0607521506-LU0955867832-LU0482498176-LU0955861983-LU0955861801-LU0432616901_English_2013_InvescoBalanced-RiskAlloc-.pdf
30. Lombard_Odier_Funds_2014_X_P_X_X.pdf


### Table

#### gen_tables

Датасет из PDF, в которых на каждой странице только таблицы.
Данные разбиты на 3 группы: 1, 2 или 3 таблицы на странице.

PDF сгенерированы скриптом `gen_tables.py`.
Текстовое наполнение генерируется случайно (слова из фиксированного множества + числа/даты).

#### real_mixed/table

Датасет из реальных PDF (`fintoc/en_fr`), в которых на каждой странице таблицы + текст.
Таблицы с границами - определены с помощью dedoc (dedoc мог ошибаться).
Документы 1-50 страниц получены случайным выбором страниц из одного 100-страничного документа.


#### real_mixed/hard_table

Датасет из реальных PDF (`rosatom_docs`, `pdf_china`, `fintoc/en`, `fintoc/sp`), в которых на каждой странице таблицы + текст.
Таблицы любые - определены с помощью layout analysis модели от docling (модель могла ошибаться).


### OCR

#### gen_texts

Датасет из PDF, в которых на каждой странице только текст.
Данные разбиты на 2 группы: страницы с небольшим/большим количеством текста.

PDF сгенерированы скриптом `gen_text.py`.
Используются тексты из [датасета](https://www.kaggle.com/datasets/shivamkushwaha/bbc-full-text-document-classification).


### Layout

#### gen_images

Датасет из PDF, в которых на каждой странице только картинки.
Данные разбиты на 3 группы: 1, 2 или 3 картинки на странице.

PDF сгенерированы скриптом `gen_images.py`.
Используются изображения из [датасета](https://www.kaggle.com/datasets/bhavikjikadara/dog-and-cat-classification-dataset?resource=download)

#### real_mixed/image

Датасет из реальных PDF (`rosatom_docs`, `pdf_china`, `fintoc/en`, `fintoc/sp`), в которых на каждой странице картинки + текст.
Картинки определены с помощью layout analysis модели от docling (модель могла ошибаться).


### Mixed

#### gen_mixed

Датасет из PDF, в которых на каждой странице 1 картинка, 1 таблица и 1-2 текстовых блока.

PDF сгенерированы скриптом `gen_mixed.py`.
Тексты и изображения взяты из тех же источников, что и для `gen_texts`, `gen_images`.

#### real_mixed/image_table

Датасет из реальных PDF (`fintoc/en_fr`), в которых на каждой странице таблицы + картинки + текст.
Таблицы с границами - определены с помощью dedoc (dedoc мог ошибаться).
Картинки определены с помощью layout analysis модели от docling (модель могла ошибаться).
Документы 1-50 страниц получены случайным выбором страниц из двух 100-страничных документов.


#### real_mixed/image_hard_table

Датасет из реальных PDF (`rosatom_docs`, `pdf_china`, `fintoc/en`, `fintoc/sp`), в которых на каждой странице таблицы + картинки + текст.
Таблицы и картинки определены с помощью layout analysis модели от docling (модель могла ошибаться).
