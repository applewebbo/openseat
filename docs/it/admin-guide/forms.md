# Moduli Pubblici

Un **modulo pubblico** (`PublicForm`) è il contenitore del percorso che una
persona compila per associarsi — o per prenotare un evento, visto che
prenotare è un'applicazione come un'altra. Più moduli possono convivere,
ciascuno con le proprie sezioni.

![La pagina di modifica di un modulo pubblico](../assets/screenshots/admin-publicform.png)

In **Admin → Associazione e domande → Moduli pubblici** ogni modulo ha:

- **Titolo** e **introduzione** — cosa vede chi apre il link
- **Slug** — la parte finale dell'indirizzo pubblico (`/modulo/<slug>/`)
- **Aperto** — se disattivato, la pagina resta visibile ma non accetta più
  richieste
- **Predefinito** — il modulo preselezionato quando si crea un nuovo evento
  senza indicarne uno specifico; solo un modulo per associazione può esserlo

Sotto, la tabella **Sezioni** elenca l'intero catalogo di passaggi di questo
modulo, nell'ordine in cui compaiono: da qui si attivano o disattivano le
sezioni fisse, e si vedono anche quelle personalizzate già aggiunte. Per
crearne di nuove, o per modificarne testo e campi, vedi
[Costruttore di Moduli](form-builder.md).

Un nuovo modulo creato da zero riceve automaticamente l'intero catalogo di
sezioni fisse, già pronte e abilitate.
