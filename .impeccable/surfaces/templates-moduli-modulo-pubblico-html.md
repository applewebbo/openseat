---
version: 1
slug: "templates-moduli-modulo-pubblico-html"
primary_target: "templates/moduli/modulo-pubblico.html"
related_targets: ["templates/segreteria/importazione.html"]
---

# Modulo pubblico e importazione da foglio

## Ambito e modalità

Due superfici, entrambe **Operate**, deliberatamente separate: chi aderisce non passa
dove passa la segreteria, e viceversa.

1. **Modulo pubblico** — link pubblico, `@login_not_required`. Prima configurazione:
   richiesta di adesione a L'Ontano–La Ca' di Asu APS. Seconda configurazione dello
   stesso motore a sezioni: prenotazione a un evento.
2. **Importazione massiva da foglio** — back-office, per chi ha aderito su carta. Il
   volontario di segreteria non ricompila il modulo pubblico per conto di altri.

Fuori ambito qui: l'interfaccia di configurazione delle sezioni, la disdetta.

## Pubblico e compito

**Modulo pubblico** — un genitore, da smartphone, arrivato da un link su WhatsApp o
email. Nessun account, nessuna intenzione di crearne uno. Conosce già l'associazione di
persona. Compito unico: sottoscrivere la richiesta di adesione. Successo: il modulo
arriva completo, senza telefonate per un codice fiscale mancante.

**Importazione** — il volontario di segreteria, da desktop, con una pila di moduli
cartacei già firmati o un foglio già tenuto per altri motivi. Compito: portare quelle
persone nel registro senza ridigitarle una per una. Successo: capisce prima di
confermare cosa entrerà e cosa verrà scartato, e perché.

## Sostanza reale

Il modulo cartaceo de L'Ontano: informativa GDPR integrale (~4.500 caratteri), link allo
Statuto, quota annuale di 10 €, due consensi immagine distinti (diffusione su social e
sito; broadcast WhatsApp), ciascuno con scelta esplicita presto / non presto.

La ramificazione **maggiorenne capace / minore / persona con tutore o ads** cambia i
campi richiesti, i consensi e il numero di firmatari (uno oppure due). È la complessità
vera del modulo ed è dove i moduli generici falliscono.

Nessun dato inventato: niente testimonianze, niente numero di soci, niente installazioni
esistenti.

## Direzione scelta

**Modulo pubblico:** una sezione alla volta, ogni passo è un foglio sotto
un'intestazione fissa che identifica l'associazione. Linea di avanzamento in alto. Un
passo per richiesta, server-driven via htmx: validazione lato server, tasto Indietro del
browser funzionante, bozza che sopravvive a una connessione persa.

*Momento memorabile:* la scelta di apertura «per chi presenti la richiesta?», che
riconfigura visibilmente il percorso — la ramificazione risolta una volta all'inizio
invece di essere disseminata in campi che compaiono a metà compilazione.

**Importazione:** tre stadi, mai un caricamento cieco — carica il foglio, rivedi cosa è
stato riconosciuto, conferma. Lo stadio centrale è la superficie vera: righe valide,
righe scartate col motivo, duplicati già a registro. La conferma agisce su ciò che si è
appena letto.

*Momento memorabile:* nessuna riga entra senza essere stata mostrata.

## Le due firme

Risolto, da confermare col consulente dell'associazione (non è un parere legale).

L'adesione è **atto di ordinaria amministrazione**: una firma basta, purché il modulo
porti la dichiarazione di responsabilità genitoriale (artt. 316 e 337-ter c.c.), a
scelta esplicita fra *sottoscrivo anche in nome dell'altro genitore, in accordo con
lui/lei* e *sono unico titolare della responsabilità genitoriale*. È il meccanismo delle
iscrizioni scolastiche online. Nessuno stato pendente: l'adesione è completa all'invio.

I **consensi immagine** non sono ordinaria amministrazione: la diffusione dell'immagine
di un minore richiede il consenso di **tutti i titolari** della responsabilità
genitoriale. Quando i titolari sono due, nome ed email del secondo si raccolgono nello
stesso passo e parte un link personale per la sua conferma; finché non arriva, il
consenso alla diffusione resta **non attivo** — l'adesione è valida, le foto non si
pubblicano. Nel dubbio non si pubblica.

