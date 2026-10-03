document.addEventListener('DOMContentLoaded', function () {
    // --- DETAILED LOGGING ENGINE ---
    function logInteraction(message) {
        const payload = {
            message: `[JS_GOZCU] ${message} | Browser: ${navigator.userAgent.substring(0, 50)} | URL: ${window.location.search || '/'}`
        };
        fetch('/api/news/log_activity/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        }).catch(e => console.error("Logging failed", e));
    }

    logInteraction("Giriş Yapıldı - Sayfa Yüklendi");

    const newsContainer = document.getElementById('news-container');
    const featuredContainer = document.getElementById('featured-container');
    const featuredSection = document.getElementById('featured-section');
    const sliderContainer = document.getElementById('conbg');
    const sidebarCategories = document.getElementById('sidebar-categories');
    const navBranches = document.getElementById('nav-branches');
    const btnLoadMore = document.getElementById('btn-load-more');
    const loadMoreContainer = document.getElementById('load-more-container');

    const api_news_url = '/api/news/';
    const api_categories_url = '/api/categories/';

    let nextUrl = null;

    const urlParams = new URLSearchParams(window.location.search);
    const catFilter = urlParams.get('category');
    const searchFilter = urlParams.get('search');
    const colFilter = urlParams.get('columnists');

    if (searchFilter && document.getElementById('search-info')) {
        document.getElementById('search-info').style.display = 'block';
        document.getElementById('search-term').innerText = searchFilter;
        logInteraction(`Arama Yapıldı: "${searchFilter}"`);
    }

    if (colFilter && document.querySelector('h1.display-4')) {
        document.querySelector('h1.display-4').innerHTML = 'GÜNÜN <span class="text-danger">KÖŞE YAZILARI</span>';
        logInteraction("Köşe Yazıları Filtrelendi");
    }

    // Load Categories & Active Federations Count
    fetch(api_categories_url + '?_t=' + Date.now(), { cache: 'no-store' })
        .then(r => r.json())
        .then(data => {
            const categories = data.results || data;
            if (!Array.isArray(categories)) return;

            const activeCount = data.active_count !== undefined ? data.active_count : categories.length;
            const navBranchBtn = document.getElementById('navbarDropdownBranches');
            if (navBranchBtn) {
                navBranchBtn.innerHTML = `🏆 BRANŞLAR & FEDERASYONLAR (${activeCount})`;
            }

            let sidebarHtml = '';
            let navHtml = '';
            let badgeHtml = '<span class="badge bg-secondary text-white me-2 px-3 py-2 font-black italic">FEDERASYONLAR:</span>';
            badgeHtml += `<a href="/" class="btn btn-outline-danger btn-sm rounded-pill text-white me-2 px-3 py-1 font-bold" onclick="logInteraction('Tüm Haberler')">TÜM HABERLER</a>`;

            categories.forEach(cat => {
                const linkUrl = cat.slug ? `/kategori/${cat.slug}/` : `/?category=${cat.id}`;
                sidebarHtml += `<li><a href="${linkUrl}" class="text-dark text-decoration-none border-bottom pb-1 d-block w-100 hover-red mb-2" onclick="logInteraction('Kategori Seçildi: ${cat.name}')">🥊 ${cat.name}</a></li>`;
                navHtml += `<li><a class="dropdown-item text-white hover-red" href="${linkUrl}" onclick="logInteraction('Navbar Kategori Seçildi: ${cat.name}')">🏆 ${cat.name}</a></li>`;
                badgeHtml += `<a href="${linkUrl}" class="btn btn-outline-light btn-sm rounded-pill me-2 px-3 py-1 font-bold text-white hover-red" style="border-color: rgba(255,255,255,0.2);" onclick="logInteraction('Federasyon Bar Seçildi: ${cat.name}')">🥊 ${cat.name}</a>`;
            });

            if (sidebarCategories) sidebarCategories.innerHTML = sidebarHtml;
            if (navBranches) navBranches.innerHTML = navHtml;
            const fedBar = document.getElementById('federation-badges-container');
            if (fedBar) fedBar.innerHTML = badgeHtml;
        }).catch(e => console.error("Categories failed", e));

    function loadNews(url, append = false) {
        if (!url) return;

        if (append && btnLoadMore) {
            btnLoadMore.disabled = true;
            btnLoadMore.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> YÜKLENİYOR...';
        }

        const cacheBustUrl = url + (url.includes('?') ? '&' : '?') + '_t=' + Date.now();
        fetch(cacheBustUrl, { cache: 'no-store' })
            .then(response => {
                if (!response.ok) throw new Error(`Server returned ${response.status}`);
                return response.json();
            })
            .then(data => {
                const news = data.results || [];
                nextUrl = data.next;

                if (loadMoreContainer) {
                    if (nextUrl) {
                        loadMoreContainer.style.display = 'block';
                        if (btnLoadMore) {
                            btnLoadMore.disabled = false;
                            btnLoadMore.innerHTML = 'DAHA FAZLA HABER YÜKLE ↓';
                        }
                    } else {
                        if (append && btnLoadMore) {
                            btnLoadMore.disabled = true;
                            btnLoadMore.innerHTML = 'TÜM HABERLER YÜKLENDİ ✓';
                        } else if (news.length <= 24) {
                            loadMoreContainer.style.display = 'none';
                        }
                    }
                }

                if (data.breaking_news && data.breaking_news.length > 0) {
                    const marqueeEl = document.querySelector('marquee');
                    if (marqueeEl) {
                        marqueeEl.innerHTML = data.breaking_news.join(' ... | ') + ' ...';
                    }
                }

                if (news.length === 0 && !append) {
                    if (newsContainer) newsContainer.innerHTML = '<p class="text-center p-5 font-black italic">ARADIĞINIZ HABER BULUNAMADI.</p>';
                    if (featuredContainer) featuredContainer.innerHTML = '';
                    if (sliderContainer) sliderContainer.style.display = 'none';
                    return;
                }

                // Initial load: Slider and Featured
                const categoryColorClasses = {
                    'EKONOMİ': 'color-azure-radiance',
                    'SİYASET': 'color-web-orange',
                    'SPOR': 'color-apple',
                    'GÜNCEL': 'color-cinnabar',
                    'EĞİTİM': 'color-cod-gray'
                };

                let sliderCount = 0;
                if (!append) {
                    // SLIDER LOGIC (v2.0 UI: 15 Slider Capacity + Ad Interleaving + Side 3 Cards)
                    const hasFilter = (catFilter && catFilter !== 'null') || (searchFilter && searchFilter !== '') || (colFilter && colFilter !== 'null');
                    const hasHeroData = Array.isArray(data.slider_items) && data.slider_items.length > 0;

                    if (!hasFilter && sliderContainer && (hasHeroData || news.length > 0)) {
                        sliderContainer.style.display = 'block';
                        
                        let sliderRawItems = hasHeroData ? data.slider_items : news.slice(0, Math.min(news.length, 15));
                        sliderCount = sliderRawItems.length;

                        // Merge Slider Ads (slider_1 ... slider_10) if present in data.ads
                        const adsMap = data.ads || {};
                        let finalSliderSlides = [];
                        
                        for (let i = 0; i < sliderRawItems.length; i++) {
                            const sliderAdKey = `slider_${i + 1}`;
                            if (adsMap[sliderAdKey]) {
                                const ad = adsMap[sliderAdKey];
                                finalSliderSlides.push({
                                    is_ad: true,
                                    id: 'ad_' + (i + 1),
                                    title: ad.baslik,
                                    image: ad.image || '/static/img/logo_5.png',
                                    hedef_url: ad.hedef_url || '#',
                                    iframe_goster: ad.iframe_goster,
                                    category_name: 'REKLAM'
                                });
                            }
                            finalSliderSlides.push(sliderRawItems[i]);
                        }
                        finalSliderSlides = finalSliderSlides.slice(0, 15);
                        
                        let navHtml = '';
                        let sliderHtml = '';
                        
                        finalSliderSlides.forEach((item, index) => {
                            const activeClass = index === 0 ? 'active' : '';
                            navHtml += `<li class="custom-nav-item ${activeClass}" data-slide="${index}">${index + 1}</li>`;
                            
                            const catName = (item.category_name || 'GÜNCEL').toUpperCase();
                            const colorClass = item.is_ad ? 'bg-danger text-white' : (categoryColorClasses[catName] || 'color-cinnabar');
                            
                            let dateStr = '';
                            if (item.created_at || item.olusturma_tarihi) {
                                const rawDate = item.created_at || item.olusturma_tarihi;
                                try {
                                    const dateObj = new Date(rawDate);
                                    const options = { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
                                    dateStr = dateObj.toLocaleDateString('tr-TR', options);
                                } catch (e) {
                                    dateStr = rawDate;
                                }
                            }

                            if (item.is_ad) {
                                let mediaContent = '';
                                if (item.iframe_goster && item.hedef_url) {
                                    mediaContent = `<iframe src="${item.hedef_url}" title="${item.title}" style="width:100%; height:100%; border:none;"></iframe>`;
                                } else {
                                    mediaContent = `<img src="${item.image}" alt="${item.title}" onerror="this.onerror=null;this.src='/static/img/logo_5.png';">`;
                                }

                                sliderHtml += `
                                    <div class="item position-relative">
                                        <a href="${item.hedef_url}" target="_blank" class="img-opacity-hover w-100 h-100 d-block" onclick="logInteraction('Slider Reklamı Tıklandı')">
                                            ${mediaContent}
                                            <div class="custom-slider-content">
                                                <div class="custom-slider-inner">
                                                    <div class="topic-box-top-xs position-relative top-0 start-0">
                                                        <div class="topic-box-sm bg-danger text-white">SPONSORLU REKLAM</div>
                                                    </div>
                                                    <h5>${item.title}</h5>
                                                    <p class="mb-0 small"><i class="fas fa-external-link-alt"></i> ${item.hedef_url}</p>
                                                </div>
                                            </div>
                                        </a>
                                    </div>
                                `;
                            } else {
                                sliderHtml += `
                                    <div class="item position-relative">
                                        <a href="/post.html?id=${item.id}" class="img-opacity-hover" onclick="logInteraction('Slider Haberi Okunuyor ID: ${item.id}')">
                                            <img src="${item.image || '/static/img/logo_5.png'}" alt="news" onerror="this.onerror=null;this.src='/static/img/logo_5.png';">
                                            <div class="custom-slider-content">
                                                <div class="custom-slider-inner">
                                                    <div class="topic-box-top-xs position-relative top-0 start-0">
                                                        <div class="topic-box-sm ${colorClass}">${catName}</div>
                                                    </div>
                                                    <h5>${item.title}</h5>
                                                    <p class="mb-0 small"><i class="far fa-clock"></i> ${dateStr}</p>
                                                </div>
                                            </div>
                                        </a>
                                    </div>
                                `;
                            }
                        });
                        
                        document.getElementById('custom-slider-nav').innerHTML = navHtml;
                        document.getElementById('custom-haber-slider').innerHTML = sliderHtml;

                        // Render Right Side 3 Sub-Cards Container
                        const sideContainer = document.getElementById('side-featured-container');
                        if (sideContainer) {
                            const sideItems = (hasHeroData && Array.isArray(data.side_items) && data.side_items.length > 0)
                                ? data.side_items
                                : news.slice(sliderCount, sliderCount + 3);
                            let sideHtml = '';
                            sideItems.forEach(sItem => {
                                const sCat = (sItem.category_name || 'GÜNCEL').toUpperCase();
                                const sColor = categoryColorClasses[sCat] || 'color-cinnabar';
                                sideHtml += `
                                    <div class="side-featured-card">
                                        <div class="side-featured-img">
                                            <img src="${sItem.image || '/static/img/logo_5.png'}" alt="${sItem.title}" onerror="this.onerror=null;this.src='/static/img/logo_5.png';">
                                            <span class="topic-box-sm ${sColor}" style="position: absolute; top: 6px; left: 6px; font-size: 9px; padding: 2px 6px;">${sCat}</span>
                                        </div>
                                        <div class="side-featured-body">
                                            <h4 class="side-featured-title">
                                                <a href="/post.html?id=${sItem.id}">${sItem.title}</a>
                                            </h4>
                                            <div class="d-flex justify-content-between align-items-center text-muted small" style="font-size: 11px;">
                                                <span><i class="far fa-clock text-danger me-1"></i> SPOR24</span>
                                                <div class="d-flex align-items-center gap-2">
                                                    <button class="btn btn-sm btn-link text-muted p-0 text-decoration-none card-share-btn" onclick="openShareModal(event, '${(sItem.title || '').replace(/'/g, "\\'")}', 'https://spor24.net/post.html?id=${sItem.id}')" title="Paylaş">
                                                        <i class="fas fa-share-nodes text-danger"></i>
                                                    </button>
                                                    <a href="/post.html?id=${sItem.id}" class="text-danger font-bold text-decoration-none">Oku <i class="fas fa-chevron-right ms-1"></i></a>
                                                </div>
                                            </div>
                                        </div>
                                    </div>`;
                            });
                            sideContainer.innerHTML = sideHtml;
                        }
                        
                        // Initialize Owl Carousel
                        const owl = $('#custom-haber-slider').owlCarousel({
                            items: 1,
                            loop: finalSliderSlides.length > 1,
                            margin: 0,
                            nav: false,
                            dots: false,
                            autoplay: true,
                            autoplayTimeout: 5000,
                            smartSpeed: 800,
                            onChanged: function(event) {
                                if (!event.namespace || event.property.name !== 'position') return;
                                
                                const count = event.item.count;
                                if (count === 0) return;
                                
                                let current = event.item.index;
                                const related = event.relatedTarget;
                                const clonesCount = (related && typeof related.clones === 'function') ? related.clones().length : 0;
                                if (clonesCount > 0) {
                                    current = current - clonesCount / 2;
                                }
                                const relativeIndex = (current % count + count) % count;
                                
                                $('#custom-slider-nav li').removeClass('active');
                                $(`#custom-slider-nav li[data-slide="${relativeIndex}"]`).addClass('active');
                            }
                        });

                        // Left Navigation Click Event
                        $('#custom-slider-nav').off('click', 'li').on('click', 'li', function() {
                            const slideIndex = $(this).data('slide');
                            owl.trigger('to.owl.carousel', [slideIndex, 800]);
                        });
                        
                    } else {
                        if (sliderContainer) sliderContainer.style.display = 'none';
                    }

                    // Disable Sub-Manset Section to guarantee 100% 4-column cards (x x x x)
                    if (featuredSection) featuredSection.style.display = 'none';
                }

                // Grid News (PURE 4-COLUMN CARDS: X X X X)
                let gridHtml = append ? '' : '<div class="row tab-space8">';
                const hasFilterForGrid = (catFilter && catFilter !== 'null') || (searchFilter && searchFilter !== '') || (colFilter && colFilter !== 'null');
                const hasHeroData = Array.isArray(data.slider_items) && data.slider_items.length > 0;
                const startIdx = (!append && !hasFilterForGrid && !hasHeroData) ? sliderCount : 0;

                const pollsMap = data.polls || (data.poll ? { 'grid_3': data.poll } : {});
                const adsMap = data.ads || {};

                news.slice(startIdx).forEach((item, index) => {
                    const pollPosKey = `grid_${index + 1}`;
                    const adPosKey = `kart_${index + 1}`;

                    if (!append && adsMap[adPosKey]) {
                        const ad = adsMap[adPosKey];
                        let adMediaHtml = '';
                        if (ad.iframe_goster && ad.hedef_url) {
                            let embedSrc = ad.hedef_url;
                            if (embedSrc.includes('youtube.com') || embedSrc.includes('youtu.be')) {
                                const sep = embedSrc.includes('?') ? '&' : '?';
                                if (!embedSrc.includes('mute=')) {
                                    embedSrc += sep + 'mute=1&autoplay=1&enablejsapi=1';
                                }
                            } else if (embedSrc.includes('medya.spor24.net')) {
                                const sep = embedSrc.includes('?') ? '&' : '?';
                                if (!embedSrc.includes('mute=')) {
                                    embedSrc += sep + 'mute=1&muted=1';
                                }
                            }
                            adMediaHtml = `
                                <div class="ratio ratio-16x9 rounded overflow-hidden mb-2" style="height: 160px;">
                                    <iframe src="${embedSrc}" title="${ad.baslik}" allow="autoplay; muted; fullscreen" style="width: 100%; height: 100%; border: none;"></iframe>
                                </div>`;
                        } else {
                            const adImg = ad.image ? `${ad.image}?v=3` : '/static/img/logo_5.png';
                            adMediaHtml = `
                                <div class="position-relative overflow-hidden mb-2 rounded" style="height: 160px; background: #111;">
                                    <img src="${adImg}" alt="${ad.baslik}" class="w-100 h-100" style="object-fit: cover;" onerror="this.onerror=null;this.src='/static/img/logo_5.png';">
                                </div>`;
                        }

                        gridHtml += `
                        <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-12 mt-20 d-flex">
                            <div class="card-ad-premium w-100 d-flex flex-column p-3" style="background: linear-gradient(135deg, #111827 0%, #1f2937 100%); border-radius: 12px; border: 1px solid rgba(255,255,255,0.15); min-height: 280px; box-shadow: 0 4px 15px rgba(0,0,0,0.4);">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span class="badge bg-danger text-white font-weight-bold px-2 py-1" style="font-size: 10px; border-radius: 4px;"><i class="fas fa-ad me-1"></i> REKLAM</span>
                                    <span class="text-white-50 small" style="font-size: 10px;">SPOR24</span>
                                </div>
                                <a href="${ad.hedef_url || '#'}" target="_blank" class="text-decoration-none flex-grow-1 d-flex flex-column">
                                    ${adMediaHtml}
                                    <h4 class="text-white font-weight-bold my-2" style="font-size: 14px; line-height: 20px;">${ad.baslik}</h4>
                                    <div class="mt-auto pt-2 border-top border-secondary text-end">
                                        <span class="text-danger small font-weight-bold">Siteye Git <i class="fas fa-external-link-alt ms-1"></i></span>
                                    </div>
                                </a>
                            </div>
                        </div>`;
                    }

                    if (!append && pollsMap[pollPosKey]) {
                        const poll = pollsMap[pollPosKey];
                        let optionsHtml = '';
                        poll.choices.forEach(ch => {
                            optionsHtml += `
                            <div class="form-check p-2 mb-2 rounded border border-secondary text-white" style="cursor: pointer; background: rgba(255,255,255,0.08);" onclick="this.querySelector('input').checked=true">
                                <input class="form-check-input ms-1 me-2" type="radio" name="choice_id_${poll.id}" id="poll_${poll.id}_choice_${ch.id}" value="${ch.id}" required>
                                <label class="form-check-label small font-weight-bold text-white mb-0 ms-1" for="poll_${poll.id}_choice_${ch.id}">
                                    ${ch.text}
                                </label>
                            </div>`;
                        });

                        gridHtml += `
                        <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-12 mt-20 d-flex">
                            <div class="card-promotional-premium w-100 d-flex flex-column p-3" style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border-radius: 12px; border: 1px solid rgba(255,255,255,0.15); min-height: 280px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span class="badge bg-warning text-dark font-weight-bold px-2 py-1" style="font-size: 10px; border-radius: 4px;"><i class="fas fa-chart-bar me-1"></i> GÜNÜN ANKETİ</span>
                                    <span class="text-white-50 small" style="font-size: 10px;">SPOR24</span>
                                </div>
                                <h4 class="text-white font-weight-bold my-2" style="font-size: 14px; line-height: 20px;">${poll.question}</h4>
                                <div class="poll-card-body flex-grow-1 d-flex flex-column justify-content-center" id="grid-poll-body-${poll.id}">
                                    <form id="grid-poll-form-${poll.id}" onsubmit="submitGridPollJS(event, ${poll.id})">
                                        <div class="poll-options-list mb-3">
                                            ${optionsHtml}
                                        </div>
                                        <button type="submit" class="btn btn-warning btn-sm font-weight-bold w-100 text-dark py-2 rounded-pill">Oy Kullan <i class="fas fa-check-circle ms-1"></i></button>
                                    </form>
                                    <div id="grid-poll-results-${poll.id}" style="display: none;" class="mt-2"></div>
                                </div>
                            </div>
                        </div>`;
                    }

                    const catName = (item.category_name || 'GÜNCEL').toUpperCase();
                    const colorClass = categoryColorClasses[catName] || 'color-cinnabar';

                    let dateStr = '';
                    if (item.created_at || item.olusturma_tarihi) {
                        const rawDate = item.created_at || item.olusturma_tarihi;
                        try {
                            const dateObj = new Date(rawDate);
                            const options = { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
                            dateStr = dateObj.toLocaleDateString('tr-TR', options);
                        } catch (e) {
                            dateStr = rawDate;
                        }
                    }

                    gridHtml += `
                            <div class="col-xl-3 col-lg-3 col-md-6 col-sm-6 col-12 mt-20">
                                <div class="item-shadow-gray">
                                    <div class="position-relative">
                                        <div class="topic-box-top-xs">
                                            <div class="topic-box-sm ${colorClass} mb-20">${catName}</div>
                                        </div>
                                        <a href="/post.html?id=${item.id}" class="img-opacity-hover one_cikan_img" onclick="logInteraction('Grid Haberi Okunuyor ID: ${item.id}')">
                                            <img src="${item.image || '/static/img/logo_5.png'}" alt="${item.title}" class="img-fluid" onerror="this.onerror=null;this.src='/static/img/logo_5.png';">
                                        </a>
                                    </div>
                                    <div class="box-padding15 bg-body item-shadow-gray one_cikan">
                                        <div class="text-dark mb-10 d-flex justify-content-between align-items-center" style="font-size: 13px;">
                                            <span><i class="far fa-clock text-danger"></i> ${dateStr}</span>
                                            <button class="btn btn-sm btn-link text-muted p-0 text-decoration-none card-share-btn" onclick="openShareModal(event, '${(item.title || '').replace(/'/g, "\\'")}', 'https://spor24.net/post.html?id=${item.id}')" title="Haberi Paylaş">
                                                <i class="fas fa-share-nodes text-danger"></i> <span style="font-size: 11px; font-weight: 700;">Paylaş</span>
                                            </button>
                                        </div>
                                        <h3 class="title-medium-dark size-sm mb-10 haber_kisa">
                                            <a href="/post.html?id=${item.id}">${item.title}</a>
                                        </h3>
                                        <div class="d-flex justify-content-between align-items-center mt-2 pt-2" style="border-top: 1px solid rgba(255,255,255,0.06);">
                                            <span class="text-muted" style="font-size: 11px;">SPOR24</span>
                                            <span class="card-view-count" style="font-size: 12px; font-weight: 700; color: #f59e0b; display: inline-flex; align-items: center; gap: 4px;" title="Görüntülenme Sayısı">
                                                <i class="far fa-eye"></i> ${item.views || item.goruntulenme_sayisi || 1}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div> `;
                });

                if (!append && newsContainer) {
                    gridHtml += '</div>';
                    newsContainer.innerHTML = gridHtml;
                } else if (append && newsContainer) {
                    const row = newsContainer.querySelector('.row');
                    if (row) row.insertAdjacentHTML('beforeend', gridHtml);
                }
            })
            .catch(err => console.error('LoadNews Error:', err));
    }

    // Load Columnists Carousel (Yazarlar)
    const api_columnists_url = '/api/news/?is_columnist=1&page_size=12';
    
    function loadColumnists() {
        const carousel = $('#columnists-carousel');
        if (!carousel.length) return;
        
        fetch(api_columnists_url)
            .then(r => r.json())
            .then(data => {
                const items = data.results || [];
                if (items.length === 0) {
                    $('#columnists-section').hide();
                    return;
                }
                
                let html = '';
                items.forEach(item => {
                    let dateStr = '';
                    if (item.created_at) {
                        try {
                            const dateObj = new Date(item.created_at);
                            const options = { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' };
                            dateStr = dateObj.toLocaleDateString('tr-TR', options);
                        } catch (e) {
                            dateStr = item.created_at;
                        }
                    }
                    
                    const authorLink = item.author_username ? `/yazar/${item.author_username}/` : `/?search=${encodeURIComponent(item.author_name)}`;
                    
                    html += `
                        <div class="item">
                            <div class="yazarlar-card text-center p-3">
                                <div class="yazar-profile">
                                    <div class="yazar-photo-container mb-2">
                                        <a href="${authorLink}" title="${item.author_name} Arşivi">
                                            <img src="${item.author_image}" alt="${item.author_name}" class="yazar-photo" onerror="this.onerror=null;this.src='/static/newsbit/images/news/author-02.jpg';">
                                        </a>
                                    </div>
                                    <a href="${authorLink}" class="yazar-name font-black" title="${item.author_name}">
                                        ${item.author_name}
                                    </a>
                                    <div class="mt-2 mb-2">
                                        <a href="${authorLink}" class="btn btn-sm btn-outline-danger font-bold rounded-pill px-3 py-1 shadow-sm" style="font-size: 11px; border-width: 2px; text-transform: uppercase; display: inline-block;">
                                            <i class="fas fa-archive me-1"></i> Tüm Yazıları (Arşiv)
                                        </a>
                                    </div>
                                </div>
                                <div class="yazar-makale-box border-top pt-2 mt-2">
                                    <div class="makale-date">
                                        <i class="far fa-clock"></i> ${dateStr}
                                    </div>
                                    <h4 class="makale-title">
                                        <a href="/post.html?id=${item.id}" title="${item.title}">
                                            ${item.title}
                                        </a>
                                    </h4>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                carousel.html(html);
                
                // Initialize Owl Carousel for Columnists
                const owl = carousel.owlCarousel({
                    loop: items.length > 4,
                    margin: 20,
                    autoplay: true,
                    autoplayTimeout: 5000,
                    smartSpeed: 2000,
                    dots: false,
                    nav: false,
                    responsive: {
                        0: { items: 1 },
                        600: { items: 2 },
                        1000: { items: 3 },
                        1200: { items: 4 }
                    }
                });

                // Custom Navigation triggers
                $('#columnists-next-btn').off('click').on('click', function() {
                    owl.trigger('next.owl.carousel');
                });
                $('#columnists-prev-btn').off('click').on('click', function() {
                    owl.trigger('prev.owl.carousel');
                });
            })
            .catch(e => console.error("Columnists failed", e));
    }
    
    // Only load columnists carousel on home page when no search/category filter is active
    if (!catFilter && !searchFilter && !colFilter) {
        loadColumnists();
    } else {
        $('#columnists-section').hide();
    }

    let initialUrl = api_news_url + '?page_size=45&';
    if (catFilter) initialUrl += `category=${catFilter}&`;
    if (searchFilter) initialUrl += `search=${searchFilter}&`;
    if (colFilter) initialUrl += `is_columnist=1&`;
    loadNews(initialUrl);

    if (btnLoadMore) {
        btnLoadMore.addEventListener('click', () => {
            logInteraction("Daha Fazla Haber butonuna basıldı");
            if (nextUrl) {
                let internalNext = nextUrl;
                try {
                    const parsed = new URL(nextUrl, window.location.origin);
                    internalNext = parsed.pathname + parsed.search;
                } catch(e) {
                    internalNext = nextUrl.replace('https://127.0.0.1:8000', '').replace('https://' + window.location.host, '');
                }
                loadNews(internalNext, true);
            }
        });
    }

    window.logInteraction = logInteraction;

    window.submitGridPollJS = function(e, pollId) {
        e.preventDefault();
        const form = document.getElementById('grid-poll-form-' + pollId);
        if (!form) return;
        const selected = form.querySelector(`input[name="choice_id_${pollId}"]:checked`);
        if (!selected) {
            alert('Lütfen bir seçenek işaretleyin.');
            return;
        }

        const getCookie = function(name) {
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
        };

        fetch('/anket/' + pollId + '/oy/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') || ''
            },
            body: JSON.stringify({ choice_id: parseInt(selected.value) })
        })
        .then(r => r.json())
        .then(data => {
            if (data.results) {
                form.style.display = 'none';
                const resContainer = document.getElementById('grid-poll-results-' + pollId);
                resContainer.style.display = 'block';
                let total = data.results.reduce((acc, curr) => acc + curr.votes, 0);
                let html = '<div class="results-list text-start py-2">';
                data.results.forEach(res => {
                    html += `
                    <div class="mb-2">
                        <div class="d-flex justify-content-between text-white small font-weight-bold mb-1">
                            <span>🔹 ${res.text}</span>
                            <span class="text-warning">%${res.percentage} (${res.votes} oy)</span>
                        </div>
                        <div class="progress" style="height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">
                            <div class="progress-bar bg-warning" role="progressbar" style="width: ${res.percentage}%"></div>
                        </div>
                    </div>`;
                });
                html += `<div class="text-end small text-muted font-weight-bold mt-2" style="font-size: 11px;">Toplam: ${total} Oy</div></div>`;
                if (!data.success && data.message) {
                    html += `<div class="alert alert-warning py-1 px-2 small text-center mt-2 mb-0" style="font-size: 11px;">${data.message}</div>`;
                }
                resContainer.innerHTML = html;
            } else if (data.message) {
                alert(data.message);
            }
        })
        .catch(err => {
            console.error('Poll vote error:', err);
            alert('Oy gönderilirken bir hata oluştu.');
        });
    };
});
