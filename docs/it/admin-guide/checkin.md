# Check-in il Giorno dell'Evento

Il giorno dell'evento, un editor (chi ha il permesso di modificare l'evento)
apre la pagina pubblica dell'evento e clicca **Gestisci evento**: la stessa
pagina diventa la postazione di check-in, senza bisogno di passare
dall'admin.

![La pagina di gestione dell'evento, con l'elenco delle prenotazioni](../assets/screenshots/event-checkin.png)

## Aprire il Check-in

Finché il check-in non è aperto, le prenotazioni restano solo annunciate.
Aprirlo chiude automaticamente le prenotazioni pubbliche per quell'evento —
da quel momento, i posti si gestiscono solo da qui.

## Confermare un Arrivo

Ogni riga dell'elenco corrisponde a una prenotazione attiva; confermarla
registra chi si è davvero presentato, insieme a come ha versato la quota se
prevista (contanti, bonifico, altro). Una conferma può sempre essere
annullata, se registrata per errore.

## Aggiungere Qualcuno all'Ultimo Momento

Chi si presenta senza una prenotazione può essere aggiunto sul posto:
cercando il suo codice fiscale, se è già socio i suoi dati si precompilano
automaticamente; altrimenti si registrano i dati minimi necessari lì per
lì.

## Esportare i Soci Acquisiti

A evento concluso, un'azione dedicata esporta in CSV i soci acquisiti
attraverso quell'evento — utile per chi tiene la contabilità o prepara il
report dell'iniziativa. Questa azione richiede un permesso più ampio di
quello che basta per il check-in: vedi
[Utenti e Permessi](users.md).

## Chiudere il Check-in

Chiudere il check-in riapre le prenotazioni pubbliche, se la data lo
permette ancora — utile se il check-in è stato aperto per errore o in
anticipo.
