/**
 * SPOR24 Autonomous Analytics & Pulse Tracker
 * Ultra-lightweight, zero-cookie, KVKK compliant tracker.
 */
(function () {
    if (window._spor24_tracker_active) return;
    window._spor24_tracker_active = true;

    const API_ENDPOINT = '/api/analytics/track/';

    function getQueryParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            haber_id: params.get('id') || params.get('haber_id') || null,
            utm_source: params.get('utm_source') || '',
            utm_medium: params.get('utm_medium') || '',
            utm_campaign: params.get('utm_campaign') || ''
        };
    }

    function sendEvent(eventType, targetUrl = null) {
        const qp = getQueryParams();
        const payload = {
            path: window.location.pathname + window.location.search,
            event_type: eventType,
            screen_width: window.innerWidth,
            referrer: document.referrer || '',
            haber_id: qp.haber_id,
            utm_source: qp.utm_source,
            utm_medium: qp.utm_medium,
            utm_campaign: qp.utm_campaign,
            target_url: targetUrl
        };

        if (navigator.sendBeacon) {
            try {
                const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
                navigator.sendBeacon(API_ENDPOINT, blob);
                return;
            } catch (e) {}
        }

        fetch(API_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
            keepalive: true
        }).catch(function () {});
    }

    // 1. Initial Pageview
    sendEvent('pageview');

    // 2. Heartbeat Ping every 25 seconds for live borsa-style active visitor count
    setInterval(function () {
        if (document.visibilityState === 'visible') {
            sendEvent('heartbeat');
        }
    }, 25000);

    // 3. Global click listener for shares and outbound link exits
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a');
        if (!link || !link.href) return;

        const href = link.href.toLowerCase();

        // Share click detection
        if (href.includes('twitter.com') || href.includes('x.com') || href.includes('whatsapp') || href.includes('telegram') || href.includes('t.me') || href.includes('facebook.com')) {
            sendEvent('share_click', link.href);
            return;
        }

        // Outbound exit link detection
        try {
            const url = new URL(link.href);
            if (url.origin && url.origin !== window.location.origin && !url.hostname.includes('spor24.net')) {
                sendEvent('outbound_click', link.href);
            }
        } catch (err) {}
    }, true);
})();
