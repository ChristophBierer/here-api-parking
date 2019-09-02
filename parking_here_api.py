"""
    Dieses Programm hat zwei verschiedene Arten die Oeffnungszeiten aus dem Response der API zu lesen.
    Der einfache Weg waere ueber die strukturierten Informationen zu den Oeffnungszeiten.
        Diese liefern zum aktuellen Tag die Uhrzeit der Oeffnung und die Dauer der Oeffnungszeit.
        Aus diesen beiden Informationen laesst sich somit auch die Uhrzeit der Schliessung ermitteln.
        Ist jedoch die Uhrzeit der Schliessung 24 Uhr, laesst sich anhand dieser Informationen nicht ermitteln,
        ob das Parkhaus nach 0 Uhr immer noch geoeffnet ist. Sind die Oeffnungszeiten fuer jeden Tag die selben,
        stellt dies zwar noch kein Problem dar. Gibt es jedoch unterschiedliche Oeffnungszeiten zu unterschiedlichen
        Tagen, koennen mit den strukturierten Informationen der Oeffnungszeiten nicht alle noetigen Informationen
        gewonnen werden. Der erste Weg ist daher nur zu verwenden, im Falle man am selben Tag das Parkhaus noch
        verlassen moechte. Andernfalls liefert es bei entsprechenden Oeffnungszeiten, die nach  0 Uhr weiterhin
        geoeffnet sind, ein falsches Ergebnis!!
    Daher wurde ein zweiter Weg gewaehlt, mit dem auch alle Sonderfaelle abgedeckt werden koennen. Dieser verwendet
    das text-Feld, welches normalerweise jedoch vermutlich als label in einer Webseite verwendet wird. Aber es
    stehen hier alle Informationen, die benoetigt werden, im Falle beispielsweise ein Parkhaus nach 24 Uhr nicht
    schliesst, aber eine andere Oeffnungszeit am Folgetag hat.
"""


import requests
import sys
from datetime import datetime, time, timedelta

#################################################################
##################  appid und appcode eintragen! ################
appid = "" # Hier muss die appid eingetragen werden
appcode = "" # Hier muss der appcode eingetragen werden


def testStructured():
    """ testen der opening hours mit den structured Daten der Oeffnungszeiten """
    # aktuelle Zeit abfragen
    cur_time = datetime.now()
    # aktuelle Zeit ins richtige Format packen
    c_time_str = cur_time.strftime("%d.%m.%Y %H:%M:%S")
    # gewuenschte Puffer-Zeit
    buffer_time = 2200

    print("Die Ergebnisse der strukturierten Informationen sind: ")
    # Aufrufen der Funktionen um Oeffnungszeiten fuer Parameter zu pruefen
    analyzeStructured(48.77526, 9.17366, c_time_str, buffer_time)
    analyzeStructured(52.51644, 13.39326, c_time_str, buffer_time)
    analyzeStructured(52.51103, 13.38867, c_time_str, buffer_time)


def testText():
    """ testen der Oeffnungszeiten mit dem Textfeld der Oeffnungszeiten """
    # aktuelle Zeit abfragen
    cur_time = datetime.now()
    # aktuelle Zeit ins richtige Format packen
    c_time_str = cur_time.strftime("%d.%m.%Y %H:%M:%S")
    # gewuenschte Puffer Zeit
    buffer_time = 200

    print("Die Ergebnisse der text-Feld Informationen sind: ")
    # Aufrufen der Funktionen um Oeffnungszeiten fuer Parameter zu pruefen
    analyzeText(48.77526, 9.17366, c_time_str, buffer_time)
    analyzeText(52.51644, 13.39326, c_time_str, buffer_time)
    analyzeText(52.51103, 13.38867, c_time_str, buffer_time)


# Daten der Oeffnungszeiten abfragen
def getData(lat, lng):
    """
    Daten der Oeffnungszeiten abfragen.
    Funktion gibt Oeffnungszeiten im json-Format zurueck.
    """
    try:
        url = """https://places.cit.api.here.com/places/v1/discover/search?\
        app_id=%s\
        &app_code=%s&\
        at=%s,%s&\
        q=parking&\
        pretty=true"""%(appid,appcode,lat,lng)
        url = url.replace("\n", "").replace(" ", "")

        req = requests.get(url)
        json_text = req.json()

        openHours = json_text["results"]["items"][0]["openingHours"]

        return openHours
    except Exception as err:
        print("error in downloading data")
        print(err)


