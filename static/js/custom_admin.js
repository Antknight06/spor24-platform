document.addEventListener('DOMContentLoaded', function() {
    // Find the right-side nav menu in Jazzmin header
    const navbarNav = document.querySelector('.main-header .navbar-nav.ml-auto') || document.querySelector('.main-header .navbar-nav');
    if (!navbarNav) return;

    // Create container list item for Yeni Haber status
    const newsLi = document.createElement('li');
    newsLi.className = 'nav-item d-none d-sm-inline-block mr-2';
    newsLi.innerHTML = `
        <a href="/admin/haberler/bekleyenhaber/?onaylandi__exact=0&reddedildi__exact=0" 
           id="news-status-link" 
           class="nav-link"
           style="padding: 6px 12px; background: #3f4756; border: 1px solid #4f5962; border-radius: 6px; color: #fff; font-size: 13px; margin-top: 2px; display: inline-flex; align-items: center; gap: 6px; line-height: 1.2;">
            <span id="news-status-icon">📰</span>
            <span id="news-status-text">Yeni Haber: 0</span>
        </a>
    `;

    // Create container list item for Yetkili Haber status
    const yetkiliLi = document.createElement('li');
    yetkiliLi.className = 'nav-item d-none d-sm-inline-block mr-2';
    yetkiliLi.innerHTML = `
        <a href="/admin/haberler/bekleyenyetkilihaberi/?onaylandi__exact=0&reddedildi__exact=0" 
           id="yetkili-news-status-link" 
           class="nav-link"
           style="padding: 6px 12px; background: #3f4756; border: 1px solid #4f5962; border-radius: 6px; color: #fff; font-size: 13px; margin-top: 2px; display: inline-flex; align-items: center; gap: 6px; line-height: 1.2;">
            <span id="yetkili-news-status-icon">📝</span>
            <span id="yetkili-news-status-text">Yetkili Haber: 0</span>
        </a>
    `;

    // Insert at the beginning of the navbar-nav
    navbarNav.insertBefore(yetkiliLi, navbarNav.firstChild);
    navbarNav.insertBefore(newsLi, navbarNav.firstChild);

    // Fetch values dynamically
    function updateNewsStatus() {
        fetch('/admin/check-new-news/')
            .then(response => response.json())
            .then(data => {
                const statusText = document.getElementById('news-status-text');
                const statusIcon = document.getElementById('news-status-icon');
                const statusLink = document.getElementById('news-status-link');
                
                if (data.has_new_news) {
                    statusText.textContent = `Yeni Haber: ${data.pending_news_count}`;
                    statusLink.style.background = '#28a745';
                    statusLink.style.borderColor = '#218838';
                    statusLink.style.color = '#fff';
                    statusIcon.textContent = '🆕';
                } else {
                    statusText.textContent = 'Yeni Haber: 0';
                    statusLink.style.background = '#3f4756';
                    statusLink.style.borderColor = '#4f5962';
                    statusLink.style.color = '#fff';
                    statusIcon.textContent = '📰';
                }
                
                const yetkilStatusText = document.getElementById('yetkili-news-status-text');
                const yetkilStatusIcon = document.getElementById('yetkili-news-status-icon');
                const yetkilStatusLink = document.getElementById('yetkili-news-status-link');
                
                if (data.has_yetkili_news) {
                    yetkilStatusText.textContent = `Yetkili Haber: ${data.pending_yetkili_count}`;
                    yetkilStatusLink.style.background = '#17a2b8';
                    yetkilStatusLink.style.borderColor = '#138496';
                    yetkilStatusLink.style.color = '#fff';
                    yetkilStatusIcon.textContent = '📋';
                } else {
                    yetkilStatusText.textContent = 'Yetkili Haber: 0';
                    yetkilStatusLink.style.background = '#3f4756';
                    yetkilStatusLink.style.borderColor = '#4f5962';
                    yetkilStatusLink.style.color = '#fff';
                    yetkilStatusIcon.textContent = '📝';
                }
            })
            .catch(error => {
                console.log('Yeni haber kontrol hatası:', error);
            });
    }

    updateNewsStatus();
    setInterval(updateNewsStatus, 60000); // Check every minute
});

