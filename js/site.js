(function () {
  var toggle = document.querySelector('.nav-toggle');
  var closeBtn = document.querySelector('.nav-close');
  var nav = document.getElementById('site-nav');
  var overlay = document.getElementById('nav-overlay');
  if (toggle && nav && overlay) {
    function openMenu() {
      nav.hidden = false;
      overlay.hidden = false;
      requestAnimationFrame(function () {
        nav.classList.add('open');
        overlay.classList.add('open');
      });
      document.body.classList.add('menu-open');
      toggle.setAttribute('aria-expanded', 'true');
      toggle.setAttribute('aria-label', 'Close menu');
    }
    function closeMenu() {
      nav.classList.remove('open');
      overlay.classList.remove('open');
      document.body.classList.remove('menu-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.setAttribute('aria-label', 'Open menu');
      setTimeout(function () {
        if (!nav.classList.contains('open')) {
          nav.hidden = true;
          overlay.hidden = true;
        }
      }, 350);
    }
    function toggleMenu() {
      if (nav.classList.contains('open')) closeMenu();
      else openMenu();
    }

    toggle.addEventListener('click', toggleMenu);
    if (closeBtn) closeBtn.addEventListener('click', closeMenu);
    overlay.addEventListener('click', closeMenu);
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', closeMenu);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) closeMenu();
    });
  }

  var header = document.querySelector('.site-header');
  if (header) {
    function syncHeader() {
      header.classList.toggle('is-solid', window.scrollY > 8);
    }
    syncHeader();
    window.addEventListener('scroll', syncHeader, { passive: true });
  }
})();
