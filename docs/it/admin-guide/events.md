# Eventi

Ogni iniziativa che l'associazione organizza — una gita, una giornata porte
aperte, un laboratorio — è un **evento** (`Admin → Eventi e prenotazioni →
Eventi`), con una propria pagina pubblica e un proprio modulo di
prenotazione.

![Il form di creazione/modifica di un evento](../assets/screenshots/admin-event-form.png)

## Campi principali

- **Titolo** e **descrizione** (con editor ricco) — genera automaticamente
  anche lo slug della pagina pubblica
- **Luogo**, **data e ora di inizio**, **durata stimata** in ore
- **Immagine** — un'immagine orizzontale di almeno 1200 px; la versione
  quadrata, usata nelle anteprime, viene ritagliata automaticamente
- **Modulo di adesione** — quale modulo compila chi prenota; se lasciato
  vuoto, si usa il modulo predefinito dell'associazione
- **Pubblicato** — se disattivato, l'evento non compare sulla home page né è
  raggiungibile dal link diretto
- **Costo suggerito** — non ancora mostrato al pubblico, solo un
  promemoria interno

## Richiede l'Adesione

Questo interruttore decide se completare la prenotazione crea o aggiorna una
voce nel libro soci, dopo il check-in:

- **Attivo** (default) — statutariamente, partecipare equivale ad
  associarsi: al check-in confermato, la persona entra o resta nel libro
  soci
- **Disattivo** — l'evento diventa una semplice prenotazione: il modulo da
  compilare resta lo stesso, ma nessun socio viene mai creato o aggiornato

Utile per eventi aperti anche a chi non è socio, dove chiedere l'adesione
completa non avrebbe senso. Approfondito in
[Costruttore di Moduli](form-builder.md#prenotazione-senza-adesione).

## Check-in e Lista Inviata

Due campi di sola lettura tengono traccia di cosa è successo il giorno
dell'evento: quando è stata inviata la lista delle prenotazioni (a
mezzanotte prima dell'evento, automaticamente) e quando un editor ha aperto
il check-in all'ingresso. Non sono modificabili da qui: si vedono, ma si
gestiscono dalla pagina stessa dell'evento, descritta in
[Check-in il Giorno dell'Evento](checkin.md).