// ============================================================
// FEDERASYON WEB SİTELERİ "AKTİF" SÜTUNU MASTER CHECKBOX VE ANLIK KAYIT
// ============================================================
function setupFederasyonAktifToggle() {
    if (!window.location.pathname.includes('/admin/haberler/federasyonwebsite/')) return;

    // Helper for CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Helper for Toast Notifications
    function showToast(message, isSuccess) {
        let toast = document.getElementById('custom-admin-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'custom-admin-toast';
            toast.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 99999; padding: 12px 20px; border-radius: 8px; font-size: 14px; font-weight: 600; color: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.25); transition: all 0.3s ease; opacity: 0; transform: translateY(20px);';
            document.body.appendChild(toast);
        }
        toast.style.background = isSuccess ? 'linear-gradient(135deg, #28a745, #218838)' : 'linear-gradient(135deg, #dc3545, #c82333)';
        toast.textContent = message;
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
        }, 3000);
    }

    // Find Aktif TH header dynamically in #result_list
    const allThs = Array.from(document.querySelectorAll('#result_list thead th, table thead th'));
    const headerTh = allThs.find(th => {
        const text = th.textContent.trim();
        return text === 'Aktif' || (th.querySelector('a') && th.querySelector('a').textContent.trim() === 'Aktif');
    });

    if (!headerTh) return;

    // Row Checkboxes in td.field-aktif
    const rowCheckboxes = Array.from(document.querySelectorAll('td.field-aktif input[type="checkbox"]'));
    if (rowCheckboxes.length === 0) return;

    // Check if master checkbox already exists
    if (!document.getElementById('master-aktif-checkbox')) {
        const wrapper = document.createElement('span');
        wrapper.id = 'master-aktif-wrapper';
        wrapper.style.cssText = 'display: inline-flex; align-items: center; justify-content: center; margin-left: 8px; gap: 4px; background: rgba(255, 255, 255, 0.25); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.4); vertical-align: middle;';
        wrapper.innerHTML = `
            <input type="checkbox" id="master-aktif-checkbox" title="Tümünü Seç / Tümünü Kaldır (Anında Kaydeder)" style="transform: scale(1.3); cursor: pointer; margin: 0;">
        `;
        
        // Append inside headerTh (next to text link)
        const textDiv = headerTh.querySelector('.text') || headerTh;
        textDiv.appendChild(wrapper);

        const masterCheckbox = document.getElementById('master-aktif-checkbox');

        // Sync Master Checkbox Initial State
        const allChecked = rowCheckboxes.every(cb => cb.checked);
        masterCheckbox.checked = allChecked;

        // Master Checkbox Toggle Action
        masterCheckbox.addEventListener('change', function(e) {
            e.stopPropagation();
            const isChecked = this.checked;
            
            // Collect all website IDs from rows
            const websiteIds = [];
            rowCheckboxes.forEach(cb => {
                cb.checked = isChecked;
                const tr = cb.closest('tr');
                if (tr) {
                    const actionInput = tr.querySelector('input.action-select');
                    if (actionInput && actionInput.value) {
                        websiteIds.push(actionInput.value);
                    }
                }
            });

            // Send instant bulk AJAX update
            fetch('/admin/haberler/federasyonwebsite/toggle-all-aktif/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({
                    aktif: isChecked,
                    website_ids: websiteIds
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    showToast(isChecked ? '✅ Tüm siteler AKTİF duruma getirildi! (Anlık Kaydedildi)' : '⚠️ Tüm siteler PASİF duruma getirildi! (Anlık Kaydedildi)', true);
                } else {
                    showToast('❌ Güncelleme hatası: ' + (data.message || 'Bilinmeyen hata'), false);
                }
            })
            .catch(err => {
                showToast('💥 Bağlantı hatası: ' + err, false);
            });
        });

        // Prevent header sorting click when clicking master checkbox wrapper
        wrapper.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        // Individual Row Checkbox Single Toggle Action
        rowCheckboxes.forEach(cb => {
            cb.addEventListener('change', function() {
                const tr = this.closest('tr');
                if (!tr) return;
                const actionInput = tr.querySelector('input.action-select');
                if (!actionInput || !actionInput.value) return;

                const websiteId = actionInput.value;
                const isChecked = this.checked;

                // Sync Master Checkbox state
                masterCheckbox.checked = rowCheckboxes.every(c => c.checked);

                // Send instant single AJAX update
                fetch('/admin/haberler/federasyonwebsite/toggle-aktif/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrftoken
                    },
                    body: JSON.stringify({
                        website_id: websiteId,
                        aktif: isChecked
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        showToast(isChecked ? '✅ Site AKTİF edildi (Anlık Kaydedildi)' : '⚠️ Site PASİF edildi (Anlık Kaydedildi)', true);
                    } else {
                        showToast('❌ Güncelleme hatası', false);
                    }
                })
                .catch(err => {
                    showToast('💥 Bağlantı hatası', false);
                });
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', setupFederasyonAktifToggle);
