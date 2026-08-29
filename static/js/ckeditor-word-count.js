window.addEventListener("load", () => {
    document.querySelectorAll(".word-count").forEach((wrapper) => {
        const editorId = wrapper.id.replace(/_script-word-count$/, "");
        const editor = window.editors && window.editors[editorId];
        if (!editor || !editor.plugins.has("WordCount")) {
            return;
        }

        const wordCountPlugin = editor.plugins.get("WordCount");
        wrapper.classList.add("text-base-content/50", "mt-1.5", "text-xs");

        const render = () => {
            wrapper.textContent = `Parole: ${wordCountPlugin.words} · Caratteri: ${wordCountPlugin.characters}`;
        };
        render();
        wordCountPlugin.on("update", render);
    });
});
