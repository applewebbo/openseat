"""Plain-language, per-release changelog shown on the public ``/novita`` page.

Newest first. Append one entry per release (the ``/release`` skill does this as
part of the workflow). Keep the notes non-technical Italian: 2-4 short bullet
points a board member would understand, condensed from the GitHub release
notes — not the raw commit list.
"""

from datetime import date

RELEASES: list[dict] = [
    {
        "version": "2026.3",
        "date": date(2026, 9, 19),
        "notes": [
            "Le email di conferma (prenotazione e domanda di adesione) "
            "mostrano ora il logo dell'associazione.",
            'Nuova pagina "Novità", raggiungibile dal numero di versione in '
            "fondo al sito, con la cronologia di tutti gli aggiornamenti.",
            "Le date si inseriscono ora digitando giorno/mese/anno, invece "
            "di aprire il calendario nativo del telefono.",
            "Corretti alcuni problemi di leggibilità in modalità scura, "
            "incluso il logo dell'associazione.",
        ],
    },
    {
        "version": "2026.2",
        "date": date(2026, 8, 30),
        "notes": [
            "Gli editor possono creare un nuovo evento direttamente dal sito, "
            "senza passare dall'area admin.",
            "Un nuovo evento propone già il luogo e il modulo di adesione "
            "predefiniti dell'associazione.",
            "La durata dell'evento si indica ora in ore stimate, invece di un "
            "orario di fine preciso.",
            "Le email inviate dal sito mostrano ora il nome dell'associazione "
            "come mittente, con un indirizzo a cui rispondere.",
        ],
    },
    {
        "version": "2026.1.4",
        "date": date(2026, 8, 28),
        "notes": [
            "Il sito segue ora automaticamente il tema chiaro o scuro del "
            "dispositivo di chi lo visita.",
            "Corretto un problema che, in alcuni casi, impediva la "
            "pubblicazione automatica degli aggiornamenti del sito.",
            "Corrette alcune traduzioni italiane mancanti o sbagliate nell'area admin.",
            "Corrette le immagini mancanti sulle schede degli eventi passati.",
        ],
    },
    {
        "version": "2026.1.3",
        "date": date(2026, 8, 28),
        "notes": [
            "Gli editor possono aggiungere una prenotazione a mano dalla "
            "pagina di check-in, partendo da un modulo cartaceo firmato.",
            "La pagina pubblica dell'evento chiede ora \"Hai già partecipato "
            'a uno dei nostri eventi?" invece di "Sei già socio?".',
            "Il libro soci si può importare ed esportare dall'area admin, "
            "nel formato richiesto dal gestionale dell'associazione.",
            "Il modulo di domanda propone ora provincia e comune da un "
            "elenco, e l'indirizzo di un figlio minorenne viene precompilato "
            "con quello del genitore.",
        ],
    },
    {
        "version": "2026.1.2",
        "date": date(2026, 8, 26),
        "notes": [
            "Gli editor possono aprire il check-in di un evento dalla sua "
            "pagina, chiudendo le prenotazioni pubbliche all'ingresso.",
            "Nuova schermata di check-in con ricerca in tempo reale per "
            "confermare o annullare una prenotazione con un tocco.",
            "Si può scegliere quando chiudere le prenotazioni pubbliche: a "
            "mano, a mezzanotte prima dell'evento (ora il comportamento "
            "predefinito) o all'orario di inizio.",
            "Nuova scheda riepilogo con prenotazioni, conferme e fasce d'età.",
        ],
    },
    {
        "version": "2026.1.1",
        "date": date(2026, 8, 23),
        "notes": [
            "Le pagine di accesso, registrazione e gestione password hanno "
            "ora il logo e i colori dell'associazione, con una nuova pagina "
            "Account per email e password.",
            "I nuovi account restano in attesa di approvazione prima di "
            "poter accedere.",
            "I messaggi del sito appaiono ora come notifiche che si chiudono da sole.",
            "Corretto il layout della scheda eventi sugli schermi piccoli.",
        ],
    },
    {
        "version": "2026.1",
        "date": date(2026, 8, 22),
        "notes": [
            "Prima versione di OpenSeat: domanda di adesione online, "
            "prenotazione agli eventi e libro soci con esportazione CSV.",
            "Ci si può iscrivere per sé, per un figlio minorenne o per una "
            "persona di cui si è tutori.",
            "Le prenotazioni si confermano o si annullano dalla mail "
            "ricevuta, senza bisogno di un account.",
            "L'area admin mostra già nome, logo e colori dell'associazione.",
        ],
    },
]