def analyzeText(lat, lng, time, buffer):
    """
    verwendet das text-Feld, um die Oeffnungszeiten zu erhalten
    """
    try:
        # Daten abfragen
        data = getData(lat, lng)
        # text-Feld mit Oeffnungszeiten Variable zuweisen
        text = data["text"]

        # teilt datetime in Datum und Zeit
        time_split = time.split(" ")
        # teilt Datum in Tag, Monat und Jahr
        cur_date = time_split[0].split(".")
        # teilt Zeit in Stunde, Minute und Sekunde
        cur_time = time_split[1].split(":")
        # erstellt eine Datetime
        date = datetime(int(cur_date[2]), int(cur_date[1]), int(cur_date[0]), int(cur_time[0]), int(cur_time[1]),
                        int(cur_time[2]))
        # generiert Wochentag im Kurzformat
        weekday = date.strftime("%a")
        # aus Minuten und Stunden wird ein timedelta generiert
        deltaTime = timedelta(hours=int(cur_time[0]), minutes=int(cur_time[1]))

        # findTime soll Oeffnungszeiten des entsprechenden Wochentages zurueck liefern
        res_findTime = findTime(text, date.weekday())

        # falls das Parkhaus im Moment geoeffnet ist, soll es die Zeit ermitteln die es noch geoeffnet ist
        if res_findTime["open"] == True:
            # berechnet die noch geoeffnete Zeit
            avail_time = calcDiffOfDeltas(deltaTime, res_findTime["end_time"])

            # falls das Parkhaus bis 24 Uhr geoeffnet ist, ist es moeglich, dass es um 24 Uhr nicht schliesst,
            # sondern nach 0 Uhr weiterhin geoeffnet ist.
            # Dies soll geprueft werden, da ansonsten dem Fahrer angezeigt werden wuerde, dass das Parkhaus schliesst,
            # obwohl es moeglocherweise durchgehend geoeffnet ist
            if res_findTime["end_time"].days == 1:
                # ermittelt die noch verfuegbare Zeit im Fall Parkhaus nach 0 Uhr noch geoeffnet ist
                avail_time = specialCaseOpenUntil24h(text, day2num(weekday), avail_time, buffer)

            # ruft Funktion auf, die das Ergebnis printet
            printResult(avail_time, buffer)
        else:
            print("Das Parkhaus ist geschlossen im Moment!")
    except Exception as err:
        print("Error in analyzing the text opening hours!")


def findTime(text, weekday):
    """
    Ermittelt aus dem Text der Oeffnungszeiten, die Oeffnungszeiten fuer den entsprechend gewuenschten Tag.
    Es ist entscheidend, dass die Struktur des Textfeldes immer die selbe ist!

    :param text: text der Oeffnungszeiten
    :param weekday: Wochentag als Integer. Mon=0, Tue=1, usw.
    :return: Gibt ein dict mit open=true, Oeffnungs- und Schliesszeit zurueck, im Falle es geoeffnet ist.
                Sonst nur open=False
    """
    try:
        # falls verschiedene Oeffnugszeiten an verschiedenen Tagen, sind diese mit <br/>, getrennt.
        # Daher ist <br/> das Spalt-Element. Dieses Textfeld wird daher in der Regel als ein Label in Webseiten verwendet.
        diff = text.split("<br/>")
        time_start = ""
        time_end = ""
        # jedes Element kann ein einzelner Tag, ein Wochenabschnitt oder eine ganze Woche sein
        # je nachdem ob verschiedene Oeffnungszeiten an verschiedenen Tagen
        for el in diff:
            # Element wird in Wochentag, Oeffnungszeit und Schliesszeit gespaltet
            sp = el.split(" ")
            # erstes Element ist immer die Definition des Wochentages
            days = sp[0]
            # falls ein '-' enthalten ist, ist es kein einzelner Tag, sondern ein Abschnitt
            if "-" in days:
                # Spaltet in Tag des Beginns und den des Ende des Abschnittes
                days_split = days.split("-")
                # ermittelt Tag des Startes des Abschnittes und wandelt diesen in eine entsprechende Integer Zahl um
                days_start = day2num(str(days_split[0])[:3])
                # ermittelt Tag des Endes des Abschnittes und wandelt diesen in eine entsprechende Integer Zahl um
                days_end = day2num(str(days_split[1])[:3])
                # prueft ob gewuenschter Tag in diesem Abschnitt,
                # Falls ja, wird Oeffnungs- und Schliesszeit den Variablen zugewiesen
                if (days_start <= weekday) and (days_end >= weekday):
                    time_start = sp[1]
                    time_end = sp[3]
            else:
                # falls kein '-' enthalten ist, handelt es sich um einen einzelnen Tag
                # daher wird nur geprueft ob gewuenschter Wochentag, dieser einzelne Wochentag ist
                # Falls ja, wird Oeffnungs- und Schliesszeit den Variablen zugewiesen
                if day2num(days[:3]) == weekday:
                    time_start = sp[1]
                    time_end = sp[3]

        # falls time_start nicht mehr leer ist, bedeutet dies, dass Oeffnungszeiten fuer diesen Tag gefunden wurden
        # diese werden in einem dict returned
        if time_start != "":
            res = {"open": True, "start_time": texttime2delta(time_start), "end_time": texttime2delta(time_end)}
            return res
        else:
            # im Falle time_start leer ist, wurden keinen Oeffnungszeiten fuer diesen Tag gefunden.
            # Dies bedeutet, dass das Parkhaus an diesem Tag geschlossen ist.
            res = {"open": False}
            return res
    except Exception as err:
        print("Error occured: ")
        print(err)
        sys.exit()


