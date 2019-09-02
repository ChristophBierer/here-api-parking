# here-api-parking
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