Nei nuclei monogenitoriali il titolare è uno solo e il suo consenso basta anche per
l'immagine: chi dichiara di essere unico titolare non entra mai nello stato di attesa.
La dichiarazione governa quindi entrambi gli atti e va chiesta **prima** dei consensi
immagine, perché decide se quella sezione mostri i campi del secondo genitore.

Microcopy, insidia da non sbagliare: separato o divorziato non significa unico titolare
— nell'affido condiviso, che è la regola, restano titolari entrambi. La formula dice
«unico titolare della responsabilità genitoriale», mai «genitore solo», affiancata dagli
esempi in cui è vera: affido esclusivo, decesso dell'altro genitore, riconoscimento da
parte di un solo genitore.

A database: una `Sottoscrizione` per atto, con firmatario, ruolo (primo o secondo
genitore), oggetto (adesione o consenso immagine), data, ora, IP e stato. Il secondo
genitore è registrato sempre, anche quando non firma.

Ne discende uno stato in più da progettare: *consenso immagine in attesa del secondo
genitore*, visibile alla segreteria e non bloccante per l'iscrizione.

## Vincoli

- Colori di base dell'associazione come tema della singola associazione, non come
  stile: `#ED5C08`, `#528116`, `#753B28`, `#4C5057`. L'impaginazione resta di OpenSeat;
  il marchio identifica, non imita.
- Nessun campo su stato di salute o diagnosi: l'informativa dichiara che quei dati si
  raccolgono solo a voce.
- Nessun consenso cumulativo, nessuna casella pre-spuntata, in nessuna delle due
  superfici — l'importazione deve portarsi dietro i consensi raccolti su carta e
  registrarne l'origine cartacea, o il registro mente su come sono stati raccolti.
- Resa da evitare: fondo panna con serif in corsivo. Il marchio è a pennarello, con
  arancione e verde saturi.
- Mai più di 8 campi per schermata; formati italiani (c.f., CAP, telefono) con
  validazione e tastiera adeguata.

## Sezioni e stati

Sezioni dell'adesione, ciascuna attivabile in configurazione: per chi presenti la
richiesta · chi presenta · dati dell'aderente (solo se minore o tutelato) · Statuto e
quota · informativa privacy (sola lettura) · consensi immagine · riepilogo e
sottoscrizione. 6-7 passi per l'adesione, 2-3 per una prenotazione. Nessun limite di
capienza sugli eventi.

Stati del modulo: primo accesso, passo in corso, errore su singolo campo, sezione
condizionale saltata, bozza ripresa, riepilogo, invio riuscito, modulo chiuso o link
scaduto, email già iscritta, errore del server, offline (PWA).

Stati dell'importazione: nessun file, foglio illeggibile, colonne non riconosciute,
anteprima con righe valide e scartate, zero righe valide, duplicati, importazione
parziale riuscita, annullamento dopo la conferma.

## Decisioni non risolte

Da non inventare in fase di costruzione:

1. **Luogo della sottoscrizione.** Proposta: precompilato dal comune di residenza,
   modificabile.
2. **Persistenza della bozza.** Sessione o record con token nel link. Consigliato il
   record: su telefono la connessione salta e ricominciare sette passi perde
   l'iscrizione.
3. **Quota associativa.** Il cartaceo dichiara l'impegno al versamento; non è deciso se
   OpenSeat lo registri, lo solleciti o lo ignori.
4. **Formato e mappatura del foglio.** Modello scaricabile a colonne fisse (consigliato:
   nessuno stadio di mappatura da progettare) oppure foglio libero con mappatura delle
   colonne. `.xlsx` richiede una dipendenza in più rispetto al solo CSV.
5. **Importazione parziale.** Le righe valide entrano e le scartate si segnalano, oppure
   il foglio passa tutto o niente.
6. **Configurazione lato organizzatore.** Il catalogo di sezioni attivabili esiste come
   modello, ma l'interfaccia che le accende non è progettata — e va progettata per
   volontari non tecnici.