def specialCaseOpenUntil24h(text, weekday, timeDay0, buffer):
    """
    Prueft, im Falle das Parkhaus bis 24 Uhr geoeffnet ist, ob dieses nach 0 Uhr weiterhin geoeffnet ist und
    berechnet nicht moegliche Zeit in der hier geparkt werden kann, bevor es schliesst

    :param text: text der Oeffnungszeiten
    :param weekday: Wochentag fuer den geprueft wird [als Integer]
    :param timeDay0: Zeit die bis 24 Uhr verfuegbar ist [in Minuten]
    :param buffer: gewuenschte Pufferzeit [in Minuten]
    :return: gibt es verfuegbare Zeit zurueck, bis Parkhaus schliesst
    """
    try:
        isopen24 = True
        counter = 0
        # Zeit, die Parkhaus an Folgetage(n) geoeffnet ist. Zunaechst wird Zeit vom eigentlichen Tag zugewiesen, als bisher
        # verfuegbare Zeit
        extra_min = timeDay0
        # nextday ist spaeter der Folgetag. Zunaechst wird der Starttag zugewiesen
        nextday = weekday
        # Schleife kann beendet werden, im Falle
        # 1. Das Parkhaus am geprueften Tag nicht 24h geoffnet ist, da dann eine Schliesszeit verfuegbar ist und
        #          Verweildauer berechnet werden kann
        # 2. der counter 8 erreicht, da dann fuer eine gesamte Woche festgestellt wurde, dass es immer 24h geoffnet ist
        # 3. die geoeffnete Zeit den gewuenschten Puffer ueberschreitet, da dadurch ohnehin "ok" geprintet werden kann
        while (isopen24 == True) and (counter < 8) and (extra_min < buffer):
            # zaehlt einen Wochentag hoch
            nextday += 1
            # falls 7 erreicht wird, ist dies wieder Montag, daher --> 0
            if nextday == 7:
                nextday = 0
            # nutzt bereits abgefragtes text-Feld um Oeffnungszeiten fuer den Folgetag zu pruefen
            res = findTime(text, nextday)
            # prueft ob ueberhaupt geoeffnet
            if res["open"] == True:
                # und um 0 Uhr geoeffnet
                if res["start_time"].seconds == 0:
                    # und bis 24 Uhr geoeffnet
                    if res["end_time"].days == 1:
                        # ein gesanmter Tag kann addiert werden
                        extra_min += 1440
                    else:
                        # falls nicht bis 24 Uhr geoeffnet, wird Zeit addiert bis es an diesem Tag schliesst
                        extra_delta = res["end_time"] - res["start_time"]
                        extra_min += int(extra_delta.seconds / 60)
                        # da Parkhaus an diesem Tag definitiv schliesst, ist isopen24 nicht mehr wahr und
                        # Folgetag muss nicht geprueft werden
                        isopen24 = False
                else:
                    # oeffnet nicht um 0 Uhr am Folgetag, daher hat es um 24 Uhr geschlossen
                    isopen24 = False
            else:
                # ist am Folgetag nicht geoeffnet, daher hat es um 24 Uhr geschlossen
                isopen24 = False
            # counter wird einen Tag hochgeszaehlt
            counter += 1
            # falls counter 8 erreicht, wurde festgestellt, dass Parkhaus jeden Tag in der Woche 24h geoffnet ist
            # --> unendlich geoffnet
            if counter == 8:
                extra_min = float("inf")

        return extra_min
    except Exception as err:
        print("An error occured:")
        print(err)
        sys.exit()


