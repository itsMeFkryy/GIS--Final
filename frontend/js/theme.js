/**
 * theme.js — Dark / Light theme toggle + tile layer switching
 */
const Theme = (() => {
    const KEY = 'gis_theme';
    let current = localStorage.getItem(KEY) || 'dark';

    const TILES = {
        light: {
            url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
            attr: '&copy; OpenStreetMap &copy; CARTO'
        },
        dark: {
            url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
            attr: '&copy; OpenStreetMap &copy; CARTO'
        }
    };

    let tileLayer = null;

    function apply(theme) {
        current = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(KEY, theme);

        // Update toggle button
        const btn = document.getElementById('theme-toggle-btn');
        if (btn) {
            btn.innerHTML = theme === 'dark'
                ? '<i class="ph-fill ph-sun"></i> Light Mode'
                : '<i class="ph-fill ph-moon"></i> Dark Mode';
        }

        // Swap Leaflet tile layer
        if (window._leafletMap && tileLayer) {
            window._leafletMap.removeLayer(tileLayer);
        }
        if (window._leafletMap) {
            tileLayer = L.tileLayer(TILES[theme].url, {
                maxZoom: 19,
                attribution: TILES[theme].attr
            });
            tileLayer.addTo(window._leafletMap);
            // push tile layer below everything else
            tileLayer.getPane('tilePane');
        }
    }

    function toggle() {
        apply(current === 'light' ? 'dark' : 'light');
    }

    function init() {
        apply(current);
    }

    function registerMap(leafletMap) {
        window._leafletMap = leafletMap;
        // Add initial tile layer now that map is available
        tileLayer = L.tileLayer(TILES[current].url, {
            maxZoom: 19,
            attribution: TILES[current].attr
        });
        tileLayer.addTo(leafletMap);
    }

    return { init, toggle, registerMap, current: () => current };
})();
