/**
 * СТРАНИЦА МЕБЕЛЬНОГО АТЕЛЬЕ «РЕцепт»
 * ===================================
 * Ванильный JavaScript, без зависимостей и сборки. Скрипт только оживляет
 * то, что уже есть в разметке: если он не загрузится, страница остаётся
 * полностью читаемой и рабочей — меню, якоря, телефоны и формы-заглушки
 * продолжают работать.
 *
 * Куда отправлять заявки
 * ---------------------
 * LEAD_ENDPOINT — адрес, который принимает POST с JSON-заявкой
 * (например, ваша CRM, Google Apps Script, n8n или Telegram-бот).
 * Если он пуст, заявка открывается в почтовом клиенте — это честнее,
 * чем показывать «отправлено» при отсутствии бэкенда.
 */

var LEAD_ENDPOINT = '';
var LEAD_EMAIL = 'tver-kuhni11@yandex.ru';

(function () {
  'use strict';

  var doc = document;
  var html = doc.documentElement;
  html.classList.remove('no-js');
  html.classList.add('js');

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------- *
   * ГОД В ПОДВАЛЕ
   * ---------------------------------------------------------------- */
  var yearEl = doc.getElementById('year');
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* ---------------------------------------------------------------- *
   * ШАПКА: ПОДЛОЖКА ПОСЛЕ ПРОКРУТКИ
   * ---------------------------------------------------------------- */
  var header = doc.getElementById('header');
  if (header) {
    var onScroll = function () {
      header.dataset.stuck = window.scrollY > 24 ? 'true' : 'false';
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------------------------------------------------------------- *
   * МОБИЛЬНОЕ МЕНЮ
   * ---------------------------------------------------------------- */
  var burger = doc.getElementById('burger');
  var menu = doc.getElementById('menu');

  function setMenu(open) {
    if (!menu || !burger) return;
    doc.body.dataset.menu = open ? 'true' : 'false';
    burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (open) {
      menu.hidden = false;
      doc.body.style.overflow = 'hidden';
    } else {
      doc.body.style.overflow = '';
      // Даём анимации договориться до конца, потом убираем из потока
      window.setTimeout(function () {
        if (doc.body.dataset.menu !== 'true') menu.hidden = true;
      }, 500);
    }
  }

  if (burger && menu) {
    burger.addEventListener('click', function () {
      setMenu(doc.body.dataset.menu !== 'true');
    });

    menu.addEventListener('click', function (event) {
      var link = event.target.closest('a');
      if (link) setMenu(false);
    });

    doc.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') setMenu(false);
    });
  }

  /* ---------------------------------------------------------------- *
   * ПОЯВЛЕНИЕ ПРИ ПРОКРУТКЕ
   * ---------------------------------------------------------------- */
  var revealItems = doc.querySelectorAll('[data-reveal]');

  if (!('IntersectionObserver' in window) || reduceMotion) {
    revealItems.forEach(function (el) {
      el.dataset.revealed = 'true';
    });
  } else {
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.dataset.revealed = 'true';
          revealObserver.unobserve(entry.target);
        });
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.08 }
    );

    revealItems.forEach(function (el) {
      revealObserver.observe(el);
    });
  }

  /* ---------------------------------------------------------------- *
   * АККОРДЕОН
   * ---------------------------------------------------------------- */
  function initAccordion(root) {
    if (!root) return;
    var heads = root.querySelectorAll('.acc__head');

    heads.forEach(function (head) {
      head.addEventListener('click', function () {
        var item = head.closest('.acc');
        var isOpen = item.dataset.open === 'true';

        // Одновременно открытым остаётся один пункт: так список читается
        root.querySelectorAll('.acc').forEach(function (other) {
          if (other === item) return;
          other.dataset.open = 'false';
          var h = other.querySelector('.acc__head');
          if (h) h.setAttribute('aria-expanded', 'false');
        });

        item.dataset.open = isOpen ? 'false' : 'true';
        head.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
      });
    });
  }

  initAccordion(doc.getElementById('acc-doubts'));
  initAccordion(doc.getElementById('acc-faq'));

  /* ---------------------------------------------------------------- *
   * ФИЛЬТР ПРОЕКТОВ ПО ПЛАНИРОВКЕ
   * ---------------------------------------------------------------- */
  var filters = doc.querySelectorAll('.filter');
  var cards = doc.querySelectorAll('.card-project');

  filters.forEach(function (button) {
    button.addEventListener('click', function () {
      var value = button.dataset.filter;

      filters.forEach(function (other) {
        other.setAttribute('aria-pressed', other === button ? 'true' : 'false');
      });

      cards.forEach(function (card) {
        var show = value === 'all' || card.dataset.layout === value;
        card.hidden = !show;
        if (show) card.dataset.revealed = 'true';
      });
    });
  });

  /* ---------------------------------------------------------------- *
   * ЛАЙТБОКС
   * ---------------------------------------------------------------- */
  var lightbox = doc.getElementById('lightbox');
  var lbImage = doc.getElementById('lb-image');
  var lbCaption = doc.getElementById('lb-caption');
  var gallery = [];
  var currentIndex = 0;

  function collectGallery() {
    var items = doc.querySelectorAll('.card-project img, .detail img');
    gallery = Array.prototype.map.call(items, function (img) {
      return {
        src: img.currentSrc || img.src,
        alt: img.alt || '',
        caption:
          (img.closest('.card-project') &&
            img.closest('.card-project').querySelector('.card-project__title')
              ?.textContent) ||
          (img.closest('.detail') &&
            img.closest('.detail').querySelector('.detail__title')
              ?.textContent) ||
          ''
      };
    });
  }

  function openLightbox(index) {
    if (!lightbox || !gallery.length) return;
    currentIndex = index;
    var item = gallery[currentIndex];
    lbImage.src = item.src;
    lbImage.alt = item.alt;
    lbCaption.textContent = item.caption;
    lightbox.dataset.open = 'true';
    doc.body.style.overflow = 'hidden';
    var close = doc.getElementById('lb-close');
    if (close) close.focus();
  }

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.dataset.open = 'false';
    doc.body.style.overflow = '';
  }

  function stepLightbox(delta) {
    if (!gallery.length) return;
    currentIndex = (currentIndex + delta + gallery.length) % gallery.length;
    var item = gallery[currentIndex];
    lbImage.src = item.src;
    lbImage.alt = item.alt;
    lbCaption.textContent = item.caption;
  }

  if (lightbox) {
    collectGallery();

    doc.querySelectorAll('.card-project').forEach(function (card) {
      card.addEventListener('click', function () {
        var img = card.querySelector('img');
        var index = gallery.findIndex(function (g) {
          return g.src === (img.currentSrc || img.src);
        });
        openLightbox(index >= 0 ? index : 0);
      });
    });

    doc.querySelectorAll('.detail').forEach(function (detail) {
      detail.addEventListener('click', function () {
        var img = detail.querySelector('img');
        var index = gallery.findIndex(function (g) {
          return g.src === (img.currentSrc || img.src);
        });
        openLightbox(index >= 0 ? index : 0);
      });
    });

    doc.getElementById('lb-close').addEventListener('click', closeLightbox);
    doc.getElementById('lb-prev').addEventListener('click', function () {
      stepLightbox(-1);
    });
    doc.getElementById('lb-next').addEventListener('click', function () {
      stepLightbox(1);
    });

    lightbox.addEventListener('click', function (event) {
      if (event.target === lightbox) closeLightbox();
    });

    doc.addEventListener('keydown', function (event) {
      if (lightbox.dataset.open !== 'true') return;
      if (event.key === 'Escape') closeLightbox();
      if (event.key === 'ArrowLeft') stepLightbox(-1);
      if (event.key === 'ArrowRight') stepLightbox(1);
    });
  }

  /* ---------------------------------------------------------------- *
   * БРИФ: ПЯТЬ ШАГОВ
   * ---------------------------------------------------------------- */
  var briefForm = doc.getElementById('brief-form');
  var briefCard = briefForm && briefForm.closest('.brief__card');

  if (briefForm) {
    var steps = briefForm.querySelectorAll('.brief__step');
    var total = steps.length;
    var step = 1;
    var answers = {};

    var bar = doc.getElementById('brief-bar');
    var stepLabel = doc.getElementById('brief-step-label');
    var nextBtn = doc.getElementById('brief-next');
    var backBtn = doc.getElementById('brief-back');
    var statusEl = doc.getElementById('brief-status');

    // Выбор варианта: один на группу, можно передумать
    briefForm.querySelectorAll('.option').forEach(function (option) {
      option.addEventListener('click', function () {
        var group = option.closest('[data-group]');
        var name = group.dataset.group;
        var value = option.dataset.value;

        var already = option.getAttribute('aria-pressed') === 'true';
        group.querySelectorAll('.option').forEach(function (o) {
          o.setAttribute('aria-pressed', 'false');
        });
        option.setAttribute('aria-pressed', already ? 'false' : 'true');
        answers[name] = already ? '' : value;

        // На шагах с выбором двигаемся вперёд сразу — это быстрее,
        // чем тянуться к кнопке «Далее»
        if (!already) window.setTimeout(function () { goTo(step + 1); }, 220);
      });
    });

    function show(n) {
      steps.forEach(function (s) {
        s.hidden = Number(s.dataset.step) !== n;
      });
      step = n;
      if (bar) bar.style.width = (n / total) * 100 + '%';
      if (stepLabel) stepLabel.textContent = 'Шаг ' + n + ' из ' + total;
      if (backBtn) backBtn.hidden = n === 1;
      if (nextBtn) {
        nextBtn.innerHTML =
          n === total
            ? 'Отправить заявку <span class="btn__arrow" aria-hidden="true">→</span>'
            : 'Далее <span class="btn__arrow" aria-hidden="true">→</span>';
      }
      if (statusEl) statusEl.textContent = '';
    }

    function goTo(n) {
      if (n < 1 || n > total) return;
      show(n);
    }

    nextBtn.addEventListener('click', function () {
      var current = briefForm.querySelector('.brief__step:not([hidden])');
      var group = current && current.querySelector('[data-group]');

      if (group && !answers[group.dataset.group]) {
        if (statusEl) {
          statusEl.textContent = 'Выберите вариант — или нажмите «Пропустить» ниже.';
          statusEl.dataset.state = 'error';
        }
        return;
      }

      if (step === total) {
        submitBrief();
      } else {
        goTo(step + 1);
      }
    });

    backBtn.addEventListener('click', function () {
      goTo(step - 1);
    });

    doc.getElementById('brief-skip-form').addEventListener('click', function () {
      goTo(total);
    });

    function submitBrief() {
      var name = doc.getElementById('bf-name').value.trim();
      var contact = doc.getElementById('bf-contact').value.trim();
      var comment = doc.getElementById('bf-comment').value.trim();
      var consent = doc.getElementById('bf-consent').checked;

      if (!name || !contact) {
        statusEl.textContent = 'Нужны имя и способ связи — иначе мы не сможем ответить.';
        statusEl.dataset.state = 'error';
        return;
      }
      if (!consent) {
        statusEl.textContent = 'Отметьте согласие на обработку данных.';
        statusEl.dataset.state = 'error';
        return;
      }

      var payload = {
        form: 'brief',
        name: name,
        contact: contact,
        comment: comment,
        layout: answers.layout || '',
        priority: answers.priority || '',
        facade: answers.facade || '',
        timing: answers.timing || '',
        page: window.location.href,
        at: new Date().toISOString()
      };

      sendLead(payload, function () {
        briefForm.hidden = true;
        var done = doc.getElementById('brief-done');
        if (done) done.hidden = false;
      });
    }

    show(1);
  }

  /* ---------------------------------------------------------------- *
   * ФОРМА «ЗАПИСАТЬСЯ НА ЗАМЕР»
   * ---------------------------------------------------------------- */
  var ctaForm = doc.getElementById('cta-form');
  if (ctaForm) {
    ctaForm.addEventListener('submit', function (event) {
      event.preventDefault();

      var name = doc.getElementById('cta-name').value.trim();
      var contact = doc.getElementById('cta-contact').value.trim();
      var consent = doc.getElementById('cta-consent').checked;
      var statusEl = doc.getElementById('cta-status');

      if (!name || !contact) {
        statusEl.textContent = 'Нужны имя и телефон.';
        statusEl.dataset.state = 'error';
        return;
      }
      if (!consent) {
        statusEl.textContent = 'Отметьте согласие на обработку данных.';
        statusEl.dataset.state = 'error';
        return;
      }

      sendLead(
        {
          form: 'zamer',
          name: name,
          contact: contact,
          page: window.location.href,
          at: new Date().toISOString()
        },
        function () {
          ctaForm.hidden = true;
          var done = doc.getElementById('cta-done');
          if (done) done.hidden = false;
        }
      );
    });
  }

  /* ---------------------------------------------------------------- *
   * ОТПРАВКА ЗАЯВКИ
   * ---------------------------------------------------------------- */
  function sendLead(payload, onDone) {
    if (LEAD_ENDPOINT) {
      fetch(LEAD_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function () { onDone(); })
        .catch(function () { onDone(); });
      return;
    }

    // Бэкенда нет — открываем почтовый клиент с готовым письмом
    var subject = 'Заявка с сайта: кухня на заказ';
    var body = [
      'Имя: ' + payload.name,
      'Контакт: ' + payload.contact,
      payload.comment ? 'Комментарий: ' + payload.comment : '',
      payload.layout ? 'Планировка: ' + payload.layout : '',
      payload.priority ? 'Важнее всего: ' + payload.priority : '',
      payload.facade ? 'Фасады: ' + payload.facade : '',
      payload.timing ? 'Сроки: ' + payload.timing : '',
      '',
      'Страница: ' + payload.page
    ]
      .filter(Boolean)
      .join('\n');

    window.location.href =
      'mailto:' +
      LEAD_EMAIL +
      '?subject=' +
      encodeURIComponent(subject) +
      '&body=' +
      encodeURIComponent(body);

    onDone();
  }

  /* ---------------------------------------------------------------- *
   * МОБИЛЬНАЯ ПАНЕЛЬ
   * Показываем после того, как человек проскроллил первый экран:
   * наверху он ещё не готов звонить.
   * ---------------------------------------------------------------- */
  var mobileBar = doc.getElementById('mobile-bar');
  if (mobileBar) {
    var threshold = window.innerHeight * 0.9;
    var updateBar = function () {
      mobileBar.dataset.visible = window.scrollY > threshold ? 'true' : 'false';
    };
    updateBar();
    window.addEventListener('scroll', updateBar, { passive: true });
    window.addEventListener('resize', function () {
      threshold = window.innerHeight * 0.9;
      updateBar();
    }, { passive: true });
  }
})();
