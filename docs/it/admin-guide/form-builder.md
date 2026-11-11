# Costruttore di Moduli

Il **modulo pubblico** è il percorso a più passaggi (sezioni) che una persona
compila per associarsi, o per prenotare un posto a un evento. Sette sezioni
sono già pronte all'uso; puoi aggiungerne altre personalizzate senza bisogno
di un deploy, direttamente dall'admin.

## Le Sezioni Fisse

Ogni modulo nasce con queste sette sezioni, nell'ordine in cui compaiono:

1. **Chi partecipa all'evento** — per sé stessi o per conto di un minore/altra persona
2. **I tuoi dati** — anagrafica di chi firma la richiesta
3. **Chi partecipa** — anagrafica del minore, se diverso da chi firma
4. **Statuto e quota** — accettazione dello statuto e della quota associativa
5. **Informativa privacy** — il testo informativo GDPR
6. **Consensi immagine** — i due consensi su foto/video (sito e WhatsApp)
7. **Riepilogo e sottoscrizione** — la firma finale

!!! info "La struttura resta fissa"
    Il comportamento di queste sette sezioni — chi le vede, quando il minore
    richiede un secondo genitore, le regole di validazione — è parte del
    codice e non è modificabile dall'admin. Quello che **puoi** cambiare per
    ciascuna è:

    - **attivarla o disattivarla** per un modulo specifico (eccetto la firma
      finale, sempre presente)
    - il **titolo** mostrato al passaggio (campo *Titolo*)
    - per **Statuto e quota** e **Informativa privacy**, il **testo**
      mostrato (campo *Testo personalizzato*, con editor ricco) — se lasciato
      vuoto, resta il testo di fabbrica
    - per **Consensi immagine**, le due **etichette** dei consensi (campi
      *Image consent label* e *WhatsApp consent label*)

Per modificarle, vai su **Admin → Associazione e domande → Sezioni**, scegli
la sezione del modulo che ti interessa e salva.

## Aggiungere una Sezione Personalizzata

Quando le sette sezioni fisse non bastano — per esempio vuoi chiedere in che
fascia oraria preferisce partecipare chi si iscrive — puoi aggiungerne una
tua.

1. Vai su **Admin → Associazione e domande → Sezioni → Aggiungi sezione**
2. Scegli il **modulo** a cui appartiene
3. Scrivi un **titolo** (obbligatorio: diventa anche lo slug tecnico della
   sezione, generato automaticamente — se un altro titolo genera lo stesso
   slug, viene aggiunto un numero)
4. Imposta l'**ordine** (un numero più basso compare prima) e se è **attiva**
5. Salva

![Form di creazione di una nuova sezione](../assets/screenshots/admin-section-add.png)

!!! warning "Attenzione all'ordine rispetto al riepilogo"
    La sezione **Riepilogo e sottoscrizione** è sempre l'ultimo passaggio
    raggiungibile dal modulo. Se dai alla tua sezione personalizzata un
    ordine più alto di quello del riepilogo, finirà dopo la firma e non sarà
    più raggiungibile da chi compila il modulo. Controlla l'ordine attuale
    delle altre sezioni dall'elenco prima di salvare.

A salvataggio avvenuto, la pagina mostra una tabella **Custom fields**: è da
qui che aggiungi le domande di questa sezione.

## Aggiungere Campi a una Sezione Personalizzata

Dalla pagina della sezione, clicca **Aggiungi un altro Custom field** e
scegli:

- **Etichetta** — la domanda mostrata alla persona
- **Testo di aiuto** — una riga facoltativa sotto la domanda
- **Tipo** — uno tra:
  - *Testo breve* — una riga di testo libero
  - *Testo lungo* — più righe di testo libero
  - *Scelta singola* — un menu a tendina con le opzioni che definisci tu
  - *Scelta multipla* — come sopra, ma selezionabili più opzioni insieme
  - *Casella di spunta* — una domanda sì/no
  - *Valore numerico* — un numero, anche decimale
- **Obbligatorio** — se spuntato, il modulo non avanza finché non risposto
- **Ordine** — l'ordine delle domande dentro la sezione

![Una sezione personalizzata con i suoi campi](../assets/screenshots/admin-section-custom-fields.png)

Per i tipi **Scelta singola** e **Scelta multipla** devi anche definire le
opzioni: salva il campo, poi apri la sua pagina dedicata (**Admin →
Associazione e domande → Custom field**, oppure il link dalla tabella della
sezione) e aggiungi le righe in **Choices**, ciascuna con una propria
etichetta e un ordine.

![Le opzioni di un campo a scelta singola](../assets/screenshots/admin-customfield-choices.png)

Le risposte di ogni persona restano collegate alla propria richiesta e sono
visibili insieme al resto nel dettaglio della richiesta in admin.

## Anteprima di una Sezione

Prima di pubblicare una sezione — fissa o personalizzata — puoi vederne
l'aspetto reale senza uscire dall'admin. In fondo alla pagina di modifica
trovi un riquadro **Anteprima** chiuso per non occupare spazio: clicca
**Mostra l'anteprima** per aprirlo.

![L'anteprima della sezione Statuto e quota, aperta](../assets/screenshots/admin-section-preview.png)

È un'istantanea di ciò che è salvato, non un'anteprima dal vivo: per vedere
l'effetto di una modifica al titolo o al testo devi prima salvare la pagina.

## Prenotazione Senza Adesione

Un evento non deve per forza richiedere di diventare socio per parteciparvi.

Su **Admin → Eventi e prenotazioni → Eventi**, ogni evento ha un'opzione
**Richiede l'adesione**:

- **Attiva** (il comportamento di default) — completare il modulo e il
  check-in all'ingresso crea o aggiorna una voce nel libro soci
- **Disattivata** — l'evento diventa una semplice prenotazione: chi partecipa
  compila comunque il modulo scelto per l'evento, ma nessun socio viene mai
  creato o aggiornato, nemmeno dopo il check-in

Utile per eventi aperti anche a non soci — una serata informativa, un evento
pubblico — dove far compilare il modulo di adesione completo non avrebbe
senso.
