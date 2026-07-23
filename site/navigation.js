(() => {
  const root = document.querySelector("[data-navigation-root]");
  const button = root?.querySelector(".nav-toggle");
  const navigation = root?.querySelector(".nav-links");
  if (!(root instanceof HTMLElement) || !(button instanceof HTMLButtonElement) || !(navigation instanceof HTMLElement)) return;

  const closeNavigation = () => {
    root.dataset.navigationOpen = "false";
    button.setAttribute("aria-expanded", "false");
  };

  button.hidden = false;
  root.dataset.navigationReady = "true";

  button.addEventListener("click", () => {
    const willOpen = root.dataset.navigationOpen !== "true";
    root.dataset.navigationOpen = String(willOpen);
    button.setAttribute("aria-expanded", String(willOpen));
  });

  navigation.addEventListener("click", (event) => {
    if (event.target instanceof Element && event.target.closest("a")) closeNavigation();
  });

  root.addEventListener("keydown", (event) => {
    if (event.key !== "Escape" || root.dataset.navigationOpen !== "true") return;
    closeNavigation();
    button.focus();
  });

  window.matchMedia("(min-width: 701px)").addEventListener("change", closeNavigation);
})();