def texttime2delta(time):
    """ wandelt Uhrzeit im Format 'hh:mm' in timedelta um """
    time_split = time.split(":")
    delta = timedelta(hours=int(time_split[0]), minutes=int(time_split[1]))
    return delta


def day2num(day):
    """ weisst Wochentag eine entsprechende Integer-Zahl zu und returned diese. Mon=0, Tue=1, usw.  """
    num = -1
    if day == "Mon":
        num = 0
    elif day == "Tue":
        num = 1
    elif day == "Wed":
        num = 2
    elif day == "Thu":
        num = 3
    elif day == "Fri":
        num = 4
    elif day == "Sat":
        num = 5
    elif day == "Sun":
        num = 6
    else:
        num = -20

    # falls
    return num


def calcDiffOfDeltas(cur_time, end):
    """ berechnet die Differenz aus 2 timedeltas und gibt die Differenz in Minuten zurueck """
    diff = end - cur_time
    diff_inMin = int(diff.seconds / 60)

    return diff_inMin


def printResult(diff_inMin, buffer):
    """
    berechnet ob Puffer Zeit ausreicht und printet das Ergebnis.
    Falls ja, wird 'ok' ausgegeben.
    Falls nein, wird ausgegeben in wievielen Minuten das Parkhaus schliesst
    """

    isEnoughTime = diff_inMin - buffer

    if isEnoughTime >= 0:
        print("ok")
    else:
        print("Das Parkhaus schliesst in: " + str(diff_inMin) + " Minuten!")


def getStructuredData(lat, lng):
    """ liesst die strukturierten Informationen ueber die Oeffnungszeiten des Parkhauses aus """
    try:
        # fraegt Oeffnungszeiten ab
        data = getData(lat, lng)
        # is das Parkhaus im Moment geoeffnet
        isOpen = data["isOpen"]

        # ab wann ist das Parkhaus geoeffnet (Info zu dem aktuellen Tag)
        start = data["structured"][0]["start"]
        # wie lange ist das Parkhaus geoeffnet (Info zu diesem Tag)
        dur = data["structured"][0]["duration"]
        # Zeit zu der das Parkhaus scliesst, berechnet aus start und duration
        # getrennt berechnet fuer Stunde in Minute
        closeHour = int(start[1:3]) + int(dur[2:4])
        closeMin = int(start[3:5]) + int(dur[5:7])

        return closeHour, closeMin, isOpen
    except Exception as err:
        # Falls in diesem Bereich ein Fehler entsteht, wird das gesamte Programm abgebrochen,
        # da dann kein Ergebnis berechnet werden kann
        print("Error. Structured data wrong!")
        print(err)
        sys.exit()


def analyzeStructured(lat, lng, tm, buffer):
    """ Analysieren der Oeffnungszeiten, basierend auf den Struktuerierten Daten der API """
    try:
        # spaltet datetime in Datum und Zeit. An Stelle 1 des Arrays ist dann die Zeit.
        # Zeit wird gespaltet in Stunden, Minuten und Sekunden
        time_split = tm.split(" ")
        cur_time = time_split[1].split(":")
        # Stunden und Minuten werden verwendet um ein timedelta zu erstellen mit der aktuellen Zeit
        cur_timedelta = timedelta(hours=int(cur_time[0]), minutes=int(cur_time[1]))

        # ruft die Funktion auf, um strukturierte Daten der Oeffnungszeiten zu bekommen
        closeH, closeM, isopen = getStructuredData(lat, lng)
        # falls Parkhaus aktuell geoeffnet
        if isopen == True:
            # erstellt ein timedelta der Uhrzeit der Schliessung
            timedeltaClose = timedelta(hours=int(closeH), minutes=int(closeM))
            # berechnet Differenz aus Schliessung des Parkhauses und aktueller Zeit
            diff_inMin = calcDiffOfDeltas(cur_timedelta, timedeltaClose)
            # ruft Funktion auf, um Ergebnis auszugegeben, basierend auf Differenz und Puffer
            printResult(diff_inMin, buffer)
        else:
            print("Das Parkhaus ist im Moment geschlossen!")

    except Exception as err:
        print("Error in analysing opening hours!")


if __name__ == '__main__':
    # testStructured()
    testText()


