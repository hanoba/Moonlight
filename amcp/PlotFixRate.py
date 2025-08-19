import matplotlib.pyplot as plt

def Plot(x_achse, werte):
    # Optional: x-Achse (Index-Werte), sonst nimmt Matplotlib 0,1,2,...
    #x_achse = list(range(len(werte)))
    
    # Kurve zeichnen
    #plt.plot(x_achse, werte, marker='o', linestyle='-', color='blue', label='Werteverlauf')
    plt.plot(x_achse, werte, marker='o', linestyle='-', color='blue')
    
    # Achsenbeschriftung und Titel
    plt.xlabel('Time in hours')
    plt.ylabel('FIX Rate in %')
    plt.title(f"{date}: FIX Rate over time")
    plt.grid(True)
    #plt.legend()
    
    # Plot anzeigen
    plt.show()



# Dateiname (anpassen oder per Eingabe holen)
date = "2025-07-28"
dateiname = f"/DriveX/tmp/{date}-amcp-log.txt"

x = []
cnt = 0
maxcnt = 12*30  # averaging over 30 minutes
wert = 0
th = []     # Zeit in Stunden
uhrzeit = []

# Datei zeilenweise öffnen und lesen
with open(dateiname, "r", encoding="utf-8") as file:
    for zeilennummer, zeile in enumerate(file, start=1):
        zeile = zeile.strip()  # Entfernt Zeilenumbruch und Leerzeichen
        if not zeile:
            continue  # Leere Zeilen überspringen

        felder = zeile.split()  # Standardmäßig nach beliebigen Leerzeichen aufteilen

        if len(felder) > 16 and felder[1][0]==":":
            if felder[15][:3] == "FIX": wert += 1

            cnt += 1
            if cnt == maxcnt:
                u = felder[0][0:5]
                t = int(felder[0][0:2]) + int(felder[0][3:5])/60
                uhrzeit.append(u)
                w = int(wert/maxcnt*100+0.5)
                x.append(w)
                th.append(t)
                cnt = 0
                wert = 0
for i in range(len(x)):
    print(f"{uhrzeit[i]}:  {x[i]}%")
print(len(x))
Plot(th,x)
