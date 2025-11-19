// Global UI controls for dark mode and background music
// Safe to include on any page; checks for element existence.

document.addEventListener("DOMContentLoaded", () => {
  // DARK MODE: apply saved state
  const darkSaved = localStorage.getItem("darkMode") === "true";
  if (darkSaved) document.body.classList.add("dark-mode");

  const themeToggle = document.getElementById("themeToggle");
  const themeIcon = document.getElementById("themeIcon");

  // Initialize theme icon if present
  if (themeIcon) themeIcon.className = darkSaved ? "fas fa-sun" : "fas fa-moon";

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const isDark = document.body.classList.toggle("dark-mode");
      localStorage.setItem("darkMode", isDark);
      if (themeIcon)
        themeIcon.className = isDark ? "fas fa-sun" : "fas fa-moon";
    });
  }

  // MUSIC: saved state and controls
  const bgMusic = document.getElementById("bgMusic");
  const musicToggle = document.getElementById("musicToggle");
  const musicIcon = document.getElementById("musicIcon");
  let musicEnabled = localStorage.getItem("musicEnabled") !== "false";

  function applyMusicState() {
    if (bgMusic) {
      if (musicEnabled) {
        const p = bgMusic.play();
        if (p && typeof p.catch === "function") p.catch(() => {});
      } else {
        try {
          bgMusic.pause();
        } catch (_) {}
        try {
          bgMusic.currentTime = 0;
        } catch (_) {}
      }
    }
    if (musicIcon)
      musicIcon.className = musicEnabled
        ? "fas fa-volume-up"
        : "fas fa-volume-mute";
  }

  // Initialize icon and attempt to apply music state (may be blocked until gesture)
  applyMusicState();

  if (musicToggle) {
    musicToggle.addEventListener("click", () => {
      musicEnabled = !musicEnabled;
      localStorage.setItem("musicEnabled", musicEnabled);
      applyMusicState();
    });
  }

  // AUTOPLAY UNLOCK after first gesture
  if (bgMusic && musicEnabled) {
    const unlock = async () => {
      try {
        const p = bgMusic.play();
        if (p && typeof p.catch === "function") await p.catch(() => {});
      } catch (_) {}
      window.removeEventListener("pointerdown", unlock);
      window.removeEventListener("keydown", unlock);
      window.removeEventListener("touchstart", unlock);
    };
    window.addEventListener("pointerdown", unlock, { once: true });
    window.addEventListener("keydown", unlock, { once: true });
    window.addEventListener("touchstart", unlock, { once: true });
  }
});
