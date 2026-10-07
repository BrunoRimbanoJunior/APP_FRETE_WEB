(function () {
    const nav = document.querySelector('.navbar');
    const toggle = document.querySelector('.nav-toggle');
    const links = document.getElementById('main-navigation');
    const config = document.querySelector('.cfg-dropdown');
    if (nav && toggle && links) {
        nav.classList.add('js-navigation');
        toggle.hidden = false;
        toggle.addEventListener('click', function () {
            const expanded = links.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', String(expanded));
            if (!expanded && config) config.open = false;
        });
        document.addEventListener('keydown', function (event) {
            if (event.key !== 'Escape') return;
            if (config && config.open) {
                config.open = false;
                config.querySelector('summary').focus();
            } else if (links.classList.contains('is-open')) {
                links.classList.remove('is-open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.focus();
            }
        });
        document.addEventListener('click', function (event) {
            if (config && !config.contains(event.target)) config.open = false;
        });
    }
    ['htmx:responseError', 'htmx:sendError', 'htmx:timeout'].forEach(function (name) {
        document.addEventListener(name, function (event) {
            const source = event.detail.elt.closest('[data-error-target]');
            const target = source && document.querySelector(source.dataset.errorTarget);
            if (target) {
                target.textContent = 'Não foi possível concluir a solicitação. Confira a conexão e tente novamente.';
                target.classList.add('text-danger');
            }
        });
    });
    document.addEventListener('htmx:beforeRequest', function (event) {
        const source = event.detail.elt.closest('[data-error-target]');
        const target = source && document.querySelector(source.dataset.errorTarget);
        if (target) {
            target.classList.remove('text-danger');
            if (target.id !== 'resultado') target.textContent = '';
        }
    });
})();
