# Backup

OpenSeat esegue un backup automatico, una volta al giorno, senza bisogno di
alcuna azione dall'admin.

## Cosa viene salvato

Ogni giorno viene creato un dump del database e una copia dei file caricati
(loghi, immagini degli eventi, PDF dello statuto). Entrambi vengono conservati
per un numero di giorni configurato dall'installazione — i backup più vecchi
di quella soglia vengono eliminati automaticamente, così come i file caricati
che nessun record nel database referenzia più.

## Dove sono conservati

A seconda di come è stata configurata l'installazione, i backup possono
risiedere su disco locale o su uno spazio di archiviazione compatibile S3.
Questa configurazione è tecnica e viene decisa da chi gestisce
l'installazione, non dall'admin dell'associazione.

!!! info "Ripristinare un backup"
    Il ripristino è un'operazione tecnica, pensata per chi amministra
    l'installazione (non per l'uso quotidiano dell'associazione) e richiede
    accesso diretto al server. Non è trattato in questa guida.
