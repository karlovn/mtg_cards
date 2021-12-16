import pandas as pd
import json
import requests
import os.path

# Функция получает список выпусков карты на разных языках. В реализации это список кортежей cardinfo['foreignData']. Возвращает строку с именем
def getRuName(data = []):
    # Идём в цикле по списку кортежей. В каждом элементе ищем русский язык. Как только нашли, возвращаем русское имя в виде строки
    for dic in data:
        if dic['language'] == 'Russian':
            return dic['name']

# Функция для получения словаря с кодами сетов. Принимает список названий сетов, возвращает словарь {}
def getsetcodes(setlst = []):
    print('Получен список имён сетов. Создаю словарь кодов...')
    # Создаем копию полученного на входе списка (чтобы не портить исходный. Он ещё пригодится)
    setlist = setlst[:]
    # Создаем пустой словарь с индексами по именам сетов из списка
    codes = dict.fromkeys(setlist)

    if os.path.isfile("./resources/SetList.json"):
        print("Файл SetList.json найден, формирую словарь.")
    else:
        print("Файл SetList.json не найден.")
        url = "https://www.mtgjson.com/api/v5/SetList.json"
        print(f"Начинаю скачивание {url}...")
        jfile = requests.get(url)
        print('Файл SetList.json получен!')
        with open("./resources/SetList.json", "w", encoding='utf-8') as wr_file:
            wr_file.write(jfile.text)
        print('Файл SetList.json записан в папку resources!')

    # В sets_json кладём содержимое JSON-a с перечнем сетов. Теперь это список словарей
    with open("./resources/SetList.json", "r", encoding='utf-8') as read_file:
        sets_json = json.load(read_file)

    for oneset in sets_json['data']:
        # Если в списке не осталось значений, прервём цикл, возвращая готовый словарь
        if setlist:
            if oneset['name'] in setlist:
                codes[oneset['name']] = oneset['code']
                if codes[oneset['name']] == 'CON':
                    codes[oneset['name']] = 'CON_' # В Windows нельзя создать файл CON.json, а сет с таким кодом есть
                                                   # И в источнике страница .../CON редиректит на .../CON_
                setlist.remove(oneset['name'])
        else:
            print('Словарь кодов сетов создан:')
            print(codes)
            print()
            return(codes)
    print('Словарь кодов сетов создан:')
    print(codes)
    print()
    print('Остались незадействованные сеты:')
    print(setlist)
    print()
    return(codes)

# Функция получает код сета и имя директории. Возвращает путь к файлу.
def downloadsetfile(setcd = '', dirc = './'):
    # Если имя директории не оканчивается /, добавляем этот слешик в конец
    if dirc[-1:] != '/': dirc = f"{dirc}/"
    # Имя конечного файла:
    destfile = f"{dirc}{setcd}.json"
    # Проверяем наличие файла. Если есть, сообщаем. Если нет, выкачиваем и сообщаем.
    if os.path.isfile(destfile):
        print(f"Файл {destfile} уже существует")
        return(destfile)
    else:
        url = f"https://www.mtgjson.com/api/v5/{setcd}.json"
        print(f"Начинаю скачивание {url}...")
        jfile = requests.get(url)
        print(f'Файл {setcd} получен!')
        with open(destfile, "w", encoding='utf-8') as wr_file:
            wr_file.write(jfile.text)
        print(f'Файл {setcd}.json записан в папку resources/setfiles!')
        return(destfile)




def main():
    # allcards - DataFrame со всеми картами из списка
    allcards = pd.read_excel("./resources/example.xlsx") # Имя исходного файла задано хардкодом

    # setnames - список сетов в файле
    setnames = list(allcards["set"].unique())
    # setnames.remove('Promo') # Сета Promo точно нет, поначалу у некоторых карт был указан такой сет, в example его нет. Оставил строку, она не мешает

    # setcodes - получаем словарь кодов сетов
    setcodes = getsetcodes(setnames)

    # Запускаем цикл по именам сетов. setname - имя сета
    for setname in setnames:
        # Проверяем наличие файла с картами текущего сета и открываем его. Если файла нет - предварительно выкачиваем.
        # Это всё реализовано в функции, так что просто получаем из неё имя файла
        cards_file = downloadsetfile(setcd = setcodes[setname], dirc = './resources/setfiles')

        # Открываем JSON с картами текущего сета, кладём в список словарей cards
        with open(cards_file, "r", encoding='utf-8') as read_file:
            cards = json.load(read_file)['data']['cards'] #для работы со старой версией 7ED нужно убрать ['data'] в этой строке
        
        # Идём в цикле по списку cards, обрабатывая каждую найденную карту (довольно топорно, зато код полегче)
        for cardinfo in cards:
            # Вытаскиваем русское имя
            rusname = getRuName(cardinfo['foreignData'])

            # Если в списке моих карт нашлась строка, где сет = текущий сет и русское имя = текущее ру имя...
            if not allcards[(allcards.runame == rusname)&(allcards.set == setname)].empty:
                # Находим индекс этой строки
                ind = allcards[(allcards.runame == rusname)&(allcards.set == setname)].index.tolist()

                # Ставим язык в этой строке = 'Russian' и вписываем английское имя
                allcards.loc[ind, "lang"] = 'Russian'
                allcards.loc[ind, "enname"] = cardinfo["name"]
            
            # Ещё раз ищем строку, теперь по англ имени + сету. Для русских карт - после предыдущего ифа англ имя уже проставлено
            if not allcards[(allcards.enname == cardinfo["name"])&(allcards.set == setname)].empty:
                # Снова пилим индекс...
                ind = allcards[(allcards.enname == cardinfo["name"])&(allcards.set == setname)].index.tolist()

                # Вот здесь уже нужна проверка, заполнен ли язык. А ещё на фойлу надо будет проверять.
                for indd in ind:
                    if str(allcards.at[indd, "lang"]) == 'nan':
                        allcards.loc[indd, "lang"] = 'English' 
                
                # Блок ниже более не актуален, т.к. в json-ах из источника теперь отсутствует информация о ценах.
                # Оставил для истории.

                # # Вот и проверка на фойлу. Это чтобы цену подтянуть
                # for indd in ind:
                #     if str(allcards.at[indd, "foil"]) == 'Y':
                #         prcdata = cardinfo['prices']['paperFoil']
                #         try:
                #             key = sorted(prcdata)[0]
                #             prc = prcdata[key]
                #             allcards.at[indd, "price"] = prc
                #         except IndexError:
                #             print(f'Не вижу цен у карты {cardinfo["name"]}')
                #     else:
                #         prcdata = cardinfo['prices']['paper']
                #         try:
                #             key = sorted(prcdata)[0]
                #             prc = prcdata[key]
                #             allcards.at[indd, "price"] = prc
                #         except IndexError:
                #             print(f'Не вижу цен у карты {cardinfo["name"]}')
                    

                # Ну и рарность проставляем
                allcards.loc[ind, "rarity"] = cardinfo["rarity"]
        # На этом заканчивается цикл по определенному сету, и мы переходим к следующему сету
        print(f"Сет {setname} успешно обработан!")

    # А здесь заканчивается цикл по всем сетам
    print("Все сеты обработаны, перехожу к записи в файл...")

    # Записываем наш полученный датафрейм в новый эксель-файл
    allcards.to_excel("./resources/result.xlsx", index=False)
    print("Файл result.xlsx успешно записан!")


if __name__ == "__main__":
    main()

