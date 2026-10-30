(function () {
    const svg = document.getElementById('clockPreview');
    const status = document.getElementById('previewStatus');
    const ns = 'http://www.w3.org/2000/svg';
    let timer;
    let inFlight = false;
    let hasFrame = false;

    function render(frame) {
        if (!frame || !['normal', 'xl'].includes(frame.boardType) || !Array.isArray(frame.rows) ||
            !frame.rows.length || !frame.rows.every(row => Array.isArray(row)) ||
            !Number.isFinite(frame.brightness)) throw new Error('Invalid frame');
        const rows = frame.rows;
        const width = Math.max(...rows.map(row => row.length)) + (rows.length - 1) / 2;
        const scale = Math.max(0, Math.min(255, frame.brightness)) / 255;
        const rowSpacing = Math.sqrt(3) / 2;
        svg.setAttribute('viewBox', `0 0 ${width} ${1 + (rows.length - 1) * rowSpacing}`);
        svg.setAttribute('aria-label', `Live ${frame.boardType === 'xl' ? 'XL' : 'normal'} clock display preview`);
        const fragment = document.createDocumentFragment();
        rows.forEach((row, y) => row.forEach((color, x) => {
            if (color === null) return;
            if (!Number.isInteger(color) || color < 0 || color > 0xffffff) throw new Error('Invalid pixel');
            const circle = document.createElementNS(ns, 'circle');
            circle.setAttribute('cx', x + (rows.length - 1 - y) / 2 + 0.5);
            circle.setAttribute('cy', y * rowSpacing + 0.5);
            circle.setAttribute('r', 0.46);
            const channels = [16, 8, 0].map(shift => Math.round(((color >> shift) & 255) * scale));
            circle.setAttribute('fill', `rgb(${channels.join(',')})`);
            circle.setAttribute('stroke', '#55515e');
            circle.setAttribute('stroke-width', '0.025');
            fragment.appendChild(circle);
        }));
        svg.replaceChildren(fragment);
    }

    async function poll() {
        if (document.hidden || inFlight) return;
        inFlight = true;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        try {
            const response = await fetch('/api/frame', {cache: 'no-store', signal: controller.signal});
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            render(await response.json());
            hasFrame = true;
            if (status.textContent !== 'Live') status.textContent = 'Live';
            status.dataset.state = 'live';
        } catch (error) {
            const message = hasFrame ? 'Disconnected · retrying' : 'Waiting for display · retrying';
            if (status.textContent !== message) status.textContent = message;
            status.dataset.state = 'stale';
        } finally {
            clearTimeout(timeout);
            inFlight = false;
            if (!document.hidden) timer = setTimeout(poll, 400);
        }
    }
    document.addEventListener('visibilitychange', () => {
        clearTimeout(timer);
        if (!document.hidden && !inFlight) poll();
    });
    poll();

    // Native dropdowns keep the controls usable without a CDN connection.
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    function closeDropdown(button) {
        button.setAttribute('aria-expanded', 'false');
        button.nextElementSibling.classList.remove('show');
    }
    dropdowns.forEach(button => {
        const menu = button.nextElementSibling;
        button.removeAttribute('data-toggle');
        button.addEventListener('click', () => {
            const open = button.getAttribute('aria-expanded') !== 'true';
            dropdowns.forEach(closeDropdown);
            button.setAttribute('aria-expanded', String(open));
            menu.classList.toggle('show', open);
        });
        menu.addEventListener('click', () => {
            closeDropdown(button);
        });
        button.parentElement.addEventListener('focusout', event => {
            if (!button.parentElement.contains(event.relatedTarget)) closeDropdown(button);
        });
        button.parentElement.addEventListener('keydown', event => {
            if (event.key === 'Escape') {
                closeDropdown(button);
                button.focus();
            }
        });
    });
    document.addEventListener('click', event => {
        dropdowns.forEach(button => {
            if (!button.parentElement.contains(event.target)) closeDropdown(button);
        });
    });
})();
