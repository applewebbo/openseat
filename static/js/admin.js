// The account menu is one `details` that reads two ways: a row of links from
// 768px up, a button and a panel below it. A closed `details` does not render
// its content at all — no stylesheet can bring it back — so the open state is
// what the width is applied to, and the markup ships open for the case where
// this file never runs.
const wide = window.matchMedia("(min-width: 768px)");

const menus = () => document.querySelectorAll(".user-menu");

const syncToWidth = () => {
    menus().forEach((menu) => {
        menu.open = wide.matches;
    });
};

syncToWidth();
wide.addEventListener("change", syncToWidth);

// The two ways out a dropdown is expected to have. Only while it is one.
document.addEventListener("click", (event) => {
    if (wide.matches) return;
    menus().forEach((menu) => {
        if (menu.open && !menu.contains(event.target)) {
            menu.open = false;
        }
    });
});

document.addEventListener("keydown", (event) => {
    if (wide.matches || event.key !== "Escape") return;
    menus().forEach((menu) => {
        menu.open = false;
    });
});
