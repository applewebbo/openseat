// Registered before Alpine loads so the listener fires on init.
document.addEventListener("alpine:init", () => {
    // A typeable dd/mm/yyyy field: digits only, auto-advance over the
    // separators, hard stop at 8 digits, with a hidden native date input as
    // the calendar-button fallback. See templates/widgets/masked-date-input.html.
    //
    // Reformats on the `input` event rather than intercepting `keydown`:
    // mobile virtual keyboards (iOS Safari in particular) routinely report
    // `key: "Unidentified"` on keydown, which would block typing outright.
    // Reading the value the browser already inserted works everywhere —
    // virtual keyboards, autofill, paste, dictation included.
    Alpine.data("maskedDate", () => ({
        digits: "",

        init() {
            this.digits = this.$refs.text.value.replace(/\D/g, "").slice(0, 8);
            this.render();
        },

        format() {
            const d = this.digits;
            let out = d.slice(0, 2);
            if (d.length > 2) out += "/" + d.slice(2, 4);
            if (d.length > 4) out += "/" + d.slice(4, 8);
            return out;
        },

        render() {
            this.$refs.text.value = this.format();
            const end = this.$refs.text.value.length;
            this.$refs.text.setSelectionRange(end, end);
        },

        onInput(event) {
            this.digits = event.target.value.replace(/\D/g, "").slice(0, 8);
            this.render();
        },

        openPicker() {
            const day = this.digits.slice(0, 2);
            const month = this.digits.slice(2, 4);
            const year = this.digits.slice(4, 8);
            if (year.length === 4) {
                this.$refs.picker.value = `${year}-${month}-${day}`;
            }
            if (typeof this.$refs.picker.showPicker === "function") {
                this.$refs.picker.showPicker();
            } else {
                this.$refs.picker.focus();
            }
        },

        onPickerChange(event) {
            const value = event.target.value;
            if (!value) return;
            const [year, month, day] = value.split("-");
            this.digits = `${day}${month}${year}`;
            this.render();
        },
    }));
});
