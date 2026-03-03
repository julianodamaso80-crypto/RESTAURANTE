/* ═══════════════════════════════════════════════════════════
   MesaMestre — Landing Page Interactions
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── 1. REVEAL ON SCROLL ─────────────────────────────── */
  function initReveal() {
    var reveals = document.querySelectorAll('.reveal');
    if (!reveals.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;

          var el = entry.target;
          var delay = parseInt(el.getAttribute('data-delay') || '0', 10);

          setTimeout(function () {
            el.classList.add('is-visible');
          }, delay * 100);

          observer.unobserve(el);
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    reveals.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ── 2. COUNTER ANIMATION ────────────────────────────── */
  function initCounters() {
    var counters = document.querySelectorAll('[data-count]');
    if (!counters.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;

          var el = entry.target;
          var target = parseInt(el.getAttribute('data-count'), 10);
          var duration = 1500;
          var start = 0;
          var startTime = null;

          function step(timestamp) {
            if (!startTime) startTime = timestamp;
            var progress = Math.min((timestamp - startTime) / duration, 1);
            // ease-out cubic
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = Math.floor(eased * (target - start) + start);
            el.textContent = current;

            if (progress < 1) {
              requestAnimationFrame(step);
            } else {
              el.textContent = target;
            }
          }

          requestAnimationFrame(step);
          observer.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );

    counters.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ── 3. NAVBAR SHRINK ON SCROLL ──────────────────────── */
  function initNavbar() {
    var navbar = document.getElementById('navbar');
    if (!navbar) return;

    var scrollThreshold = 60;
    var ticking = false;

    function onScroll() {
      if (!ticking) {
        requestAnimationFrame(function () {
          if (window.scrollY > scrollThreshold) {
            navbar.classList.add('is-scrolled');
          } else {
            navbar.classList.remove('is-scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ── 4. MOBILE MENU ──────────────────────────────────── */
  function initMobileMenu() {
    var hamburger = document.getElementById('hamburger');
    var mobileMenu = document.getElementById('mobileMenu');
    if (!hamburger || !mobileMenu) return;

    hamburger.addEventListener('click', function () {
      var isOpen = hamburger.classList.toggle('is-open');
      mobileMenu.classList.toggle('is-open', isOpen);
      hamburger.setAttribute('aria-expanded', String(isOpen));
      mobileMenu.setAttribute('aria-hidden', String(!isOpen));
    });

    // Close menu when clicking a link
    var links = mobileMenu.querySelectorAll('a');
    links.forEach(function (link) {
      link.addEventListener('click', function () {
        hamburger.classList.remove('is-open');
        mobileMenu.classList.remove('is-open');
        hamburger.setAttribute('aria-expanded', 'false');
        mobileMenu.setAttribute('aria-hidden', 'true');
      });
    });
  }

  /* ── 5. PRICING TOGGLE ───────────────────────────────── */
  function initPricingToggle() {
    var toggle = document.getElementById('pricingToggle');
    var labelMonthly = document.getElementById('labelMonthly');
    var labelAnnual = document.getElementById('labelAnnual');
    if (!toggle) return;

    var amounts = document.querySelectorAll('.pricing-card__amount[data-monthly]');

    toggle.addEventListener('click', function () {
      var isAnnual = toggle.getAttribute('aria-checked') === 'true';
      var newState = !isAnnual;
      toggle.setAttribute('aria-checked', String(newState));

      if (newState) {
        labelMonthly.classList.remove('pricing__label--active');
        labelAnnual.classList.add('pricing__label--active');
      } else {
        labelMonthly.classList.add('pricing__label--active');
        labelAnnual.classList.remove('pricing__label--active');
      }

      amounts.forEach(function (el) {
        var value = newState
          ? el.getAttribute('data-annual')
          : el.getAttribute('data-monthly');

        // Fade transition
        el.style.opacity = '0';
        setTimeout(function () {
          el.textContent = value;
          el.style.opacity = '1';
        }, 150);
      });
    });
  }

  /* ── 6. SMOOTH SCROLL FOR ANCHOR LINKS ───────────────── */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (link) {
      link.addEventListener('click', function (e) {
        var targetId = this.getAttribute('href');
        if (targetId === '#') return;

        var target = document.querySelector(targetId);
        if (!target) return;

        e.preventDefault();

        var navHeight = parseInt(
          getComputedStyle(document.documentElement)
            .getPropertyValue('--nav-height'),
          10
        ) || 72;

        var top = target.getBoundingClientRect().top + window.scrollY - navHeight;
        window.scrollTo({ top: top, behavior: 'smooth' });
      });
    });
  }

  /* ── 7. FAQ — single open at a time (optional UX) ───── */
  function initFAQ() {
    var items = document.querySelectorAll('.faq__item');
    if (!items.length) return;

    items.forEach(function (item) {
      item.addEventListener('toggle', function () {
        if (this.open) {
          items.forEach(function (other) {
            if (other !== item && other.open) {
              other.open = false;
            }
          });
        }
      });
    });
  }

  /* ── INIT ────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    initReveal();
    initCounters();
    initNavbar();
    initMobileMenu();
    initPricingToggle();
    initSmoothScroll();
    initFAQ();
  });
})();
