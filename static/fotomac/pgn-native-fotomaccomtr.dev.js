var googletag = googletag || {}; googletag.cmd = googletag.cmd || [];

var PgnNParams = PgnNParams || {};
PgnNParams.PGNN_PREBID_TIMEOUT = 750;
PgnNParams.FAILSAFE_TIMEOUT = 751;
PgnNParams.PGNNATIVE_NUMBER = 0;
PgnNParams.PGNNINPROGRESS = 0;
PgnNParams.PGNNEWSITEMS = new Array();
PgnNParams.PGNNEWSITEMS_ORG = new Array();
PgnNParams.PGNSTARTURL = document.location.href;
PgnNParams.PGNN_VGN_TIMEELAPSED = 0;
PgnNParams.PGNN_HBCREATIVESTACK = new Array();
PgnNParams.PGNN_ACTIVE = 1;
PgnNParams.initNativeImmediatelly = ["gunes.com", "m.gunes.com", "aksam.com.tr", "m.aksam.com.tr","star.com.tr","m.star.com.tr"];
PgnNParams.dummyImageSrc = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAAXNSR0IArs4c6QAAAA1JREFUGFdj+P///38ACfsD/QVDRcoAAAAASUVORK5CYII=";
PgnNParams.pgnNativeViewedSlots = new Array();
PgnNParams.pgnNativeViewableOffset = 1500;
PgnNParams.pgnnDebugScreenVisible = 0;
PgnNParams.pgnnOutstreamInterval = -1;
PgnNParams.pgnnVignetteDelayFirstAd = 3000;
PgnNParams.pgnnVignetteDelayOtherAds = 60000;
PgnNParams.pgnnVignetteCookieTimeout = 600000;
PgnNParams.pgnnVignetteLimitInFc = 2;
PgnNParams.pgnnVignetteEventsBinded = 0;

PgnNParams.pgnnDomains = [
    "pigeoon-native.b-cdn.net",
    "ahaber.com.tr",
    "sabah.com.tr",
    "test.sabah.com.tr",
    "test2.sabah.com.tr",
    "m.sabah.com.tr",
    "fotomac.com.tr",
    "takvim.com.tr",
    "prodtest.takvim.com.tr",
    "aspor.com.tr",
    "apara.com.tr",
    "yeniasir.com.tr",
    "atv.com.tr",
    "rotaborsa.com",
    "haberler.com",
    "kampanyaradar.com",
    "sondakika.com",
    "odatv.com",
    "dunya.com",
    "t24.com.tr",
    "teststage.t24.com.tr",
    "astroloji.co",
    "aksam.com.tr",
    "m.aksam.com.tr",
    "morpapatyaekstra.aksam.com.tr",
    "kadin.aksam.com.tr",
    "ruyatabirleri.aksam.com.tr",
    "sporekstra.aksam.com.tr",
    "ajans.aksam.com.tr",
    "quiz.aksam.com.tr",
    "star.com.tr",
    "m.star.com.tr",
    "gunes.com",
    "m.gunes.com",
    "yirmidort.tv",
    "24radyo.com",
    "tercuman.com",
    "tv360.com.tr",
    "tv4.com.tr",
    "alem.com.tr",
    "platinonline.com",
    "alemfm.com"
]
PgnNParams.pgnPrcRange = {
    "buckets": [
        {
            "precision": 2,
            "min": 0,
            "max": 1,
            "increment": 0.01
        },
        {
            "precision": 2,
            "min": 1,
            "max": 10,
            "increment": 0.10
        },
        {
            "precision": 2,
            "min": 10,
            "max": 100,
            "increment": 1.00
        },
        {
            "precision": 2,
            "min": 100,
            "max": 1000,
            "increment": 10.00
        }
    ]
};
PgnNParams.PrebidConfigUserSync = {
    syncEnabled: true,
    iframeEnabled: true,
    syncsPerBidder: 3,
    syncDelay: 3000,
    filterSettings: {
        iframe: {
            bidders: '*',
            filter: 'include'
        }
    },
    userIds: [
        {
            name: "pubCommonId",
            storage: { type: "cookie", name: "_pubCommonId", expires: 1825 }
        },
        {
            name: "id5id",
            params: { partner: 653 },
            storage: { type: "html5", name: "id5id", expires: 45, refreshInSeconds: 8 * 3600 }
        },
        {
            name: "unifiedId",
            params: {
                url: "//match.adsrvr.org/track/rid?ttd_pid=owaep76&fmt=json"
            },
            storage: {
                type: "cookie",
                name: "pbjs-unifiedid",
                expires: 60
            }
        },
        {
            name: "criteo",
        },
        {
            name: 'teadsId',
            params: {
                pubId: 23360
            }
        }
    ],
    auctionDelay: 50
};

PgnNParams.PrebidConfigCurrency = {
    "adServerCurrency": "TRY",
    "defaultRates": { "USD": { "TRY": 37 } }
};
PgnNParams.PrebidConfigAllowActivities = {
    accessDevice: {
        default: true,
        rules: [{
            allow: true
        }]
    },
    transmitTids: {
        default: true,
        rules: [{
            allow: true
        }]
    },
    transmitEids: {
        rules: [{
            allow: true
        }]
    },
    enrichEids: {
        rules: [{
            allow: true
        }]
    }
};


PgnNParams.pgnnSlotSizeArr__d_ba = [['fluid']];
PgnNParams.pgnnSlotSizeArr__d_ba_fw = [['fluid']];
PgnNParams.pgnnSlotSizeArr__m_ba = [['fluid'], [300, 250]];
PgnNParams.pgnnSlotSizeArr__m_ba_sm_list = [[300, 250]];
PgnNParams.pgnnSlotSizeArr__d_masthead = [[970, 250], [970, 90]];
PgnNParams.pgnnSlotSizeArr__m_masthead = [[300, 250], [320, 100]];
PgnNParams.pgnnSlotSizeArr__d_vignette = [[800, 600], [640, 480]];
PgnNParams.pgnnSlotSizeArr__m_vignette = [[320, 480], [300, 250]];
PgnNParams.pgnnSlotSizeArr__d_sticky_bottom = [[728, 90], [970, 90]];
PgnNParams.pgnnSlotSizeArr__m_sticky_bottom = [[320, 100], [300, 100]];
PgnNParams.pgnnSlotSizeArr__d_sticky_top = [[320, 100], [320, 50], [300, 100]];
PgnNParams.pgnnSlotSizeArr__m_sticky_top = [[320, 100], [320, 50], [300, 100]];
PgnNParams.pgnnSlotSizeArr__m_showcase = [[300, 250], [336, 280]];
PgnNParams.pgnnSlotSizeArr__d_showcase = [[300, 250], [336, 280]];
PgnNParams.pgnnSlotSizeArr__d_sidebar = [['fluid']];
PgnNParams.pgnnSlotSizeArr__m_sidebar = [['fluid']];

PgnNParams.pgnnFlNotAllowedSortOrders__d_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__d_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__d_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__d_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__d_ba_fw = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__d_ba_fw = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__d_ba_fw = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__d_ba_fw = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__m_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__m_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__m_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__m_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__m_ba_sm_list = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__m_ba_sm_list = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__m_ba_sm_list = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__m_ba_sm_list = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__m_sidebar = [1];
PgnNParams.pgnnFlAllowedSortOrders__m_sidebar = [2];
PgnNParams.pgnnAdxNotAllowedSortOrders__m_sidebar = [1];
PgnNParams.pgnnAdxAllowedSortOrders__m_sidebar = [2];
PgnNParams.pgnnFlNotAllowedSortOrders__d_sidebar = [];
PgnNParams.pgnnFlAllowedSortOrders__d_sidebar = [1, 2];
PgnNParams.pgnnAdxNotAllowedSortOrders__d_sidebar = [];
PgnNParams.pgnnAdxAllowedSortOrders__d_sidebar = [1, 2];

PgnNParams.pgnnTitleLength__d_ba = 50;
PgnNParams.pgnnBodyLength__d_ba = 0;
PgnNParams.pgnnTitleLength__d_ba_fw = 70;
PgnNParams.pgnnBodyLength__d_ba_fw = 0;
PgnNParams.pgnnTitleLength__m_ba = 100;
PgnNParams.pgnnBodyLength__m_ba = 0;
PgnNParams.pgnnTitleLength__m_ba_sm_list = 1000;
PgnNParams.pgnnBodyLength__m_ba_sm_list = 0;
PgnNParams.pgnnTitleLength__d_sidebar = 45;
PgnNParams.pgnnBodyLength__d_sidebar = 0;
PgnNParams.pgnnTitleLength__m_sidebar = 45;
PgnNParams.pgnnBodyLength__m_sidebar = 0;

PgnNParams.pgnnNativeImageParams__d_ba = [{ min_width: 250, min_height: 250, ratio_width: 1, ratio_height: 1 }];
PgnNParams.pgnnNativeImageParams__d_ba_fw = [{ min_width: 500, min_height: 250, ratio_width: 1.9, ratio_height: 1 }];
PgnNParams.pgnnNativeImageParams__m_ba = [{ min_width: 500, min_height: 500, ratio_width: 1, ratio_height: 1 }];
PgnNParams.pgnnNativeImageParams__m_ba_sm_list = [{ min_width: 200, min_height: 200, ratio_width: 1, ratio_height: 1 }];
PgnNParams.pgnnNativeImageParams__d_sidebar = [{ min_width: 100, min_height: 100, ratio_width: 1, ratio_height: 1 }];
PgnNParams.pgnnNativeImageParams__m_sidebar = [{ min_width: 200, min_height: 200, ratio_width: 1, ratio_height: 1 }];
PgnNParams.pgnnNativeImageParams__d_masthead = [];
PgnNParams.pgnnNativeImageParams__m_masthead = [];
PgnNParams.pgnnNativeImageParams__d_vignette = [];
PgnNParams.pgnnNativeImageParams__m_vignette = [];
PgnNParams.pgnnNativeImageParams__d_sticky_bottom = [];
PgnNParams.pgnnNativeImageParams__m_sticky_bottom = [];
PgnNParams.pgnnNativeImageParams__d_sticky_top = [];
PgnNParams.pgnnNativeImageParams__m_sticky_top = [];
PgnNParams.pgnnNativeImageParams__m_showcase = [];
PgnNParams.pgnnNativeImageParams__d_showcase = [];

PgnNParams.hidden = undefined;
PgnNParams.visibilityChange = undefined;
//If you want to override global params, define in here
PgnNParams.PBJSINSTANCE_NAME = "pbjs";
PgnNParams.WidgetTitle = 'İlginizi Çekebilir';
PgnNParams.WidgetBrandText = 'Native Ads By Turkuvaz Media';
PgnNParams.WidgetBrandUrl = 'https://www.fotomac.com.tr';
PgnNParams.WidgetLogoUrl = ''; // 'https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png'; //If logo exists, Widget Brand won't be used
PgnNParams.TrackNewsClick = false;
PgnNParams.MbaBgColor = "inherit";
PgnNParams.MbaSmListBgColor = "inherit";
PgnNParams.DbaBgColor = "inherit";
PgnNParams.DbaFwBgColor = "inherit";
PgnNParams.DbaFwHeaderBgColor = "inherit";
PgnNParams.DbaObjectFit = "inherit";
PgnNParams.pgnNativeViewableOffset = 2500;

PgnNParams.UseParentPrebidConfig = true;
PgnNParams.useCMP = false;
PgnNParams.pgnnNewsSourceType = "json";
PgnNParams.pgnnNewsSourceImagePlaceHolderSquare = "imageUrl";
PgnNParams.pgnnNewsSourceImagePlaceHolderWide = "imageUrl";
PgnNParams.pgnnNewsSourceTitlePlaceHolder = "title";
PgnNParams.pgnnNewsSourceDescriptionPlaceHolder = "description";
PgnNParams.pgnnNewsSourceClickUrlPlaceHolder = "clickUrl";

PgnNParams.pgnnHbAdvertisers = [5623484851];
PgnNParams.pgnnAdxOrders = [389705318];
PgnNParams.iframeSources = ["https://www.ahaber.com.tr", "https://www.sabah.com.tr","https://www.fotomac.com.tr"];
PgnNParams.pgnnRssLink = "https://www.fotomac.com.tr/json/most-read";

PgnNParams.pgnnSlotSizeArr__d_ba = [['fluid']];
PgnNParams.pgnnSlotSizeArr__d_ba_fw = [['fluid']];
PgnNParams.pgnnSlotSizeArr__m_ba = [['fluid'], [300, 250]];
PgnNParams.pgnnSlotSizeArr__m_ba_sm_list = [[300, 250]];
PgnNParams.pgnnSlotSizeArr__d_masthead = [[970, 250], [970, 90]];
PgnNParams.pgnnSlotSizeArr__m_masthead = [[300, 250], [320, 100]];
PgnNParams.pgnnSlotSizeArr__d_vignette = [[800, 600], [640, 480]];
PgnNParams.pgnnSlotSizeArr__m_vignette = [[320, 480], [300, 250]];
PgnNParams.pgnnSlotSizeArr__d_sticky_bottom = [[728, 90], [970, 90]];
PgnNParams.pgnnSlotSizeArr__m_sticky_bottom = [[728, 90], [970, 90]];
PgnNParams.pgnnSlotSizeArr__d_sticky_top = [[320, 100], [320, 50], [300, 100]];
PgnNParams.pgnnSlotSizeArr__m_sticky_top = [[320, 100], [320, 50], [300, 100]];
PgnNParams.pgnnSlotSizeArr__m_showcase = [[300, 250], [336, 280]];
PgnNParams.pgnnSlotSizeArr__d_showcase = [[300, 250], [336, 280]];
PgnNParams.pgnnSlotSizeArr__d_sidebar = [['fluid']];
PgnNParams.pgnnSlotSizeArr__d_sidebar_big = [['fluid']];
PgnNParams.pgnnSlotSizeArr__m_sidebar = [['fluid']];

PgnNParams.pgnnFlNotAllowedSortOrders__d_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__d_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__d_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__d_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__d_ba_fw = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__d_ba_fw = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__d_ba_fw = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__d_ba_fw = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__m_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__m_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__m_ba = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__m_ba = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__m_ba_sm_list = [2, 4, 6, 8, 10];
PgnNParams.pgnnFlAllowedSortOrders__m_ba_sm_list = [1, 3, 5, 7, 9];
PgnNParams.pgnnAdxNotAllowedSortOrders__m_ba_sm_list = [2, 4, 6, 8, 10];
PgnNParams.pgnnAdxAllowedSortOrders__m_ba_sm_list = [1, 3, 5, 7, 9];
PgnNParams.pgnnFlNotAllowedSortOrders__m_sidebar = [1];
PgnNParams.pgnnFlAllowedSortOrders__m_sidebar = [2];
PgnNParams.pgnnAdxNotAllowedSortOrders__m_sidebar = [1];
PgnNParams.pgnnAdxAllowedSortOrders__m_sidebar = [2];
PgnNParams.pgnnFlNotAllowedSortOrders__d_sidebar = [];
PgnNParams.pgnnFlAllowedSortOrders__d_sidebar = [1, 2];
PgnNParams.pgnnAdxNotAllowedSortOrders__d_sidebar = [];
PgnNParams.pgnnAdxAllowedSortOrders__d_sidebar = [1, 2];

PgnNParams.SlotRenderEndedFixMbaShowcase = true;
PgnNParams.SlotRenderEndedFixMbaNative = true;

function pgnnGetNativeMediaType(ortbVer, rendererUrl) {
    var mt = {
        sendTargetingKeys: false,
        rendererUrl: rendererUrl,
        ortb: {
            ver: "1.2",
            context: 1,
            plcmttype: 2,
            privacy: 1,
            assets: [{
                id: 1,
                required: 1,
                img: {
                    type: 3,
                    w: 100,
                    h: 100,
                }
            },
            {
                id: 2,
                required: 1,
                title: {
                    len: 80,
                }
            },
            {
                id: 3,
                required: 0,
                data: {
                    type: 1
                }
            },
            {
                id: 4,
                required: 0,
                data: {
                    type: 2
                }
            },
            {
                id: 5,
                required: 0,
                data: {
                    type: 6
                }
            },
            {
                id: 6,
                required: 0,
                data: {
                    type: 12
                }
            }
            ],
            eventtrackers: [{
                event: 1, methods: [1, 2]
            }]
        }
    }
    if (ortbVer == "1.1") {
        mt = {
            sendTargetingKeys: false,
            rendererUrl: rendererUrl,
            image: {
                required: true,
                sendId: true
            },
            title: {
                required: false,
                len: 100,
                sendId: true
            },
            clickUrl: {
                required: false,
                sendId: true
            },
            displayUrl: {
                required: false,
                sendId: true
            },
            privacyLink: {
                required: false,
                sendId: true
            },
            privacyIcon: {
                required: false,
                sendId: true
            },
            body: {
                required: false,
                len: 100,
                sendId: true
            },
            icon: {
                required: false,
                sendId: true
            },
            cta: {
                required: false,
                sendId: true
            },
            sponsoredBy: {
                required: false,
                sendId: true
            }
        }
    }
    return mt;
} 

function pgnnPartialCreateParamsObj(renderOrder, formats, unitName, ros, widgetType, scheme, overridedSlotPath, adUnitOrder, nativeOrtbVer, adUnitPath, triggerType, cellPadding, outStreamSlotId) {
    const paramsObj = {
        _renderOrder: renderOrder,
        _formats: formats,
        _unitName: unitName,
        _ros: ros,
        _widgetType: widgetType,
        _scheme: scheme,
        _overrideSlotPath: overridedSlotPath,
        _adUnitOrder: adUnitOrder,
        _nativeOrtbVer: nativeOrtbVer,
        _adUnitPath: adUnitPath,
        _triggerType: triggerType,
        _cellPadding: cellPadding,
        _outStreamSlotId: outStreamSlotId
    };

    //Override parameters
    if (formats == undefined || formats == "")
        paramsObj._formats = "n,n,n|n,n,n";
    if (cellPadding == undefined || cellPadding == "")
        paramsObj._cellPadding = 10;
    return paramsObj;
}

function pgnnPartialGetBidderObjects(_widgetType, _format, _sortOrder) {
    var returnBidObjects = new Array();

    var yandexBidObjArr = [
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '1' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '2' },
        { bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '3' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '4' },
        { bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '5' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '6' },
        { bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '7' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '8' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba-fw', format: 'n', sortOrder: '9' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'm-ba', format: 'n,d,b', sortOrder: '1' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'm-ba', format: 'n,d,b', sortOrder: '2' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'm-ba', format: 'n,d,b', sortOrder: '3' },
        //{ bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'm-ba', format: 'n,d,b', sortOrder: '4' },
        { bidder: 'yandex', params: { pageId: 1819780, impId: 1 }, widgetType: 'd-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '7,8,9,10,11,12,13,14,15,16' }
    ];
    var rtbHouseBidObjArr = [
        { bidder: 'rtbhouse', params: { region: 'prebid-eu', publisherId: '365b81345b61d1a75ytw' }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var adtelligentBidObjArr = [
        { bidder: 'adtelligent', params: { aid: 810492 }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var ixBidObjArr = [
        { bidder: 'ix', params: { siteId: '939378' }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var rubiconBidObjArr = [
        { bidder: 'rubicon', params: { accountId: 20686, siteId: 298742, zoneId: 2260336 }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var teadsBidObjArr = [
        { bidder: 'teads', params: { placementId: '176155', pageId: '161494' }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var smartAdserverBidObjArr = [
        { bidder: 'smartadserver', params: { siteId: 332578, pageId: 1516044, formatId: 84323 }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var adfBidObj = [
        { bidder: 'adf', params: { mid: 748470 }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var pixadBidAdapter = [
        { bidder: 'pixad', params: { networkId: 8877472719, host: 'turkuvaz.rtb.pixad.com.tr' }, widgetType: 'd-ba,d-ba-fw,m-ba,m-ba-sm-list,d-sidebar,m-sidebar,d-masthead,m-masthead,d-vignette,m-vignette,d-sticky-top,m-sticky-top,d-sticky-bottom,m-sticky-bottom,d-showcase,m-showcase', format: 'n,d,b', sortOrder: '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16' }
    ];
    var containerArr = [
        yandexBidObjArr,
        rtbHouseBidObjArr,
        adtelligentBidObjArr,
        ixBidObjArr,
        rubiconBidObjArr,
        teadsBidObjArr,
        smartAdserverBidObjArr,
        adfBidObj,
        pixadBidAdapter
    ];

    //If all needed params are exists, then select proper bidObject item from array. Else, select only first item per [bidder]ObjArr
    for (let k = 0; k < containerArr.length; k++) {
        var objArr = containerArr[k];
        var tempObj = new Array();
        for (let i = 0; i < objArr.length; i++) {
            var item = objArr[i];
            if (item.hasOwnProperty('sortOrder') && item.hasOwnProperty('widgetType') && item.hasOwnProperty('format')) {
                var widgetTypeArr = item.widgetType.split(',');
                var formatArr = item.format.split(',');
                var sortOrderArr = item.sortOrder.split(',');
                if (widgetTypeArr.includes(_widgetType) && formatArr.includes(_format) && sortOrderArr.indexOf(_sortOrder.toString()) != undefined && sortOrderArr.indexOf(_sortOrder.toString()) > -1) {
                    tempObj.push(item);
                    returnBidObjects.push(item);
                    break;
                }
            }
        }
        if (tempObj.length == 0) {
            //returnBidObjects.push(objArr[0]);
        }
    }

    return returnBidObjects;
}

function pgnnPartialSetAdUnitPaths() {
    if (window.location.href.includes("/galeri/")) {
        PgnNParams.pgnnPath__m_ba = "/31110078,22727463451/fotomac/mobile_web/galeri/native";
        PgnNParams.pgnnPath__d_ba = "/31110078,22727463451/fotomac/desktop_web/galeri/native";
        PgnNParams.pgnnPath__d_ba_fw = "/31110078,22727463451/fotomac/desktop_web/galeri/native";
        PgnNParams.pgnnPath__m_sidebar = "/31110078,22727463451/fotomac/mobile_web/galeri/native_advertorial";
        PgnNParams.pgnnPath__d_sidebar = "/31110078,22727463451/fotomac/desktop_web/galeri/native_advertorial";
        PgnNParams.pgnnPath__m_masthead = "/31110078,22727463451/fotomac/mobile_web/galeri/native";
        PgnNParams.pgnnPath__d_masthead = "/31110078,22727463451/fotomac/desktop_web/galeri/native";
        PgnNParams.pgnnPath__m_vignette = "/31110078,22727463451/fotomac/mobile_web/galeri/native";
        PgnNParams.pgnnPath__d_vignette = "/31110078,22727463451/fotomac/desktop_web/galeri/native";
        PgnNParams.pgnnPath__d_sticky_top = "/31110078,22727463451/fotomac/desktop_web/galeri/native";
        PgnNParams.pgnnPath__m_sticky_top = "/31110078,22727463451/fotomac/mobile_web/galeri/native";
        PgnNParams.pgnnPath__d_sticky_bottom = "/31110078,22727463451/fotomac/desktop_web/galeri/native";
        PgnNParams.pgnnPath__m_sticky_bottom = "/31110078,22727463451/fotomac/mobile_web/galeri/native";
        PgnNParams.pgnnPath__m_showcase = "/31110078,22727463451/fotomac/mobile_web/galeri/300x250";
        PgnNParams.pgnnPath__d_showcase = "/31110078,22727463451/fotomac/desktop_web/galeri/300x250";
    } else {
        PgnNParams.pgnnPath__m_ba = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/native";
        PgnNParams.pgnnPath__d_ba = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native";
        PgnNParams.pgnnPath__d_ba_fw = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native";
        PgnNParams.pgnnPath__m_sidebar = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/native_advertorial";
        PgnNParams.pgnnPath__d_sidebar = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native_advertorial";
        PgnNParams.pgnnPath__m_masthead = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/native";
        PgnNParams.pgnnPath__d_masthead = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native";
        PgnNParams.pgnnPath__m_vignette = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/native";
        PgnNParams.pgnnPath__d_vignette = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native";
        PgnNParams.pgnnPath__d_sticky_top = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native";
        PgnNParams.pgnnPath__m_sticky_top = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/native";
        PgnNParams.pgnnPath__d_sticky_bottom = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/native";
        PgnNParams.pgnnPath__m_sticky_bottom = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/native";
        PgnNParams.pgnnPath__m_showcase = "/31110078,22727463451/fotomac/mobile_web/sitegeneli/300x250";
        PgnNParams.pgnnPath__d_showcase = "/31110078,22727463451/fotomac/desktop_web/sitegeneli/300x250";
    }
}
window[PgnNParams.PBJSINSTANCE_NAME] = window[PgnNParams.PBJSINSTANCE_NAME] || {};
window[PgnNParams.PBJSINSTANCE_NAME].que = window[PgnNParams.PBJSINSTANCE_NAME].que || [];
//timelog eklendi 11-09-2024
var PgnN = (function () {
    'use strict';

    function timeLog(message) {
        var currentdate = new Date();
        var datetime = "PgnNativeLogv2 => " + message + " => " + currentdate.getDate() + "/"
            + (currentdate.getMonth() + 1) + "/"
            + currentdate.getFullYear() + " @ "
            + currentdate.getHours() + ":"
            + currentdate.getMinutes() + ":"
            + currentdate.getSeconds() + ":"
            + currentdate.getMilliseconds();
        console.log(datetime);
    }

    function getQueryStringByName(name, url = window.location.href) {
        name = name.replace(/[\[\]]/g, '\\$&');
        var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
            results = regex.exec(url);
        if (!results) return null;
        if (!results[2]) return '';
        return decodeURIComponent(results[2].replace(/\+/g, ' '));
    }

    function pgnNLog(message) {
        if (getCookie('pgnndebug') == '1' || getQueryStringByName('pgnnconsole') == '1') {
            console.log("PgnNLog => " + message);
            if (getQueryStringByName('pgnnconsole') == '1') {
                if (document.getElementById('pgnnDebugContainer') == null) {
                    const pgnnDebugContainer = document.createElement('div');
                    pgnnDebugContainer.setAttribute('id', 'pgnnDebugContainer');
                    pgnnDebugContainer.style.position = 'sticky';
                    pgnnDebugContainer.style.backgroundColor = 'red';
                    pgnnDebugContainer.style.padding = '20px';
                    pgnnDebugContainer.style.width = '100%';
                    //pgnnDebugContainer.style.height = '250px';
                    pgnnDebugContainer.style.bottom = '0px';
                    pgnnDebugContainer.style.textAlign = 'center';
                    pgnnDebugContainer.style.zIndex = '9999999999999';
                    document.body.appendChild(pgnnDebugContainer);

                    const pgnnDebugTextArea = document.createElement('textarea');
                    pgnnDebugTextArea.setAttribute('id', 'pgnnDebugTextArea');
                    pgnnDebugTextArea.setAttribute('rows', '15');
                    pgnnDebugTextArea.style.width = '90%';
                    pgnnDebugTextArea.style.backgroundColor = 'white';
                    pgnnDebugTextArea.style.fontSize = '12px';
                    pgnnDebugTextArea.style.fontWeight = 'normal';
                    pgnnDebugContainer.appendChild(pgnnDebugTextArea);
                    PgnNParams.pgnnDebugScreenVisible = 1;
                }
            }
        }

        if (PgnNParams.pgnnDebugScreenVisible == 1) {
            document.getElementById('pgnnDebugTextArea').value = document.getElementById('pgnnDebugTextArea').value + "PgnNLog => " + message + '\r\n';
        }
    }

    function generateRandomString(length) {
        var result = '';
        var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
        var charactersLength = characters.length;
        for (var i = 0; i < length; i++) {
            result += characters.charAt(Math.floor(Math.random() * charactersLength));
        }
        return result;
    }

    function isMobile() {
        var scrw = screen.width;
        if (document.body && document.body.offsetWidth) {
            scrw = document.body.offsetWidth;
        }
        if (document.compatMode == 'CSS1Compat' && document.documentElement && document.documentElement.offsetWidth) {
            scrw = document.documentElement.offsetWidth;
        }
        if (window.innerWidth && window.innerHeight) {
            scrw = window.innerWidth;
        }
        var isMobile = false;
        if (/ip(hone|od)|blackberry|android|windows (ce|phone)|symbian|avantgo|blazer|compal|elaine|fennec|hiptop|iemobile|iris|kindle|lge |maemo|midp|mmp|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\/|plucker|pocket|psp|symbian|treo/i.test(navigator.userAgent)) {
            isMobile = true;
        }

        return ((scrw < 1024) || isMobile);
    }

    function isIpad() {
        if (navigator.userAgent.match(/Mac/) && navigator.maxTouchPoints && navigator.maxTouchPoints > 2) {
            return true;
        }
        return false;
    }

    function createTargetingKeys(paramsObj, adIds) {
        var returnList = new Array();
        returnList.push({ key: "pgnNative", val: '1' });
        returnList.push({ key: "pgnNativeNumber", val: PgnNParams.PGNNATIVE_NUMBER });
        returnList.push({ key: 'kv_invtype', val: 'web,pgnNative' });

        if (adIds != null && adIds != undefined) {
            for (var x = 0; x < adIds.length; x++) {
                returnList.push({ key: "pgnNativeDivId", val: adIds[x] });
            }
        }

        if (paramsObj._widgetType != undefined && paramsObj._widgetType != null) {
            returnList.push({ key: "pgnNativeWidget", val: paramsObj._widgetType });
        }

        var containerDivId = adIds[0].split("_")[0];
        var widgetContainerWidth = document.getElementById(containerDivId).innerWidth || document.getElementById(containerDivId).clientWidth || document.getElementById(containerDivId).clientWidth;
        var colCount = parseInt((paramsObj._scheme.split("|")[0]).split(",").length);
        var cellPaddingWidth = parseInt(paramsObj._cellPadding);
        var totalCellPaddingWitdh = colCount * 2 * cellPaddingWidth;
        var nativeStyleWidth = parseInt((widgetContainerWidth - totalCellPaddingWitdh) / colCount) + cellPaddingWidth; //neden? :)

        if (nativeStyleWidth >= 250) {
            returnList.push({ key: "pgnNativeStyleW", val: '250' });
        }
        else if (nativeStyleWidth < 250 && nativeStyleWidth >= 240) {
            returnList.push({ key: "pgnNativeStyleW", val: '240' });
        }
        else if (nativeStyleWidth < 240 && nativeStyleWidth >= 230) {
            returnList.push({ key: "pgnNativeStyleW", val: '230' });
        }
        else if (nativeStyleWidth < 230 && nativeStyleWidth >= 220) {
            returnList.push({ key: "pgnNativeStyleW", val: '220' });
        }
        else if (nativeStyleWidth < 220 && nativeStyleWidth >= 210) {
            returnList.push({ key: "pgnNativeStyleW", val: '210' });
        }
        else if (nativeStyleWidth < 210 && nativeStyleWidth >= 200) {
            returnList.push({ key: "pgnNativeStyleW", val: '200' });
        }
        else if (nativeStyleWidth < 200 && nativeStyleWidth >= 190) {
            returnList.push({ key: "pgnNativeStyleW", val: '190' });
        }
        else if (nativeStyleWidth < 190 && nativeStyleWidth >= 180) {
            returnList.push({ key: "pgnNativeStyleW", val: '180' });
        }
        else if (nativeStyleWidth < 180 && nativeStyleWidth >= 170) {
            returnList.push({ key: "pgnNativeStyleW", val: '170' });
        }


        try {
            if (getCookie('prdCnAudience') != null) {
                let items = JSON.parse(getCookie('prdCnAudience'));
                if (items != null) {
                    var aud_values = new Array();
                    for (const [key, value] of Object.entries(items)) {
                        aud_values.push(key.replace("prd_", "").replace("prd_", "").replace("prd_", ""));
                    }
                    returnList.push({ key: "prd_audience", val: aud_values });
                }
            }
        }
        catch (err) {
            console.error('PgnNative error when creating targeting keys! ' + err.message);
        }
        return returnList;
    }

    function getUserSegments() {
        var returnList = new Array();
        var currentSegmentObj = new Object();
        if (getCookie('prdCnSgv2') != null) {
            let items = JSON.parse(getCookie('prdCnSgv2'));

            if (items != null && items.w != null && items.w.length > 5) {
                let ws = items.w.split(",");
                if (ws != null && ws.length > 0) {
                    for (let i = 0; i < ws.length; i++) {
                        currentSegmentObj[("prd_w_" + ws[i].split("#")[0]).toString()] = (ws[i].split("#")[1]).toString();
                        /*returnList.push(currentSegmentObj);*/
                    }
                }
            }
            if (items != null && items.c != null && items.c.length > 5) {
                let wc = items.c.split(",");
                if (wc != null && wc.length > 0) {
                    for (let i = 0; i < wc.length; i++) {
                        currentSegmentObj[("prd_c_" + wc[i].split("#")[0]).toString()] = (wc[i].split("#")[1]).toString();
                        /*returnList.push(currentSegmentObj);*/
                    }
                }
            }
            if (items != null && items.kc != null && items.kc.length > 5) {
                let wkc = items.kc.split(",");
                if (wkc != null && wkc.length > 0) {
                    for (let i = 0; i < wkc.length; i++) {
                        currentSegmentObj[("prd_kc_" + wkc[i].split("#")[0]).toString()] = (wkc[i].split("#")[1]).toString();
                        let key = "prd_kc_" + wkc[i].split("#")[0];
                        let value = wkc[i].split("#")[1];
                        /*returnList.push(currentSegmentObj);*/
                    }
                }
            }
        }
        returnList.push(currentSegmentObj);
        return returnList;
    }

    function getCookie(cname) {
        let name = cname + "=";
        let decodedCookie = decodeURIComponent(document.cookie);
        let ca = decodedCookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            while (c.charAt(0) == ' ') {
                c = c.substring(1);
            }
            if (c.indexOf(name) == 0) {
                return c.substring(name.length, c.length);
            }
        }
        return null;
    }

    function setCookie(cname, cvalue, miliSeconds) {
        const d = new Date();
        d.setTime(d.getTime() + (miliSeconds));
        let expires = "expires=" + d.toUTCString();
        document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
    }

    function getOrtb2Values() {
        var obj = {
            site: {
                name: document.location.host,
                domain: document.location.host,
                page: window.location.href.toString(),
                ref: window.location.href.toString(),
                /*keywords: "gundem, cumhurbaskani, secim",*/
                cat: ["IAB2"],
                sectioncat: ["IAB2-2"],
                pagecat: ["IAB2-2"],
                content: {
                    data: [{
                        name: document.location.host,
                        /*ext: { segtax: 7, cids: [ "iris_c73g5jq96mwso4d8" ] },
                        segment: getUserSegments()*/
                    }]
                },
            },
            user: {
                data: [{
                    name: document.location.host,
                    ext: { segtax: 4 },
                    /*segment: getUserSegments(),*/
                }],
                ext: {
                    /*data: {registered: true, interests: ["cars,sports"]}*/
                }
            }
        };
        return obj;
    }

    function getAdunitPath(widget, format, sortOrder) {
        return PgnNParams["pgnnPath__" + widget.replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_")];
    }

    function initNativeAds(divId) {
        PgnN.TimeLog("initNativeAds=>Start!");
        if (PgnNParams.pgnNativeViewedSlots.includes(divId)) {
            PgnN.PgnNLog("Already worked initNativeAds for divId=" + divId);
        } else {
            PgnNParams.pgnNativeViewedSlots.push(divId);
            pgnnPartialSetAdUnitPaths();
            PgnN.PgnNLog("initNativeAds divId=" + divId);
            fetch(PgnNParams.pgnnRssLink, {
                method: 'GET'
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    PgnNParams.PGNNEWSITEMS_ORG = data;
                    PgnNParams.PGNNEWSITEMS = shuffleArray(data);

                    PgnNParams.PGNNATIVE_NUMBER++;
                    var itm = document.getElementById(divId);

                    var renderOrder = itm.getAttribute('pgn-native-rndrOrd');//p, p-g, g-p
                    var formats = itm.getAttribute('pgn-native-f') == null ? "" : itm.getAttribute('pgn-native-f');
                    var unitName = itm.getAttribute('pgn-native-unit');
                    var ros = itm.getAttribute('pgn-native-ros');
                    var widgetType = itm.getAttribute('pgn-native-w');
                    var scheme = itm.getAttribute('pgn-native-scheme');
                    var overridedSlotPath = itm.getAttribute('pgn-native-slot');
                    var adUnitOrder = ((itm.getAttribute('pgn-native-order') != null && itm.getAttribute('pgn-native-order') != undefined) ? itm.getAttribute('pgn-native-order') : 1)
                    var nativeOrtbVer = itm.getAttribute('pgn-native-ortb-ver');
                    var adUnitPath = (overridedSlotPath != undefined && overridedSlotPath != null) ? overridedSlotPath : getAdunitPath(widgetType, unitName, ros);
                    var triggerType = itm.getAttribute('pgn-native-trgType'); //instant,scroll
                    var cellPadding = itm.getAttribute('pgn-native-cp');
                    var outStreamSlotId = itm.getAttribute('pgn-native-outstream-slot')
                    var paramsObj = pgnnPartialCreateParamsObj(renderOrder, formats, unitName, ros, widgetType, scheme, overridedSlotPath, adUnitOrder, nativeOrtbVer, adUnitPath, triggerType, cellPadding, outStreamSlotId);

                    var widgetObj = generatePgnnWidget(divId, paramsObj);
                    document.getElementById(divId).innerHTML = widgetObj.content;

                    //Get news if newsBlock needed
                    if (widgetObj.newsIds.length > 0) {
                        if (PgnNParams.pgnnNewsSourceType == "xml") {
                            generateNewsXml(widgetObj.newsIds, paramsObj);
                        }
                        else if (PgnNParams.pgnnNewsSourceType == "json") {
                            generateNewsJson(widgetObj.newsIds, paramsObj);
                        }
                    }
                    //generate iframe widgets
                    if (widgetObj.iframeIds.length > 0) {
                        generateIframes(widgetObj.iframeIds, paramsObj);
                    }

                    if (paramsObj._outStreamSlotId != null && paramsObj._outStreamSlotId != '') {
                        var placementId = paramsObj._outStreamSlotId;
                        PgnN.LoadScript('https://serving.stat-rock.com/player/pigeoon-outstream.js', function () {
                            PgnN.InitOutstreamAds(divId, placementId);
                        });
                    }

                    if (paramsObj._renderOrder == "p") {
                        makeAdRequestP(paramsObj, widgetObj);
                    }
                    else {
                        makeAdRequestGP(paramsObj, widgetObj);
                    }
                });
        }
    }

    function findAdUnitOrder(divId, widgetObj) {
        var result = 0;
        var arr = new Array();
        widgetObj.adIds.forEach(element => arr.push(element));
        widgetObj.newsIds.forEach(element => arr.push(element));
        widgetObj.iframeIds.forEach(element => arr.push(element));
        arr = arr.sort();
        for (var r = 0; r < arr.length; r++) {
            if (divId == arr[r]) {
                result = r + 1;
                break;
            }
        }
        return result;
    }

    function makeAdRequestGP(paramsObj, widgetObj) {
        PgnN.TimeLog("makeAdRequestGP=>Start");
        var hbUnitArray = new Array();
        var gptUnitArray = new Array();

        try {
            var slotSizeArr = [['fluid']];
            googletag.cmd.push(function () {

                for (let b = 0; b < widgetObj.adIds.length; b++) {
                    var sortOrder = findAdUnitOrder(widgetObj.adIds[b], widgetObj);
                    slotSizeArr = paramsObj._formats.replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").split(",")[sortOrder - 1] == "n" ? [['fluid']] : PgnNParams["pgnnSlotSizeArr__" + paramsObj._widgetType.replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_").replace("-", "_")];
                    var slot = googletag.defineSlot(paramsObj._adUnitPath + "_" + sortOrder, slotSizeArr, widgetObj.adIds[b]).addService(googletag.pubads());
                    //PgnN.PgnNLog("defineSlot: " + widgetObj.adIds[b] + " | path: " + paramsObj._adUnitPath);
                    if (paramsObj._widgetType == 'd-ba' || paramsObj._widgetType == 'd-ba-fw' || paramsObj._widgetType == 'm-ba-sm-list' || paramsObj._widgetType == 'm-ba') {
                        if (PgnNParams["pgnnFlNotAllowedSortOrders__" + paramsObj._widgetType.replace("-", "_").replace("-", "_").replace("-", "_")].indexOf(sortOrder) >= 0) {
                            slot.setTargeting('pgnAllowFl', "0");  //do not allow fl 
                        }
                        if (PgnNParams["pgnnFlAllowedSortOrders__" + paramsObj._widgetType.replace("-", "_").replace("-", "_").replace("-", "_")].indexOf(sortOrder) >= 0) {
                            slot.setTargeting('pgnAllowFl', "1");  //allow fl 
                        }
                        if (PgnNParams["pgnnAdxNotAllowedSortOrders__" + paramsObj._widgetType.replace("-", "_").replace("-", "_").replace("-", "_")].indexOf(sortOrder) >= 0) {
                            slot.setTargeting('pgnAllowAdx', "0");  //do not allow Adx 
                        }
                        if (PgnNParams["pgnnAdxAllowedSortOrders__" + paramsObj._widgetType.replace("-", "_").replace("-", "_").replace("-", "_")].indexOf(sortOrder) >= 0) {
                            slot.setTargeting('pgnAllowAdx', "1");  //allow Adx 
                        }
                    }
                    slot.setTargeting('pgnNativeDivId', slot.getSlotElementId());
                    gptUnitArray.push(slot);
                }

                googletag.pubads().addEventListener('slotRenderEnded', function (event) {
                    try {
                        var containerId = event.slot.getSlotElementId();
                        var containerEl = document.getElementById(containerId);
                        if (containerEl === null) return;

                        var slot = event.slot;
                        if (widgetObj.adIds.includes(slot.getSlotElementId())) {

                            if (event.isEmpty) {
                                if (paramsObj._widgetType == 'd-masthead'
                                    || paramsObj._widgetType == 'm-masthead'
                                    || paramsObj._widgetType == 'd-vignette'
                                    || paramsObj._widgetType == 'm-vignette'
                                    || paramsObj._widgetType == 'd-sticky-bottom'
                                    || paramsObj._widgetType == 'm-sticky-bottom'
                                    || paramsObj._widgetType == 'd-sticky-top'
                                    || paramsObj._widgetType == 'm-sticky-top'
                                    || paramsObj._widgetType == 'd-showcase'
                                    || paramsObj._widgetType == 'm-showcase'
                                ) {
                                    for (let i = 0; i < document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container').length; i++) {
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].parentElement.removeAttribute('id');
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].remove();
                                    }
                                }
                                else {
                                    var divsToHide = document.getElementById(containerId).querySelectorAll('[id^="google"]');
                                    divsToHide.forEach(box => {
                                        //box.style.display = "none";
                                    });
                                    document.getElementById(containerId).style.display = "block";//when slot unfilled prevent to make display:none by adserver
                                    var tempArr = new Array();
                                    tempArr.push(slot.getSlotElementId());
                                    var elementsToRemove = document.getElementById(slot.getSlotElementId()).querySelectorAll('.pgnn-ad-element');
                                    elementsToRemove.forEach(box => {
                                        box.remove();
                                    });

                                    if (PgnNParams.pgnnNewsSourceType == "xml") {
                                        generateNewsXml(tempArr, paramsObj);
                                    }
                                    else if (PgnNParams.pgnnNewsSourceType == "json") {
                                        generateNewsJson(tempArr, paramsObj);
                                    }
                                }
                            }
                            else if (!event.isEmpty) {
                                if (paramsObj._widgetType == "d-ba" || paramsObj._widgetType == "d-ba-fw") {
                                    PgnN.PgnNLog("slotId: " + slot.getSlotElementId() + " | path: " + slot.getAdUnitPath() + " | event.size: " + event.size[0] + "," + event.size[1] + " | creativeId: " + event.sourceAgnosticCreativeId);
                                }
                                else if (paramsObj._widgetType == 'm-ba') {
                                    PgnN.TimeLog("slotRenderEnded=> Fix Start");
                                    PgnN.TimeLog("pgnn: divId: " + slot.getSlotElementId() + " => event size: " + event.size[0] + "x" + event.size[1]);
                                    var elem = document.getElementById(slot.getSlotElementId());
                                    elem.style.display = "flex";
                                    elem.style.justifyContent = "center";
                                    var parentElem = elem.parentElement;
                                    var parentWidth = parentElem.offsetWidth;
                                    var cellContainerPadding = paramsObj._cellPadding;
                                    //document.getElementById(containerId).style.display = "flex";//when slot unfilled prevent to make display:none by adserver
                                    if (PgnNParams.SlotRenderEndedFixMbaShowcase) {
                                        if (event.size[0] == "300" || event.size[0] == "336") {
                                            elem.setAttribute("style", "border:1px solid #dedbd9;background-color:#f2f2f2;border-radius:4px;padding:10px 0 10px 0;width:" + (parentWidth - 2 * cellContainerPadding) + "px;display:flex;justify-content:center;margin-bottom:10px;margin-left:" + cellContainerPadding + "px;");
                                        }

                                    } else if (event.size[0] == "1") {
                                        var innerDiv = elem.getElementsByTagName("div")[0];
                                        var innerIframe = elem.getElementsByTagName("iframe")[0];
                                        innerDiv.style.width = (parentWidth - 2 * cellContainerPadding) + "px";
                                        innerIframe.style.width = (parentWidth - 2 * cellContainerPadding) + "px";
                                    }
                                    PgnN.TimeLog("slotRenderEnded=> Fix End");
                                }
                                else if (paramsObj._widgetType == 'm-ba-sm-list') {
                                    if (event.slot.getSizes()[0] != "fluid" && event.slot.getSizes()[0].width != undefined) {
                                        var mbaSmListFixInterval = window.setInterval(function () {
                                            setTimeout(function () { clearInterval(mbaSmListFixInterval); }, 2000);
                                            var containerW = document.getElementById(containerId).offsetWidth;
                                            var innerDiv = document.getElementById(containerId).children[0];
                                            var innerDivIframe = innerDiv.getElementsByTagName("iframe")[0];
                                            var left = (containerW - innerDivIframe.offsetWidth) / 2
                                            if (left > 10) {
                                                document.getElementById(containerId).children[0].style.position = "relative";
                                                document.getElementById(containerId).children[0].style.left = left + "px";
                                            }
                                        }, 100);
                                    }
                                    PgnN.PgnNLog("slotId: " + slot.getSlotElementId() + " | path: " + slot.getAdUnitPath() + " | event.size: " + event.size[0] + "," + event.size[1] + " | creativeId: " + event.sourceAgnosticCreativeId);
                                }
                                else if (paramsObj._widgetType == 'd-sidebar') {
                                    var elem = document.getElementById(slot.getSlotElementId());
                                    PgnN.PgnNLog("slotId: " + slot.getSlotElementId() + " | path: " + slot.getAdUnitPath() + " | event.size: " + event.size[0] + "," + event.size[1] + " | creativeId: " + event.sourceAgnosticCreativeId);

                                    if (event.size[0] == 0 || event.size[0] == 1 || event.size[0] == 2) {
                                        elem.getElementsByTagName("div")[0].style.width = elem.offsetWidth + "px";
                                        elem.getElementsByTagName("div")[0].style.minHeight = "80px";
                                        elem.getElementsByTagName("iframe")[0].style.width = elem.offsetWidth + "px";
                                        elem.getElementsByTagName("iframe")[0].style.minHeight = "80px";
                                    }

                                    PgnN.PgnNLog('pgnNative SlotElementId:' + event.slot.getSlotElementId() + ' => sizefix!');
                                }
                                else if (paramsObj._widgetType == 'm-sticky-bottom' || paramsObj._widgetType == 'd-sticky-bottom') {
                                    var elem = document.getElementById(slot.getSlotElementId());
                                    PgnN.PgnNLog("slotId: " + slot.getSlotElementId() + " | path: " + slot.getAdUnitPath() + " | event.size: " + event.size[0] + "," + event.size[1] + " | creativeId: " + event.sourceAgnosticCreativeId);
                                    for (let i = 0; i < document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container').length; i++) {
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].parentElement.style.display = 'flex';
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].style.display = 'flex';
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].style.justifyContent = 'center';
                                    }
                                }
                                else if (paramsObj._widgetType == 'd-masthead'
                                    || paramsObj._widgetType == 'm-masthead'
                                    || paramsObj._widgetType == 'd-vignette'
                                    || paramsObj._widgetType == 'm-vignette'
                                    || paramsObj._widgetType == 'd-sticky-top'
                                    || paramsObj._widgetType == 'd-showcase'
                                    || paramsObj._widgetType == 'm-showcase'
                                ) {
                                    for (let i = 0; i < document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container').length; i++) {
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].parentElement.style.display = 'flex';
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].style.display = 'flex';
                                        document.getElementsByClassName('pgnn-' + paramsObj._widgetType + '-container')[i].style.justifyContent = 'center';
                                    }
                                }
                            }
                        }
                    }
                    catch (exc) {
                        console.error('pgnNative Error when adjusting sizes!: ' + exc.message);
                    }
                });

                googletag.pubads().addEventListener("impressionViewable", (event) => {
                    var slot = event.slot;
                    if (widgetObj.adIds.includes(slot.getSlotElementId())) {
                        PgnN.TimeLog("impressionViewable=>" + slot.getSlotElementId());
                    }
                });

                googletag.pubads().addEventListener("impressionViewable", (event) => {
                    if ((getQueryStringByName('pgnnd') == '1')) {
                        PgnN.PgnNLog('Impression for slot ', event.slot.getSlotElementId(), ' became viewable.');
                    }
                });

                var prdKeys = createTargetingKeys(paramsObj, widgetObj.adIds);

                if (prdKeys.length > 0) {
                    for (let s = 0; s < prdKeys.length; s++) {
                        for (let v = 0; v < gptUnitArray.length; v++) {
                            if (!gptUnitArray[v].getTargetingKeys().includes(prdKeys[s].key)) {
                                gptUnitArray[v].setTargeting(prdKeys[s].key, prdKeys[s].val);
                            }
                        }
                    }
                }

                googletag.pubads().disableInitialLoad();

                googletag.pubads().enableSingleRequest();

                googletag.enableServices();

                window[PgnNParams.PBJSINSTANCE_NAME].que.push(function () {
                    PgnN.TimeLog("makeAdRequestGP=>que.push inside");
                    setupPbjs(paramsObj, hbUnitArray, widgetObj);
                    window[PgnNParams.PBJSINSTANCE_NAME].requestBids({
                        timeout: PgnNParams.PGNN_PREBID_TIMEOUT,
                        bidsBackHandler: function () {
                            window[PgnNParams.PBJSINSTANCE_NAME].setPAAPIConfigForGPT();
                            if (paramsObj._renderOrder == "p") {
                                renderpbjsAds(widgetObj.adIds);
                            } else if (paramsObj._renderOrder == "p-g") {
                                throw new Error('Not implemented yet! ' + paramsObj._widgetType + ' for divId ' + widgetObj.adIds[0]);
                            } else {
                                googletag.cmd.push(function () {
                                    window[PgnNParams.PBJSINSTANCE_NAME].que.push(function () {
                                        window[PgnNParams.PBJSINSTANCE_NAME].setTargetingForGPTAsync();
                                        for (let c = 0; c < widgetObj.adIds.length; c++) {
                                            googletag.display(widgetObj.adIds[c]);
                                        }
                                        PgnN.TimeLog("makeAdRequestGP=>googletag.pubads().refresh");
                                        googletag.pubads().refresh(gptUnitArray);
                                        PgnNParams.PGNNINPROGRESS = 0;
                                    });
                                });
                            }
                        },
                        bidderTimeout: PgnNParams.PGNN_PREBID_TIMEOUT
                    });
                });
            });
        } catch (err) {
            console.error(err.message);
        }
    }

    function makeAdRequestP(paramsObj, widgetObj) {
        var hbUnitArray = new Array();

        try {
            window[PgnNParams.PBJSINSTANCE_NAME].que.push(function () {

                setupPbjs(paramsObj, hbUnitArray, widgetObj);

                window[PgnNParams.PBJSINSTANCE_NAME].requestBids({
                    bidsBackHandler: function () {
                        if (paramsObj._renderOrder == "p") {
                            renderpbjsAds(widgetObj.adIds);
                        } else if (paramsObj._renderOrder == "p-g") {
                            throw new Error('Not implemented yet! ' + paramsObj._widgetType + ' for divId ' + widgetObj.adIds[0]);
                        } else {
                            googletag.cmd.push(function () {
                                window[PgnNParams.PBJSINSTANCE_NAME].que.push(function () {
                                    window[PgnNParams.PBJSINSTANCE_NAME].setTargetingForGPTAsync();
                                    for (let c = 0; c < widgetObj.adIds.length; c++) {
                                        googletag.display(widgetObj.adIds[c]);
                                    }
                                    googletag.pubads().refresh(gptUnitArray);
                                    PgnNParams.PGNNINPROGRESS = 0;
                                });
                            });
                        }
                    },
                    bidderTimeout: 0
                });
            });

        } catch (err) {
            console.error(err.message);
        }
    }

    function setupPbjs(paramsObj, hbUnitArray, widgetObj) {
        console.log("PgnNativeLogv2 => setupPbjs start!");
        if (paramsObj._widgetType == 'm-ba-sm-list'
            || paramsObj._widgetType == 'm-ba'
            || paramsObj._widgetType == 'd-ba'
            || paramsObj._widgetType == 'd-ba-fw'
            || paramsObj._widgetType == 'm-sidebar'
            || paramsObj._widgetType == 'd-sidebar'
            || paramsObj._widgetType == 'd-sidebar-big') {
            for (let a = 0; a < widgetObj.adIds.length; a++) {
                PgnN.PgnNLog("makeAdRequest for " + paramsObj._adUnitPath + " with divId " + widgetObj.adIds[a]);
                var sortOrder = findAdUnitOrder(widgetObj.adIds[a], widgetObj);
                var hbUnit = getHbAdunit(widgetObj, paramsObj._adUnitPath, paramsObj._formats.replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").split(",")[sortOrder - 1], paramsObj._nativeOrtbVer, widgetObj.adIds[a]);
                hbUnitArray.push(hbUnit);
                //if (paramsObj._formats.replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").split(",")[sortOrder - 1] == "b") {

                //var additionalHbUnit = getHbAdunit(widgetObj, paramsObj._adUnitPath, paramsObj._formats.replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").split(",")[sortOrder - 1], paramsObj._nativeOrtbVer, widgetObj.adIds[a]);
                //hbUnitArray.push(additionalHbUnit);
                //}
            }
        }
        else if (paramsObj._widgetType == 'd-masthead'
            || paramsObj._widgetType == 'm-masthead'
            || paramsObj._widgetType == 'd-vignette'
            || paramsObj._widgetType == 'm-vignette'
            || paramsObj._widgetType == 'd-sticky-bottom'
            || paramsObj._widgetType == 'm-sticky-bottom'
            || paramsObj._widgetType == 'd-sticky-top'
            || paramsObj._widgetType == 'm-sticky-top'
            || paramsObj._widgetType == 'd-showcase'
            || paramsObj._widgetType == 'm-showcase'
        ) {
            for (let a = 0; a < widgetObj.adIds.length; a++) {
                PgnN.PgnNLog("makeAdRequest for " + paramsObj._adUnitPath + "_" + (parseInt(paramsObj._adUnitOrder) + a) + " with divId " + widgetObj.adIds[a]);
                var sortOrder = findAdUnitOrder(widgetObj.adIds[a], widgetObj);
                var hbUnit = getHbAdunit(widgetObj, paramsObj._adUnitPath, paramsObj._formats.replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").replace("|", ",").split(",")[sortOrder - 1], paramsObj._nativeOrtbVer, widgetObj.adIds[a]);
                hbUnitArray.push(hbUnit);
            }
        }

        window[PgnNParams.PBJSINSTANCE_NAME].removeAdUnit();
        for (let b = 0; b < hbUnitArray.length; b++) {
            window[PgnNParams.PBJSINSTANCE_NAME].addAdUnits(hbUnitArray[b]);
        };
        if (window[PgnNParams.PBJSINSTANCE_NAME].adUnits != null && window[PgnNParams.PBJSINSTANCE_NAME].adUnits.length > 0) {
            for (let v = 0; v < window[PgnNParams.PBJSINSTANCE_NAME].adUnits.length; v++) {
                PgnN.TimeLog("setupPbjs=>Ad Units are: " + window[PgnNParams.PBJSINSTANCE_NAME].adUnits[v].code);
            }
        }
        if (!PgnNParams.UseParentPrebidConfig) {
            window[PgnNParams.PBJSINSTANCE_NAME].setConfig({
                enableTIDs: true,
                gptPreAuction: {
                    enabled: true
                },
                paapi: {
                    enabled: true,
                    defaultForSlots: 1
                },
                bidderTimeout: PgnNParams.PGNN_PREBID_TIMEOUT,
                debug: (PgnN.GetCookie('pgnndebug') == '1'),
                priceGranularity: PgnNParams.pgnPrcRange,
                currency: PgnNParams.PrebidConfigCurrency,
                enableSendAllBids: false,
                pubcid: { enable: true, expInterval: 525600 },
                allowActivities: PgnNParams.PrebidConfigAllowActivities,
                userSync: PgnNParams.PrebidConfigUserSync,
            });
            window[PgnNParams.PBJSINSTANCE_NAME].bidderSettings = {
                standard: {
                    storageAllowed: true,
                    bidCpmAdjustment: function (bidCpm, bid) {
                        var adjustedCpm = bidCpm * 1.18;
                        return adjustedCpm;
                    }
                }
            };
            window[PgnNParams.PBJSINSTANCE_NAME].setBidderConfig(PgnNParams.bidderConfig);
        }

        if (PgnNParams.useCMP) {
            var consentManagement = {};
            consentManagement.gdpr = {
                "cmpApi": "iab",
                "timeout": 10000,
                "defaultGdprScope": false
            };
            if (typeof __tcfapi === 'function') {
                PgnN.PgnNLog('CMP found setting up consentManagementModule config!');
                window[PgnNParams.PBJSINSTANCE_NAME].setConfig({ consentManagement });
            }
        }

        window[PgnNParams.PBJSINSTANCE_NAME].onEvent('adRenderFailed', function (data) {
            PgnN.PgnNLog('adRenderFailed: ' + data.adUnitCode + ' => ' + data.adId + ' => ' + data.bidderCode + ' => ' + data.cpm + ' ' + data.currency);
        });

        window[PgnNParams.PBJSINSTANCE_NAME].onEvent('adRenderSucceeded', function (data) {
            PgnN.PgnNLog('adRenderSucceed: ' + data.bid.adUnitCode + ' => ' + data.adId + ' => ' + data.bid.bidderCode + ' => ' + data.bid.cpm + ' ' + data.bid.currency);
            var div = document.getElementById(data.bid.adUnitCode);
            var width = data.bid.getSize().split("x")[0];
            var height = data.bid.getSize().split("x")[1];

            if (div.parentElement.parentElement.getAttribute("pgn-native-rndrOrd") == "p") {
                if (div.parentElement.parentElement.getAttribute("pgn-native-w") == "d-sticky-bottom" || div.parentElement.parentElement.getAttribute("pgn-native-w") == "m-sticky-bottom"
                    || div.parentElement.parentElement.getAttribute("pgn-native-w") == "d-sticky-top" || div.parentElement.parentElement.getAttribute("pgn-native-w") == "m-sticky-top"
                    || div.parentElement.parentElement.getAttribute("pgn-native-w") == "d-masthead" || div.parentElement.parentElement.getAttribute("pgn-native-w") == "m-masthead"
                    || div.parentElement.parentElement.getAttribute("pgn-native-w") == "d-showcase" || div.parentElement.parentElement.getAttribute("pgn-native-w") == "m-showcase") {
                    if (!isNaN(width) && !isNaN(height)) {
                        var innerIframe = document.getElementById(data.bid.adUnitCode).children[0];
                        document.getElementById(data.bid.adUnitCode).style.height = height + "px";
                        innerIframe.style.width = width + "px";
                        innerIframe.style.height = height + "px";
                        div.parentElement.style.display = "block";
                    }
                }
            }
            else if (div.parentElement.parentElement.parentElement.getAttribute("pgn-native-rndrOrd") == "p") {
                if (div.parentElement.parentElement.parentElement.getAttribute("pgn-native-w") == "d-vignette" || div.parentElement.parentElement.parentElement.getAttribute("pgn-native-w") == "m-vignette") {
                    if (!isNaN(width) && !isNaN(height)) {
                        var innerIframe = document.getElementById(data.bid.adUnitCode).children[0];
                        document.getElementById(data.bid.adUnitCode).style.height = height + "px";
                        innerIframe.style.width = width + "px";
                        innerIframe.style.height = height + "px";
                        div.parentElement.parentElement.style.display = "block";
                        setTimeout(function () { div.parentElement.parentElement.style.display = "block"; }, 500);
                    }
                }
            }
            else {
                if (data.bid.adUnitCode.includes("m-ba-sm-list")) {
                    //PgnN.FixSizeForAdUnit(width, height, data.bid.adUnitCode, data.bid.mediaType);
                } else if (data.bid.adUnitCode.includes("m-ba")) {
                    PgnN.FixSizeForAdUnit(width, height, data.bid.adUnitCode, data.bid.mediaType, paramsObj);
                }
            }

            //delete re-render old prebid bids due to refreshing slots
            var slotCount = googletag.pubads().getSlots().length;
            for (let c = 0; c < slotCount; c++) {
                if (data.bid.adUnitCode == googletag.pubads().getSlots()[c].getSlotElementId()) {
                    var slot = googletag.pubads().getSlots()[c];
                    for (let v = 0; v < slot.getTargetingKeys().length; v++) {
                        if (slot.getTargetingKeys()[v].includes("hb_pb")) {
                            //slot.setTargeting(slot.getTargetingKeys()[v],"-1");
                        }
                    }
                }
            }
        });

        window[PgnNParams.PBJSINSTANCE_NAME].onEvent('bidWon', function (data) {
            PgnN.PgnNLog('bidWon: ' + data.adUnitCode + ' => ' + data.adId + ' => ' + data.bidderCode + ' => ' + data.cpm + ' ' + data.currency);
        });

        window[PgnNParams.PBJSINSTANCE_NAME].onEvent('setTargeting', function (data) {
            PgnN.PgnNLog('setTargeting: ' + data);
        });

        window[PgnNParams.PBJSINSTANCE_NAME].onEvent('bidResponse', function (data) {
            PgnN.PgnNLog('bidResponse for ' + data.adUnitCode + ' => ' + data.adId + ' => ' + data.bidderCode + ' => ' + data.cpm + ' ' + data.currency);
        });

        window[PgnNParams.PBJSINSTANCE_NAME].onEvent('bidderError', function (error) {
            if (error != undefined && error.bidderRequest != undefined && error.bidderRequest.bidderCode != undefined) {
                PgnN.PgnNLog('bidderError: ' + error.bidderRequest.bidderCode + ' => Status: => ' + error.error.status + ' => Message: ' + error.error.statusText + ' => AuctionId: => ' + error.bidderRequest.auctionId);
            }
        });

    }

    function getBidderObjects(widgetObj, format, sortOrder) {
        var bidObjects = pgnnPartialGetBidderObjects(widgetObj.widgetType, format, sortOrder);
        return bidObjects;
    }

    function getHbAdunit(widgetObj, adUnitPath, format, nativeOrtbVer, divId) {
        var imageSize = [300, 300];
        var rendererUrl = "https://cdn-native.pigeoon.com/common/v8/nativerenderer-" + widgetObj.widgetType + "-v" + nativeOrtbVer.replace(".", "-").replace(".", "-").replace(".", "-") + ".js";

        var sortOrder = findAdUnitOrder(divId, widgetObj);
        var bidObjects = getBidderObjects(widgetObj, format, sortOrder);

        //to remove 'fluid' size
        var bannerSizeArr = PgnNParams["pgnnSlotSizeArr__" + widgetObj.widgetType.replace("-", "_").replace("-", "_").replace("-", "_")];
        var arrIndex = -1;
        for (var t = 0; t < bannerSizeArr.length; t++) {
            if (bannerSizeArr[t] != undefined && bannerSizeArr[t] == 'fluid')
                arrIndex = t;
        }
        if (arrIndex > -1)
            bannerSizeArr.splice(arrIndex, 1);
        var mediaTypeBanner = { sizes: bannerSizeArr };

        var mTypeNative = pgnnGetNativeMediaType(nativeOrtbVer, rendererUrl);
        var mediaTypeObj = format == 'n' ? { native: mTypeNative } : (format == 'b' ? { banner: mediaTypeBanner, native: mTypeNative } : { banner: mediaTypeBanner });

        PgnN.PgnNLog("adUnitPath.toString():" + adUnitPath.toString());
        var adUnits = [
            {
                code: divId,
                mediaTypes: mediaTypeObj,
                bids: bidObjects
            }
        ];

        return adUnits;
    }

    function initOutstreamAds(divId, placementId) {
        PgnN.PgnNLog("initOutstreamAds divId=" + divId + " ,placementId=" + placementId);

        var container = document.getElementById(divId).getElementsByClassName("pgnn-outstream-slot-inner")[0];
        if (container != null && container != undefined) {
            (AdPlayerPro = window.AdPlayerPro || []).push({ id: placementId, after: container, init: bindPlayerEvents });
        }
    }

    function bindPlayerEvents(api) {
        if (api) {
            api.on('AdLoaded', function () {
                PgnN.PgnNLog("PgnPlayer AdLoaded");
            });
            api.on('AdStarted', function () {

                PgnN.PgnNLog("PgnPlayer Ad  started");

                for (var r = 0; r < document.getElementsByClassName("pgnn-outstream-slot-inner").length; r++) {
                    var itm = document.getElementsByClassName("pgnn-outstream-slot-inner")[r];
                    itm.parentElement.style.marginBottom = "10px";
                }
                //fixPgnOutstreamZindex(1);
                //pgnnOutstreamInterval = setInterval(PgnOutstreamTick, 100);
                //function PgnOutstreamTick() {
                //    if (api.getAdRemainingTime() > 0) {
                //        fixPgnOutstreamZindex(1);
                //    }
                //}
            });
            api.on('AdVideoComplete', function () {
                for (var r = 0; r < document.getElementsByClassName("pgnn-outstream-slot-inner").length; r++) {
                    var itm = document.getElementsByClassName("pgnn-outstream-slot-inner")[r];
                    itm.parentElement.style.marginBottom = "inherit";
                }
                //fixPgnOutstreamZindex(0);
                //clearInterval(pgnnOutstreamInterval);
            });
            api.on('AdSkipped', function () {
                for (var r = 0; r < document.getElementsByClassName("pgnn-outstream-slot-inner").length; r++) {
                    var itm = document.getElementsByClassName("pgnn-outstream-slot-inner")[r];
                    itm.parentElement.style.marginBottom = "inherit";
                }
                //fixPgnOutstreamZindex(0);
                //clearInterval(pgnnOutstreamInterval);
            });
            api.on('AdStopped', function () {

            });
            api.on('AdPlaying', function () {
                //fixPgnOutstreamZindex(1);
            });
        } else {
            PgnN.PgnNLog("PgnPlayer Api Undefined!");
        }
    }

    function fixPgnOutstreamZindex(top) {
        if (top == 1) {
            if (document.location.host.includes('takvim')) {
                document.getElementsByClassName('column-right')[0].style.zIndex = 0;
            }
            if (document.getElementById('cornerstick') != null)
                document.getElementById('cornerstick').style.zIndex = 100;
            if (document.getElementsByClassName('pageSkinRight').length > 0)
                document.getElementsByClassName('pageSkinRight')[0].style.zIndex = 99;
            if (document.getElementsByClassName('pageSkinLeft').length > 0)
                document.getElementsByClassName('pageSkinLeft')[0].style.zIndex = 99;
        } else {
            if (document.location.host.includes('takvim')) {
                document.getElementsByClassName('column-right')[0].style.zIndex = null;
            }
            if (document.getElementById('cornerstick') != null)
                document.getElementById('cornerstick').style.zIndex = 997888;
            if (document.getElementsByClassName('pageSkinRight').length > 0)
                document.getElementsByClassName('pageSkinRight')[0].style.zIndex = 10004;
            if (document.getElementsByClassName('pageSkinLeft').length > 0)
                document.getElementsByClassName('pageSkinLeft')[0].style.zIndex = 10004;
        }
    }

    function generatePgnnWidget(divId, paramsObj) {
        //console.log("PgnNativeLogv2 => generatePgnnWidget start!");
        //widgetType, scheme
        var rowItems = new Array();
        var newsItems = new Array();

        var widgetObj = new Object();
        widgetObj.content = "";
        widgetObj.adIds = new Array();
        widgetObj.newsIds = new Array();
        widgetObj.iframeIds = new Array();
        widgetObj.widgetType = paramsObj._widgetType;

        //console.log("PgnNativeLogv2 => location " + document.location.host.replace("https://", "").replace("http://", "").replace("www", ""));
        if (PgnNParams.pgnnDomains.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
            //console.log("PgnNativeLogv2 => generatePgnnWidget start=>if true");
            //custom headers etc.
            if (paramsObj._widgetType == "d-ba") {
                var widgetWidth = document.getElementById(divId).offsetWidth;
                var cellPaddingLeft = paramsObj._cellPadding != null ? "padding-left: " + paramsObj._cellPadding + "px;" : "";
                var cellPaddingLRight = paramsObj._cellPadding != null ? "padding-right: " + paramsObj._cellPadding + "px;" : "";
                widgetObj.content += "<div style='width:" + widgetWidth + "px; height:30px; font-size:14px;font-weight:bold;'>";
                widgetObj.content += "<div style='" + cellPaddingLeft + "text-align:left; float:left;line-height:30px;height:30px;font-size:17px;'>" + PgnNParams.WidgetTitle.replace(/["�"]/g, "ç").replace("ï¿½", "ç").replace("Ã§Ã§Ã§", "ç") + "</div>";
                widgetObj.content += "<div style='float:right;height:30px;line-height:30px;'>";
                widgetObj.content += "<a style='" + cellPaddingLRight + "font-size:12px;text-decoration:none; color:#666666;font-weight:normal !important' target='_blank' href='" + PgnNParams.WidgetBrandUrl + "'>";
                if (PgnNParams.WidgetLogoUrl != null && PgnNParams.WidgetLogoUrl.length > 5) {
                    widgetObj.content += "<img style= 'width:30px;' src='" + PgnNParams.WidgetLogoUrl + "'>";
                } else if (PgnNParams.WidgetBrandText != null && PgnNParams.WidgetBrandText.length > 5) {
                    widgetObj.content += PgnNParams.WidgetBrandText;
                }
                widgetObj.content += "</a>";
                widgetObj.content += "</div>";
                widgetObj.content += "</div>";
            }
            else if (paramsObj._widgetType == "d-ba-fw") {
                widgetObj.content += "<table width='100%' style='background-color:" + PgnNParams.DbaFwHeaderBgColor + ";'><tbody><tr><td><hr></td><td style='width:1px;padding: 0 10px;font-size: 20px;white-space: nowrap;'>" + PgnNParams.WidgetTitle.replace(/["�"]/g, "ç") + "</td><td><hr></td></tr></tbody></table>";
                //set bg-color
                document.getElementById(divId).parentElement.style.backgroundColor = PgnNParams.DbaFwBgColor;
            }
            else if (paramsObj._widgetType == "m-ba") {
                //set bg-color
                document.getElementById(divId).style.backgroundColor = PgnNParams.MbaBgColor;
                var widgetWidth = document.getElementById(divId).offsetWidth;

                widgetObj.content += "<div style='justify-content:center !important; width:" + widgetWidth + "px; padding:5px; margin-bottom:5px; display:flex;flex-wrap:wrap;'>";
                widgetObj.content += "<div class='pgnn-m-ba-header-title' style='font-size:15px;'> Haber devam ediyor ";
                widgetObj.content += "<div style='width: 0;height: 0;border-left: 5px solid transparent;border-right: 5px solid transparent;border-top: 10px solid #2f2f2f;font-size: 0;line-height: 0;float: right; margin-left:10px;margin-top:3px'>";
                widgetObj.content += "</div>";
                widgetObj.content += "</div>";
                widgetObj.content += "</div>";
            }
            else if (paramsObj._widgetType == "m-ba-sm-list") {
                var widgetWidth = document.getElementById(divId).parentElement.offsetWidth;
                widgetObj.content += "<div class='pgnn-m-ba-header' style='width:" + widgetWidth + "px; text-align:center;border-bottom: 1px solid #ececec; font-size:15px; margin-bottom: 10px;'>";
                widgetObj.content += "<div class='pgnn-m-ba-header-title' style='display:inline-block;'> Bunlara da göz atabilirsiniz";
                widgetObj.content += "<div style='width: 0;height: 0;border-left: 5px solid transparent;border-right: 5px solid transparent;border-top: 10px solid #2f2f2f;font-size: 0;line-height: 0;float: right; margin-left:10px;margin-top:3px'>";
                widgetObj.content += "</div>";
                widgetObj.content += "</div>";
                widgetObj.content += "</div>";
            }
            else if (paramsObj._widgetType == "d-sidebar" | paramsObj._widgetType == "m-sidebar" | paramsObj._widgetType == "d-sidebar-big") {
            }

            //rows
            for (let k = 0; k < paramsObj._scheme.split("|").length; k++) {
                var rowPlan = paramsObj._scheme.split("|")[k];
                var tempObj = generateRow(paramsObj, rowPlan, divId + "_" + k.toString());
                widgetObj.content += tempObj.content;
                //if outstream slot available, generate
                if (paramsObj._widgetType == "m-ba-sm-list" && k == 5) {
                    widgetObj.content += "<div class='pgnn-outstream-slot' style='display:flex;'><div class='pgnn-outstream-slot-inner'></div></div>";
                }
                tempObj.adIds.forEach(element => widgetObj.adIds.push(element));
                tempObj.newsIds.forEach(element => widgetObj.newsIds.push(element));
                tempObj.iframeIds.forEach(element => widgetObj.iframeIds.push(element));
            }

            //think as footer block
            if (paramsObj._widgetType == "m-ba") {

                if (PgnNParams.WidgetLogoUrl != null && PgnNParams.WidgetLogoUrl.length > 5) {
                    widgetObj.content += "<div class='pgnn-row pgnn-no-gutters pgnn-justify-content-center' style='margin-bottom:10px !important;'>";
                    widgetObj.content += "  <div class='pgnn-col pgnn-d-ba-header-brand'>";
                    widgetObj.content += "      <a class='' target='_blank' href='" + PgnNParams.WidgetBrandUrl + "'><img style='width: 30px;' src='" + PgnNParams.WidgetLogoUrl + "'></a>";
                    widgetObj.content += "  </div>";
                    widgetObj.content += "</div>";
                }
            }
            else if (paramsObj._widgetType == "m-ba-sm-list") {
                widgetObj.content += "<div style='margin-bottom:10px !important; text-align:right;'>";
                widgetObj.content += "  <div>";
                widgetObj.content += "      <a class='' target='_blank' href='https://www.pigeoon.com'><img alt='Native Ads by Pigeoon' style='width: 30px;' src='https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png'></a>";
                widgetObj.content += "  </div>";
                widgetObj.content += "</div>";
            }
        }
        //console.log("PgnNativeLogv2 widget content: " + widgetObj.content);
        return widgetObj;
    }

    function generateRow(paramsObj, rowPlan, container) {
        var adIds = new Array();
        var newsIds = new Array();
        var iframeIds = new Array();
        var content = "";
        var rowWidth = 0;
        if (PgnNParams.pgnnDomains.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
            if (paramsObj._widgetType == "d-ba" || paramsObj._widgetType == "d-ba-fw") {
                rowWidth = document.getElementById(container.split("_")[0]).offsetWidth;
                content = "<div class='' style='display:flex;width:" + rowWidth + "px; margin-bottom:20px;'>";
            }
            else if (paramsObj._widgetType == "m-ba-sm-list") {
                var rowWidth = document.getElementById(container.split("_")[0]).offsetWidth;
            }
            else if (paramsObj._widgetType == "m-ba") {
                rowWidth = document.getElementById(container.split("_")[0]).offsetWidth;
                content = "<div style='justify-content:center !important;display:block;'>";
            }
            else if (paramsObj._widgetType == "m-sidebar") {
                rowWidth = document.getElementById(container.split("_")[0]).offsetWidth;
                content = "<div class='pgnn-m-sidebar-container' style='display:flex; justify-content:center;width:" + rowWidth + "px;'>";
            }
            else if (paramsObj._widgetType == "d-sidebar" || paramsObj._widgetType == "d-sidebar-big") {
                rowWidth = document.getElementById(container.split("_")[0]).offsetWidth;
                content = "<div style='width:" + rowWidth + "px;'>";
            }
            else if (paramsObj._widgetType == "d-masthead") {
                content = "<div style='width:970px; height:250px; background-color:white; margin:10px auto;' class='pgnn-d-masthead-container'>";
            }
            else if (paramsObj._widgetType == "m-masthead") {
                content = "<div style='display:inline:block;height:100px; margin:10px auto;' class='pgnn-m-masthead-container'>";
            }
            else if (paramsObj._widgetType == "d-vignette") {
                content = '<div class="pgnn-d-vignette-container" style="display:none; position:absolute; width:100%; height:100%; background-color:black; background-color:rgba(0, 0, 0, 0.7); z-index:2147483647; position:fixed; top:0px; left:0; backdrop-filter: blur(5px)">';
                content += '    <div class="pgnn-d-vignette-top-bar" style="width: 100%; height: 50px; top:0; position:fixed; z-index:9999999999;"><img class="pgnn-d-vignette-close-button" style="width: 40px;position: relative;right: 0;top: 0px;float: right;margin: 5px 5px 5px 0;" src="https://cdn-native.pigeoon.com/static/pigeoon/vignette/vignette-close-64x64.png"></img></div>';
                content += '        <div class="pgnn-d-vignette-content" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: block; background-color:silver; z-index=9999999998; border:5px solid white; border-radius:5px;">';
                content += '            <div style="paramsObj: fixed;bottom: -25px;right:-5px;background-color:white;padding:0 5px;border-radius: 5px 0px 5px 5px;"><a href="https://www.pigeoon.com" target="_blank"><img style="width:25px;" src="https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png"></img></a></div>'
            }
            else if (paramsObj._widgetType == "m-vignette") {
                content = '<div class="pgnn-m-vignette-container" style="display:none; position:absolute; width:100%; height:100%; background-color:black; background-color:rgba(0, 0, 0, 0.7); z-index:2147483647; position:fixed; top:0px; left:0; backdrop-filter: blur(5px)">';
                content += '    <div class="pgnn-m-vignette-top-bar" style="width: 100%; height: 50px; top:0; position:fixed; z-index:9999999999;"><img class="pgnn-m-vignette-close-button" style="width: 40px;position: relative;right: 0;top: 0px;float: right;margin: 5px 5px 5px 0;" src="https://cdn-native.pigeoon.com/static/pigeoon/vignette/vignette-close-64x64.png"></img></div>';
                content += '    <div class="pgnn-m-vignette-content" style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); display: block; background-color:silver; z-index=9999999998; border:5px solid white; border-radius:5px;">';
                content += '        <div style="position: fixed;bottom: -25px;right:-5px;background-color:white;padding:0 5px;border-radius: 5px 0px 5px 5px;"><a href="https://www.pigeoon.com" target="_blank"><img style="width:25px;" src="https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png"></img></a></div>'

            }
            else if (paramsObj._widgetType == "d-sticky-bottom") {
                content += '<div class="pgnn-d-sticky-bottom-container pgnn-d-sticky-bottom-close-button" style="display:none;z-index:2147483644;position:fixed;bottom:85px;right:-5px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:3px;font-family:Arial;color:#000000;font-size:15px;background:rgb(236, 236, 236);padding: 4px 12px 6px 12px;border: solid 2px rgb(236, 236, 236);text-decoration: none;">Kapat</div>';
                content += '<div class="pgnn-d-sticky-bottom-container" style="display:none; width: 100%;  bottom:0; position:fixed; z-index:2147483645; background-color:#fbf9f9; border-top:3px solid #ececec; text-align:center;">';
            }
            else if (paramsObj._widgetType == "d-sticky-top") {
                content += '<div class="pgnn-d-sticky-top-container" style="display:none; width: 100%;  top:0; position:fixed; z-index:2147483645; background-color:#fbf9f9; border-bottom:3px solid #ececec; text-align:center;">';
            }
            else if (paramsObj._widgetType == "m-sticky-bottom") {
                content += '<div class="pgnn-m-sticky-bottom-container pgnn-m-sticky-bottom-close-button" style="display:none;z-index:2147483644;position:fixed;bottom:95px;right:-5px;-webkit-border-radius:3px;-moz-border-radius:3px;border-radius:3px;font-family:Arial;color:#000000;font-size:15px;background:rgb(236, 236, 236);padding: 4px 12px 6px 12px;border: solid 2px rgb(236, 236, 236);text-decoration: none;">Kapat</div>';
                content += '<div class="pgnn-m-sticky-bottom-container" style="display:none; width: 100%; bottom:0; position:fixed; z-index:2147483645; background-color:#fbf9f9; border-top:3px solid #ececec; text-align:center;">';
            }
            else if (paramsObj._widgetType == "m-sticky-top") {
                content += '<div class="pgnn-m-sticky-top-container" style="display:none; width: 100%; top:0; position:fixed; z-index:2147483645; background-color:#fbf9f9; border-bottom:3px solid #ececec; text-align:center;">';
            }
            else if (paramsObj._widgetType == "d-showcase") {
                content = "<div style='width:100%; margin:10px auto;' class='pgnn-d-showcase-container'>";
            }
            else if (paramsObj._widgetType == "m-showcase") {
                content = "<div style='display:inline-block; margin:10px auto;' class='pgnn-m-showcase-container'>";
            }
        }

        var iframeExistsFlag = 0;
        //d-ba-fw de width olarak, m-ba da height olarak kullanılıyor
        var iframeWidthHeight = 0;
        for (let c = 0; c < rowPlan.split(",").length; c++) {
            if (rowPlan.split(",")[c].includes("i") && rowPlan.split(",")[c].includes(":") && iframeExistsFlag == 0) {//only one iframe is allowed
                iframeWidthHeight = rowPlan.split(",")[c].split(":")[1];
                iframeExistsFlag = 1;
            }
        }
        for (let x = 0; x < rowPlan.split(",").length; x++) {
            var currentCellPlan = rowPlan.split(",")[x];
            var divId = container + "_" + paramsObj._widgetType + "_" + x.toString();
            var width = rowWidth / rowPlan.split(",").length;
            var height = 0;
            if (paramsObj._widgetType == "d-ba-fw") {
                width = iframeExistsFlag ? (rowWidth - iframeWidthHeight) / (((rowPlan.split(",").length - 1)) == 0 ? 1 : ((rowPlan.split(",").length - 1))) : rowWidth / rowPlan.split(",").length;
            }
            if (paramsObj._widgetType == "m-ba") {
                height = iframeWidthHeight;
            }

            if (currentCellPlan.includes("i")) {
                if (paramsObj._widgetType == "d-ba-fw") {
                    width = iframeWidthHeight;
                }
                else if (paramsObj._widgetType == "m-ba") {
                    height = iframeWidthHeight;
                }
            }

            if (currentCellPlan.includes("a")) { adIds.push(divId); }
            else if (currentCellPlan.includes("n")) { newsIds.push(divId); }
            else if (currentCellPlan.includes("i")) { iframeIds.push(divId); };
            content += generateCell(paramsObj, width, height, divId);
        }


        if (paramsObj._widgetType == "d-vignette" || paramsObj._widgetType == "m-vignette") {
            content += "</div>";
        }
        else if (paramsObj._widgetType == "d-sticky-bottom") {
            //content += '<div class="pgnn-d-sticky-bottom-container-logo" style="position: absolute;top:0px;right:5px;"><a href="https://www.pigeoon.com" target="_blank"><img style="width:25px;" src="https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png"></img></a></div>'
        }
        else if (paramsObj._widgetType == "d-sticky-top") {
            //content += '<div class="pgnn-d-sticky-top-container-logo" style="position: absolute; bottom:0px; right:5px;"><a href="https://www.pigeoon.com" target="_blank"><img style="width:25px;" src="https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png"></img></a></div>'
        }
        else if (paramsObj._widgetType == "m-sticky-bottom") {
            //content += '<div class="pgnn-m-sticky-bottom-container-logo" style="position: absolute;top:-25px;right:5px;"><a href="https://www.pigeoon.com" target="_blank"><img style="width:25px;" src="https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png"></img></a></div>'
        }
        else if (paramsObj._widgetType == "m-sticky-top") {
            //content += '<div class="pgnn-m-sticky-top-container-logo" style="position: absolute; bottom:0px; right:5px;"><a href="https://www.pigeoon.com" target="_blank"><img style="width:25px;" src="https://cdn-native.pigeoon.com/static/pigeoon/pigeoon-logo-small.png"></img></a></div>'
        }

        content += "</div>";

        var returnObj = new Object();
        returnObj.content = content;
        returnObj.adIds = adIds;
        returnObj.newsIds = newsIds;
        returnObj.iframeIds = iframeIds;
        return returnObj;
    }

    function generateCell(paramsObj, cellWidth, cellHeight, id) {
        if (PgnNParams.pgnnDomains.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
            if (paramsObj._widgetType == "d-ba") {
                var widgetWidth = document.getElementById(id.split("_")[0]).offsetWidth;
                var cellContainerPadding = paramsObj._cellPadding;
                var content = "<div style='width:" + cellWidth + "px;padding:0 " + cellContainerPadding + "px;'>";
                content += "         <div id='" + id + "' style='overflow:hidden;'>";
                content += "             <div style='width:99%;height:99%;'>";
                content += "                <div class='pgnn-img'>";
                content += "                     <a href='#' target='_blank'>";
                content += "                        <img style='text-decoration:none;width:" + (cellWidth - 2 * cellContainerPadding) + "px;height:" + (cellWidth - 2 * cellContainerPadding) + "px;object-fit:cover;' src = '" + PgnNParams.dummyImageSrc + "' >";
                content += "                     </a >";
                content += "                </div>";
                content += "                <div>";
                content += "                    <div class='pgnn-title'>";
                content += "                        <div style='overflow: hidden;text-align:left;'>";
                content += "                            <a  href='##hb_native_linkurl##' target='_blank' style='text-decoration:none;color:black;font-weight: bold;text-align: left;overflow: hidden;font-size: 15px !important;margin-top: 5px;line-height: 1.4;font-family: sans-serif;'></a>";
                content += "                        </div>";
                content += "                    </div>";
                content += "                    <div class='pgnn-ad-element' style='display:flex;justify-content:end;height:22px;display:none;'>";
                content += "                        <div class='pgnn-ad-element-cta'>";
                content += "                            <a href='##hb_native_linkurl##' target='_blank' style='border: 1px solid #212529; border-radius: 5px;color: #212529;padding: 3px;text-decoration: none !important;text-transform: capitalize;font-size: 12px !important;font-weight: bold;font-family: sans-serif;'></a>";
                content += "                        </div>";
                content += "                    </div>";
                content += "                </div>";
                content += "            </div>";
                content += "        </div>";
                content += "    </div>";
                return content;
            }
            else if (paramsObj._widgetType == "d-ba-fw") {
                var cellContainerPadding = paramsObj._cellPadding;
                var content = "<div style='width:" + cellWidth + "px;padding:" + cellContainerPadding + "px;'>";
                content += "         <div id='" + id + "' style='overflow:hidden;'>";
                content += "             <div style='width:100%;height:100%;'>";
                content += "                 <div style='margin-bottom:3px;'>";
                content += "                     <a href='#' target='_blank'>";
                content += "                         <img style='border:1px solid #ececec;width:" + (cellWidth - 2 * cellContainerPadding) + "px;object-fit:cover;aspect-ratio:1.91;' src = '" + PgnNParams.dummyImageSrc + "' ></a>";
                content += "                 </div>";

                content += `                 <div style='display:table;width:100%'>
                                                <div class='pgnn-title' style='display:table;text-align:left;'>
                                                    <div>
                                                        <a href='#' target='_blank' style='font-weight: bold;text-align: left;overflow: hidden;font-size: 19px !important;margin-top: 10px;font-family: sans-serif;text-decoration: none;color: black;line-height:22px;'></a>
                                                    </div>
                                                </div>
                                                
                                                 <div class='pgnn-ad-element' style='display:none;float:right;'>
                                                    <div class='pgnn-ad-element-cta' style='border: 1px solid gray;float: right;padding: 3px;border-radius: 5px;'>
                                                        <a href='#' target='_blank' style='color:gray;text-decoration:none;font-size:16px;font-family:sans-serif;'></a>
                                                    </div>
                                                </div> 
                                            </div>
                                        </div>
                                    </div>
                                </div>`;
                return content;
            }
            else if (paramsObj._widgetType == "m-ba-sm-list") {
                var widgetWidth = document.getElementById(id.split("_")[0]).offsetWidth;
                var cellContainerPadding = paramsObj._cellPadding;
                var content = '<div id="' + id + '" class="pgnn-m-ba-sm-list-item" style="display:flex; border-bottom:1px solid #ececec;margin-bottom:5px;padding-bottom:5px; width:' + widgetWidth + 'px;">';
                content += '<div style="margin-right:5px;" class="pgnn-ad-element-img">';
                content += '<a href="#" target="_blank">';
                content += '<img style="width: 125px; height: 125px; min-width:125px; object-fit:cover;" src="' + PgnNParams.dummyImageSrc + '"/>';
                content += '</a>';
                content += '</div>';
                content += '<div style="flex-direction:column; display:flex; flex-grow:1;text-align:left;">';
                content += '<div style="width:100%;" class="pgnn-ad-element-title">';
                content += '<a style="text-decoration:none; font-size:16px; font-family:sans-serif; font-weight:bold; color:black; text-transform: capitalize;" href="#" target="_blank">';
                content += '</a>';
                content += '</div>';
                content += '<div style="width:100%; flex-grow:1;margin-top:2px;" class="pgnn-ad-element-spot">';
                content += '<a style="text-decoration:none; font-size:14px; font-family:sans-serif; font-weight:normal; color:black; text-transform: capitalize;" href="#" target="_blank">';
                content += '</a>';
                content += '</div>';
                content += '<div style="display: flex; justify-content: flex-end;" class="pgnn-ad-element-cta">';
                content += '<div style="border:1px solid black; text-align: right; padding: 1px; border-radius: 5px; display: inline-block;">';
                content += '<a style="text-decoration:none; font-size:14px; font-family:sans-serif; font-weight:normal; color:black;" href="#" target="_blank">';
                content += '</a>';
                content += '</div>';
                content += '</div>';
                content += '</div>';
                content += '</div>';
                return content;
            }
            else if (paramsObj._widgetType == "m-ba") {
                var cellContainerPadding = paramsObj._cellPadding;
                var heightStr = cellHeight != 0 ? "height:" + cellHeight + "px;" : "";
                var content = "     <div id='" + id + "' style='" + heightStr + "border: 1px solid  #dedbd9;border-radius: 4px;text-align:left;margin-bottom:10px; display:none; width:" + (cellWidth - 2 * cellContainerPadding) + "px;margin-left:" + cellContainerPadding + "px;'>";
                content += "             <div style='background-color:#f2f2f2;border-radius:4px;'>";
                content += "                <div style='width:100%;'>";
                content += "                    <a href='#' target='_blank'>";
                content += "                        <img style='border-radius:4px 4px 0px 0px;aspect-ratio:1.9/1; object-fit:cover;width:100%;' src='" + PgnNParams.dummyImageSrc + "'>";
                content += "                    </a>";
                content += "                </div>";
                content += "                <div style='padding:0px 5px 5px 5px'>";
                content += "                    <div style='overflow:hidden;'>";
                content += "                        <div>";
                content += "                            <a href='#' target='_blank' style='font-family:sans-serif;font-size:16px;font-weight:bold;text-decoration:none;color:black;'></a>";
                content += "                        </div>";
                content += "                        <div>";
                content += "                            <a href='#' target='_blank' style='font-family:sans-serif;font-size:14px;text-decoration:none;color:black;'></a>";
                content += "                        </div>";
                content += "                        <div style='padding:3px;text-align:right;display:none;' class='pgnn-ad-element'>";
                content += "                            <a href='#' target='_blank' style='color:black;text-decoration:none;font-size:14px !important; border:1px solid #666666;border-radius:5px;padding:2px;text-transform:capitalize;font-family:sans-serif;'></a>";
                content += "                        </div>";
                content += "                    </div>";
                content += "                </div>";
                content += "            </div>";
                content += "        </div>";
                return content;
            }
            else if (paramsObj._widgetType == "m-sidebar") {
                var widgetWidth = document.getElementById(id.split("_")[0]).offsetWidth;
                var cellContainerPadding = paramsObj._cellPadding;
                var content = "   <div style='display:flex; border:1px solid #d5d5d5;width:" + (cellWidth - 2 * cellContainerPadding) + "px; margin:0 " + cellContainerPadding + "px;' id='" + id + "'>";
                content += "         <div style='text-align:center;'>";
                content += "            <div  style='margin-top:5px'>";
                content += "               <a href='#' target='_blank' style='text-decoration:none;'>";
                content += "                  <img style='min-width: 150px !important; object-fit: scale-down; height: 100px !important; max-width:initial !important; max-height:initial !important;' src=''/>";
                content += "               </a>";
                content += "            </div>";

                content += "            <div  style='text-align: left; padding:5px; min-height:50px'>";
                content += "               <a href='#' target='_blank' style='font-family:Trebuchet MS,Verdana,sans-serif; color:#14233a; font-weight:700; font-size:17px; text-decoration:none; line-height:1em !important;'></a>";
                content += "            </div>";
                content += "         </div>";

                content += "         <div class='pgnn-ad-element' style='background-color: #14233a; height:25px; padding:5px; text-align:center; '><a href='#' target='_blank' style='font-weight:600; width:100%; color:white; text-decoration:none;font-family:Trebuchet MS,Verdana,sans-serif; font-size:16px;'></a></div>"
                content += "      </div>"
                return content;
            }
            else if (paramsObj._widgetType == "d-sidebar") {
                var content = "<div  id='" + id + "' style='width:" + cellWidth + "px;'>";
                content += "   <div style='display:flex;'>";
                content += "       <div style='margin-right: 15px; margin-left:0px;display:flex; float:left;'>";
                content += "           <a href='#' target='_blank' style='text-decoration:none;'>";
                content += "               <img style='width: 100px; height:80px;object-fit: cover;' src='#' style='display:none;   '>";
                content += "           </a>";
                content += "       </div>";
                content += "       <div style='text-align: left;'>";
                content += "           <div style='padding-right:15px;'>";
                content += "               <a href='#' target='_blank' style='font-family:Trebuchet MS,Verdana,sans-serif;color:black; font-weight:700; font-size:14px; text-decoration:none;'></a>";
                content += "           </div>";
                content += "           <div>";
                content += "               <a href='#' target='_blank' style='font-family:Trebuchet MS,Verdana,sans-serif;color:black; font-size:13px; text-decoration:none;'></a>";
                content += "           </div>";
                content += "           <div class='pgnn-ad-element' style='float:right; margin:0 0 5px 0; position:absolute; bottom:0px; right: 0px;'>";
                content += "               <a href='#' target='_blank' style='font-family:Trebuchet MS,Verdana,sans-serif; color:blue; font-size:13px; text-decoration:none;'></a>";
                content += "           </div>";
                content += "       </div>";
                content += "   </div>";
                content += "</div>";
                return content;
            }
            else if (paramsObj._widgetType == "d-sidebar-big") {
                var content = "<div  id='" + id + "' style='width:" + cellWidth + "px;'>";
                content += "   <div style='display:flex;'>";
                content += "       <div>";
                content += "           <a href='#' target='_blank' style='text-decoration:none;'>";
                content += "               <img style='width: 100%; aspect-ratio:1.9/1; object-fit: cover;' src='" + PgnNParams.dummyImageSrc + "'>";
                content += "           </a>";
                content += "       </div>";
                content += "       <div style='text-align: left;  position: relative;margin-top:10px;'>";
                content += "           <div>";
                content += "               <a href='#' target='_blank' style='color:#14233a; font-weight:700; font-size:18px; text-decoration:none;'></a>";
                content += "           </div>";
                content += "           <div>";
                content += "               <a href='#' target='_blank' style='color:#14233a; font-size:18px; text-decoration:none;'></a>";
                content += "           </div>";
                content += "           <div class='pgnn-ad-element' style='float:right; margin:0 0 5px 0; position:absolute; bottom:0px; right: 0px;'>";
                content += "               <a href='#' target='_blank' style='font-family:Trebuchet MS,Verdana,sans-serif; color:blue; font-size:13px; text-decoration:none;'></a>";
                content += "           </div>";
                content += "       </div>";
                content += "   </div>";
                content += "</div>";
                return content;
            }
            else if (
                paramsObj._widgetType == "d-masthead"
                || paramsObj._widgetType == "m-masthead"
                || paramsObj._widgetType == "d-vignette"
                || paramsObj._widgetType == "m-vignette"
                || paramsObj._widgetType == "d-sticky-top"
                || paramsObj._widgetType == "d-sticky-bottom"
                || paramsObj._widgetType == "m-sticky-top"
                || paramsObj._widgetType == "m-sticky-bottom"
                || paramsObj._widgetType == "d-showcase"
                || paramsObj._widgetType == "m-showcase") {
                var content = "<div id='" + id + "'>";
                content += "</div>";
                return content;
            }
        }
    }

    function fillNewsItemDbaFw(paramsObj, cellWidth, cellHeight, id) {
        if (PgnNParams.pgnnDomains.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
            if (paramsObj._widgetType == "d-ba-fw") {
                var cellContainerPadding = paramsObj._cellPadding;
                var content = "             <div style='width:100%;height:100%;'>";
                content += "                 <div style='margin-bottom:3px;'>";
                content += "                     <a href='#' target='_blank'>";
                content += "                         <img style='border:1px solid #ececec;width:" + (cellWidth - 2 * cellContainerPadding) + "px;object-fit:cover;aspect-ratio:1.91;' src = '" + PgnNParams.dummyImageSrc + "' ></a>";
                content += "                 </div>";

                content += `                 <div style='display:table;width:100%'>
                                                <div class='pgnn-title' style='display:table;text-align:left;'>
                                                    <div>
                                                        <a href='#' target='_blank' style='font-weight: bold;text-align: left;overflow: hidden;font-size: 19px !important;margin-top: 10px;font-family: sans-serif;text-decoration: none;color: black;line-height:22px;'></a>
                                                    </div>
                                                </div>
                                                
                                                 <div class='pgnn-ad-element' style='display:none;float:right;'>
                                                    <div class='pgnn-ad-element-cta' style='border: 1px solid gray;float: right;padding: 3px;border-radius: 5px;'>
                                                        <a href='#' target='_blank' style='color:gray;text-decoration:none;font-size:16px;font-family:sans-serif;'></a>
                                                    </div>
                                                </div> 
                                            </div>
                                        </div>`;
                return content;
            }
        }
    }

    function generateNewsJson(newsIds, paramsObj) {
        for (let k = 0; k < newsIds.length; k++) {
            var newsItemToBeUsed;

            for (let p = 0; p < PgnNParams.PGNNEWSITEMS.length; p++) {
                if (PgnNParams.PGNNEWSITEMS[p].isUsed == undefined || PgnNParams.PGNNEWSITEMS[p].isUsed == null) {
                    PgnNParams.PGNNEWSITEMS[p].isUsed = 1;
                    newsItemToBeUsed = PgnNParams.PGNNEWSITEMS[p];
                    break;
                }
            }
            drawNewsItem(newsItemToBeUsed, newsIds[k], paramsObj);
        }
    }

    function drawNewsItem(newsItem, newsId, paramsObj) {
        var newsBlock = document.getElementById(newsId);
        if (newsBlock != null && newsBlock != undefined) {
            if (!newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder].includes('?')) { newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder] = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder] + '?utm_source=pgnNative'; } else { newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder] = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder] + '&utm_source=pgnNative'; }
            if (PgnNParams.pgnnDomains.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
                if (paramsObj._widgetType == 'd-ba' || paramsObj._widgetType == 'd-ba-fw' || paramsObj._widgetType == 'd-sidebar' || paramsObj._widgetType == 'd-sidebar-big' || paramsObj._widgetType == 'm-sidebar') {
                    titleNew = "";
                    if (newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder].length > PgnNParams['pgnnTitleLength__' + paramsObj._widgetType.replace("-", '_').replace("-", '_').replace("-", '_')]) {
                        var tempTitle = newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder].substring(0, PgnNParams['pgnnTitleLength__' + paramsObj._widgetType.replace("-", '_').replace("-", '_').replace("-", '_')]).split(" ");
                        for (var z = 0; z < tempTitle.length - 1; z++) {
                            titleNew += tempTitle[z] + " ";
                        }
                        titleNew = titleNew + "...";
                    } else {
                        titleNew = newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder] + "...";
                    }

                    try {
                        var widgetWidth = document.getElementById(newsBlock.getAttribute("id").split("_")[0]).offsetWidth;
                        var colCount = paramsObj._formats.split("|")[parseInt(newsId.split("d-ba-fw")[0].split("_")[1])].split(",").length;
                        var cellWidth = widgetWidth / colCount;
                        if (paramsObj._widgetType != "d-ba-fw")
                            newsBlock.innerHTML = generateCell(paramsObj, cellWidth, 0, newsId);
                        else {
                            newsBlock.innerHTML = fillNewsItemDbaFw(paramsObj, cellWidth, 0, newsId);
                        }
                        newsBlock.style.display = "block";
                        newsBlock.getElementsByTagName('a')[0].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];
                        newsBlock.getElementsByTagName('a')[1].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];
                        newsBlock.getElementsByTagName('a')[1].innerHTML = titleNew;

                        newsBlock.getElementsByTagName('a')[0].addEventListener("click", function () {
                            PgnN.TrackNewsItemClick(newsBlock.getElementsByTagName('a')[0], paramsObj);
                        });
                        newsBlock.getElementsByTagName('a')[1].addEventListener("click", function () {
                            PgnN.TrackNewsItemClick(newsBlock.getElementsByTagName('a')[1], paramsObj);
                        });

                        if (newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderSquare] == null || newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderSquare] == "null") {
                            newsBlock.getElementsByTagName('img')[0].src = PgnNParams.dummyImageSrc;
                            if (document.location.host.includes("dunya.com"))
                                newsBlock.getElementsByTagName('img')[0].style.backgroundColor = "#e20031";
                            newsBlock.getElementsByTagName('img')[0].style.objectFit = "scale-down";
                        } else {
                            newsBlock.getElementsByTagName('img')[0].src = newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderSquare];
                        }
                        newsBlock.getElementsByTagName('a')[1].style.color = "black";
                    }
                    catch (err) {
                        console.error(err.message);
                    }
                }
                else if (paramsObj._widgetType == 'm-ba') {
                    var w = newsBlock.parentElement.offsetWidth;
                    newsBlock.parentElement.innerHTML = generateCell(paramsObj, w, 0, newsId);
                    newsBlock = document.getElementById(newsId);
                    newsBlock.style.display = "block";
                    var titleNew = newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder];
                    if (newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder].length > PgnNParams['pgnnTitleLength__' + paramsObj._widgetType.replace("-", '_').replace("-", '_').replace("-", '_')]) {
                        titleNew = "";
                        var tempTitle = newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder].substring(0, PgnNParams['pgnnTitleLength__' + paramsObj._widgetType.replace("-", '_').replace("-", '_').replace("-", '_')]).split(" ");
                        for (var z = 0; z < tempTitle.length - 1; z++) {
                            titleNew += tempTitle[z] + " ";
                        }
                        titleNew = titleNew + "...";
                    }

                    newsBlock.getElementsByTagName('a')[0].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];
                    newsBlock.getElementsByTagName('a')[1].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];

                    newsBlock.getElementsByTagName('a')[0].addEventListener("click", function () {
                        PgnN.TrackNewsItemClick(newsBlock.getElementsByTagName('a')[0], paramsObj);
                    });
                    newsBlock.getElementsByTagName('a')[1].addEventListener("click", function () {
                        PgnN.TrackNewsItemClick(newsBlock.getElementsByTagName('a')[1], paramsObj);
                    });

                    newsBlock.getElementsByTagName('a')[1].innerHTML = titleNew;
                    //newsBlock.getElementsByTagName('a')[1].style.fontSize="18px";
                    if (newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderWide] == null || newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderWide] == "null") {
                        newsBlock.getElementsByTagName('img')[0].src = PgnNParams.dummyImageSrc;
                        if (document.location.host.includes("dunya.com"))
                            newsBlock.getElementsByTagName('img')[0].style.backgroundColor = "#e20031";
                        newsBlock.getElementsByTagName('img')[0].style.objectFit = "scale-down";
                    } else {
                        newsBlock.getElementsByTagName('img')[0].src = newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderWide];
                    }
                    try {
                        newsBlock.getElementsByTagName("div")[2].style.minHeight = "60px";
                    } catch (err) {
                        console.error(err);
                    }
                }
                else if (paramsObj._widgetType == 'm-ba-sm-list') {
                    try {
                        newsBlock.getElementsByClassName("pgnn-ad-element-img")[0].getElementsByTagName('a')[0].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];
                        newsBlock.getElementsByClassName("pgnn-ad-element-title")[0].getElementsByTagName('a')[0].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];
                        newsBlock.getElementsByClassName("pgnn-ad-element-spot")[0].getElementsByTagName('a')[0].href = newsItem[PgnNParams.pgnnNewsSourceClickUrlPlaceHolder];

                        newsBlock.getElementsByClassName("pgnn-ad-element-img")[0].getElementsByTagName('a')[0].addEventListener("click", function () {
                            PgnN.TrackNewsItemClick(newsBlock.getElementsByClassName("pgnn-ad-element-img")[0].getElementsByTagName('a')[0], paramsObj);
                        });
                        newsBlock.getElementsByClassName("pgnn-ad-element-title")[0].getElementsByTagName('a')[0].addEventListener("click", function () {
                            PgnN.TrackNewsItemClick(newsBlock.getElementsByClassName("pgnn-ad-element-title")[0].getElementsByTagName('a')[0], paramsObj);
                        });
                        newsBlock.getElementsByClassName("pgnn-ad-element-spot")[0].getElementsByTagName('a')[0].addEventListener("click", function () {
                            PgnN.TrackNewsItemClick(newsBlock.getElementsByClassName("pgnn-ad-element-spot")[0].getElementsByTagName('a')[0], paramsObj);
                        });

                        if (newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderWide] == null || newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderWide] == "null") {
                            newsBlock.getElementsByClassName("pgnn-ad-element-img")[0].getElementsByTagName('img')[0].src = PgnNParams.dummyImageSrc;
                        } else {
                            newsBlock.getElementsByClassName("pgnn-ad-element-img")[0].getElementsByTagName('img')[0].src = newsItem[PgnNParams.pgnnNewsSourceImagePlaceHolderWide];
                        }

                        var titleNew = "";
                        if (newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder].length > PgnNParams['pgnnTitleLength__' + paramsObj._widgetType.replace("-", '_').replace("-", '_').replace("-", '_')]) {
                            var tempTitle = newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder].substring(0, PgnNParams['pgnnTitleLength__' + paramsObj._widgetType.replace("-", '_').replace("-", '_').replace("-", '_')]).split(" ");
                            for (var z = 0; z < tempTitle.length - 1; z++) {
                                titleNew += tempTitle[z] + " ";
                            }
                            titleNew = titleNew + "...";
                        } else {
                            titleNew = newsItem[PgnNParams.pgnnNewsSourceTitlePlaceHolder];
                        }
                        newsBlock.getElementsByClassName("pgnn-ad-element-title")[0].getElementsByTagName('a')[0].innerHTML = titleNew;

                        var descriptionNew = "";
                        var descLimit = 40;
                        if (titleNew.length < 50) {
                            descLimit = 80;
                        }
                        else if (titleNew.length >= 50 && titleNew.length <= 100) {
                            descLimit = 50;
                        }
                        else {
                            descLimit = 25;
                        }
                        if (newsItem[PgnNParams.pgnnNewsSourceDescriptionPlaceHolder].length > 50) {
                            var tempDescription = newsItem[PgnNParams.pgnnNewsSourceDescriptionPlaceHolder].substring(0, descLimit).split(" ");
                            for (var v = 0; v < tempDescription.length - 1; v++) {
                                descriptionNew += tempDescription[v] + " ";
                            }
                            descriptionNew = descriptionNew + "...";
                        } else {
                            descriptionNew = newsItem[PgnNParams.pgnnNewsSourceDescriptionPlaceHolder];
                        }
                        newsBlock.getElementsByClassName("pgnn-ad-element-spot")[0].getElementsByTagName('a')[0].innerHTML = descriptionNew;

                        newsBlock.getElementsByClassName("pgnn-ad-element-cta")[0].remove();
                    }
                    catch (exc) {
                        console.error(exc.message);
                    }
                }
            }
        }
    }

    function generateNewsXml(newsIds, rssLink, widgetObj) {
        var newsList = new Array();

        if (PgnNParams.PGNNEWSITEMS == undefined || PgnNParams.PGNNEWSITEMS.length == 0) {
            fetch(rssLink, {
                method: 'GET'
            })
                .then(function (response) { return response.text(); })
                .then(str => new window.DOMParser().parseFromString(str, "text/xml"))
                .then(data => {
                    const items = data.querySelectorAll("item");
                    for (let i = 0; i < items.length; i++) {
                        try {
                            var newsItem = new Object();
                            newsItem.title = items[i].querySelector("title").innerHTML.replace("<![CDATA[", "").replace("]]>", "").replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€Â¢", "").replace("ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“", "").replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€Â¢", "");
                            newsItem.imageUrl = (items[i].querySelector("enclosure") != null && items[i].querySelector("enclosure") != undefined) ? items[i].querySelector("enclosure").getAttribute("url") : dummyImageSrc;
                            newsItem.clickUrl = items[i].querySelector("link").innerHTML.replace("<![CDATA[", "").replace("]]>", "");
                            if (!newsItem.clickUrl.includes('?')) {
                                newsItem.clickUrl = newsItem.clickUrl + '?utm_source=pgnNative';
                            } else {
                                newsItem.clickUrl = newsItem.clickUrl + '&utm_source=pgnNative';
                            }
                            newsList.push(newsItem);
                        } catch (err) {
                            console.error(err);
                        }
                    }
                    PgnNParams.PGNNEWSITEMS = newsList;
                    PgnNParams.PGNNEWSITEMS = shuffleArray(PgnNParams.PGNNEWSITEMS);

                    var currentNewsOrder = 0;
                    for (let k = 0; k < newsIds.length; k++) {
                        var newsItemToBeUsed;
                        for (let p = 0; p < PgnNParams.PGNNEWSITEMS.length; p++) {
                            if (PgnNParams.PGNNEWSITEMS[p].isUsed == undefined || PgnNParams.PGNNEWSITEMS[p].isUsed == null) {
                                PgnNParams.PGNNEWSITEMS[p].isUsed = 1;
                                newsItemToBeUsed = PgnNParams.PGNNEWSITEMS[p];
                                break;
                            }
                        }
                        drawNewsItem(newsItemToBeUsed, newsIds[k], widgetObj);
                    }
                });
        } else {
            PgnNParams.PGNNEWSITEMS = shuffleArray(PgnNParams.PGNNEWSITEMS);
            var currentNewsOrder = 0;
            for (let k = 0; k < newsIds.length; k++) {
                var newsItemToBeUsed;
                for (let p = 0; p < PgnNParams.PGNNEWSITEMS.length; p++) {
                    if (PgnNParams.PGNNEWSITEMS[p].isUsed == undefined || PgnNParams.PGNNEWSITEMS[p].isUsed == null) {
                        PgnNParams.PGNNEWSITEMS[p].isUsed = 1;
                        newsItemToBeUsed = PgnNParams.PGNNEWSITEMS[p];
                        break;
                    }
                }
                drawNewsItem(newsItemToBeUsed, newsIds[k], widgetObj);
            }
        }
    }

    function generateIframes(iframeIds, paramsObj) {

        for (let i = 0; i < iframeIds.length; i++) {
            var currentBlock = document.getElementById(iframeIds[i]);
            var parentBlock = document.getElementById(iframeIds[i]).parentElement;
            var parentWidth = parentBlock.offsetWidth;
            var parentHeight = parentBlock.offsetHeight;
            var paddingNum = parentBlock.style.padding.length >= 3 ? parentBlock.style.padding.replace("px", "") : 0;
            if (paramsObj._widgetType == "d-ba-fw") {
                currentBlock.innerHTML = "<iframe src='" + PgnNParams.iframeSources[i] + "' title='PgnNative Iframe Content' height='" + (parentHeight - 2 * paddingNum) + "' width='" + (parentWidth - 2 * paddingNum) + "' frameborder='0' scrolling='no' style='overflow:hidden'></iframe>";
            } else if (paramsObj._widgetType == "m-ba") {
                currentBlock.innerHTML = "<iframe src='" + PgnNParams.iframeSources[i] + "' title='PgnNative Iframe Content' height='" + (parentHeight - 2 * paddingNum) + "' width='" + (parentWidth - 2 * paddingNum) + "' frameborder='0' scrolling='no' style='overflow:hidden'></iframe>";
                parentBlock.style.marginBottom = "10px";
            }

        }
    }

    function shuffleArray(array) {
        for (var i = array.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var temp = array[i];
            array[i] = array[j];
            array[j] = temp;
        }
        return array;
    }

    function loadScript(url, callback) {
        if (document.querySelector("[src*='" + url + "']") == null) {
            var script = document.createElement("script")
            script.type = "text/javascript";
            if (script.readyState) {  // only required for IE <9
                script.onreadystatechange = function () {
                    if (script.readyState === "loaded" || script.readyState === "complete") {
                        script.onreadystatechange = null;
                        if (callback)
                            callback();
                    }
                };
            } else {  //Others
                script.onload = function () {
                    if (callback)
                        callback();
                };
            }
            script.src = url;
            document.getElementsByTagName("head")[0].appendChild(script);
        } else {
            callback();
        }
    }

    function loadCss(url, callback) {
        if (document.querySelector("[href*='" + url + "']") == null) {
            var link = document.createElement("link")
            link.rel = 'stylesheet';
            link.type = 'text/css';
            link.href = url;
            if (link.readyState) {  // only required for IE <9
                link.onreadystatechange = function () {
                    if (link.readyState === "loaded" || link.readyState === "complete") {
                        link.onreadystatechange = null;
                        if (callback)
                            callback();
                    }
                };
            } else {
                link.onload = function () {
                    if (callback)
                        callback();
                };
            }
            document.getElementsByTagName("head")[0].appendChild(link);
        }
    }

    function fixSizeForAdUnit(width, height, divId, mediaType, paramsObj) {

        var elem = document.getElementById(divId);
        var widgetType = document.getElementById(divId).parentElement.parentElement.getAttribute("pgn-native-w");
        var parentElem = elem.parentElement;
        var parentWidth = parentElem.offsetWidth;
        var cellContainerPadding = paramsObj._cellPadding;
        if (mediaType == "banner") {
            elem.setAttribute("style", "border:1px solid #dedbd9;height:100%;background-color:#f2f2f2;border-radius:6px;padding:10px 0 10px 0;width:" + (parentWidth - 2 * cellContainerPadding) + "px;display:flex;justify-content:center;margin-bottom:10px;margin-left:" + cellContainerPadding + "px;");
            elem.style.Height = height + "px";
        }
        //else if (mediaType == "native") {
        //    var innerDiv = elem.getElementsByTagName("div")[0];
        //    var innerIframe = elem.getElementsByTagName("iframe")[0];
        //    innerDiv.removeAttribute("width");
        //    innerDiv.removeAttribute("height");
        //    innerIframe.removeAttribute("width");
        //    innerIframe.removeAttribute("width");
        //    innerDiv.style.width = (parentWidth - 2 * cellContainerPadding) + "px";
        //    innerIframe.style.width = (parentWidth - 2 * cellContainerPadding) + "px";
        //}
    }

    function checkVignetteAvailability(tabStateChange) {
        var showedVignetteAmount = PgnN.GetCookie("PgnNVignetteCount") == null ? 0 : parseInt(PgnN.GetCookie("PgnNVignetteCount"));
        if (showedVignetteAmount == 0) {
            if (PgnNParams.PGNN_VGN_TIMEELAPSED > PgnNParams.pgnnVignetteDelayFirstAd || tabStateChange) {
                return true;
            }
        }
        else if (showedVignetteAmount < PgnNParams.pgnnVignetteLimitInFc) {
            if (PgnNParams.PGNN_VGN_TIMEELAPSED > PgnNParams.pgnnVignetteDelayOtherAds || tabStateChange) {
                return true;
            }
        }
        return false;
    }

    function vgnListener() {
        if (typeof document.hidden !== "undefined") {
            PgnNParams.hidden = "hidden";
            PgnNParams.visibilityChange = "visibilitychange";
        } else if (typeof document.msHidden !== "undefined") {
            PgnNParams.hidden = "msHidden";
            PgnNParams.visibilityChange = "msvisibilitychange";
        } else if (typeof document.webkitHidden !== "undefined") {
            PgnNParams.hidden = "webkitHidden";
            PgnNParams.visibilityChange = "webkitvisibilitychange";
        }

        // Warn if the browser doesn't support addEventListener or the Page Visibility API
        if (typeof document.addEventListener === "undefined" || PgnNParams.hidden === undefined) {
            console.error("PgnNative => Visibility API desteklenmiyor.");
        } else {
            // Handle page visibility change
            document.addEventListener(PgnNParams.visibilityChange, function () {
                if (document[PgnNParams.hidden]) {
                    console.log("bdTabState handleVisibilityChange: hidden");
                    PgnN.PgnNLog("PgnNVignette bdTabState handleVisibilityChange: hidden");
                } else {
                    if (!document[PgnNParams.hidden]) {
                        console.log("bdTabState handleVisibilityChange: visible");
                        PgnN.PgnNLog("PgnNVignette bdTabState handleVisibilityChange: visible");
                        showAdIfAvailable(true);
                    }
                }
            }, false);
        }
    }

    function showAdIfAvailable(tabStateChange) { //if request comes from tabStateChange
        PgnN.PgnNLog("PgnNVignette showAdIfAllowed worked!");
        PgnNParams.PGNN_VGN_TIMEELAPSED = PgnNParams.PGNN_VGN_TIMEELAPSED + 1000;
        var targetElements = document.querySelectorAll(".pgn-native-d-vignette, .pgn-native-m-vignette");
        if (targetElements.length > 0) {
            if (checkVignetteAvailability(tabStateChange)) {
                try {
                    if (targetElements[0].getAttribute("id") == null) {
                        var slotId = "pgn-native-id-" + PgnN.GenerateRandomString(10);
                        targetElements[0].setAttribute("id", slotId);
                        PgnN.PgnNLog("PgnNVignette will trigger  with divId  => " + slotId);

                        var pgnLazySlotId = targetElements[0].getAttribute("id");
                        var itm = document.getElementById(pgnLazySlotId);
                        if (itm != null && itm.getAttribute("id").includes("pgn-native-") && !PgnNParams.pgnNativeViewedSlots.includes(pgnLazySlotId)) {
                            PgnN.InitNativeAds(pgnLazySlotId);
                        }
                    }
                } catch (err) {
                    console.error(err.message);
                }
            } else {
                PgnN.PgnNLog("PgnNVignette wont trigger currently! Cookie exists");
            }
        }
    }

    function manageVignette() {
        var vignetteInterval = setInterval(function () {
            if (PgnNParams.pgnnVignetteEventsBinded == 0) {
                PgnNParams.pgnnVignetteEventsBinded = 1;
                vgnListener();
            }
            showAdIfAvailable(false);
        }, 1000);
    }

    function manageStandard() {
        var pgnnStandardInterval = setInterval(function () {
            var targetElements = document.querySelectorAll(".pgn-native-d-sticky-bottom, .pgn-native-d-sticky-top, .pgn-native-m-sticky-bottom, .pgn-native-m-sticky-top, .pgn-native-d-masthead, .pgn-native-m-masthead, .pgn-native-d-showcase, .pgn-native-m-showcase");
            if (targetElements.length > 0) {
                clearInterval(pgnnStandardInterval);
                function showAdIfAllowed() {
                    try {
                        for (var st = 0; st < targetElements.length; st++) {
                            targetElements[st].removeAttribute("id");
                            if (targetElements[st].getAttribute("id") == null) {
                                var slotId = "pgn-native-id-" + PgnN.GenerateRandomString(10);
                                targetElements[st].setAttribute("id", slotId);
                                PgnN.PgnNLog("PgnNStandardAd will trigger  with divId  => " + slotId);

                                var itm = document.getElementById(slotId);
                                if (itm != null && itm.getAttribute("id").includes("pgn-native-") && !PgnNParams.pgnNativeViewedSlots.includes(slotId)) {
                                    PgnN.InitNativeAds(slotId);
                                }
                            }
                            //else {
                            //    targetElements[st].removeAttribute("id"); //on next iteration trigger will be allowed    
                            //}
                        }
                    } catch (err) {
                        console.error(err.message);
                    }

                }
                showAdIfAllowed();
                var stickyInterval = setInterval(showAdIfAllowed, manageStandardCookieTimeout() * 1000);
            }
        }, 100);
    }

    function manageStandard() {
        var pgnnStandardInterval = setInterval(function () {
            var targetElements = document.querySelectorAll(".pgn-native-d-sticky-bottom, .pgn-native-d-sticky-top, .pgn-native-m-sticky-bottom, .pgn-native-m-sticky-top, .pgn-native-d-masthead, .pgn-native-m-masthead, .pgn-native-d-showcase, .pgn-native-m-showcase");
            if (targetElements.length > 0) {
                clearInterval(pgnnStandardInterval);
                function showAdIfAllowed() {
                    try {
                        for (var st = 0; st < targetElements.length; st++) {
                            targetElements[st].removeAttribute("id");
                            if (targetElements[st].getAttribute("id") == null) {
                                var slotId = "pgn-native-id-" + PgnN.GenerateRandomString(10);
                                targetElements[st].setAttribute("id", slotId);
                                PgnN.PgnNLog("PgnNStandardAd will trigger  with divId  => " + slotId);

                                var itm = document.getElementById(slotId);
                                if (itm != null && itm.getAttribute("id").includes("pgn-native-") && !PgnNParams.pgnNativeViewedSlots.includes(slotId)) {
                                    PgnN.InitNativeAds(slotId);
                                }
                            }
                            //else {
                            //    targetElements[st].removeAttribute("id"); //on next iteration trigger will be allowed    
                            //}
                        }
                    } catch (err) {
                        console.error(err.message);
                    }

                }
                showAdIfAllowed();
                var stickyInterval = setInterval(showAdIfAllowed, manageStandardCookieTimeout() * 1000);
            }
        }, 100);
    }

    function manageNative() {
        if (PgnNParams.initNativeImmediatelly.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
            var targetElements = document.querySelectorAll(".pgn-native-d-ba, .pgn-native-d-ba-fw, .pgn-native-m-ba");
            if (targetElements.length > 0) {
                try {
                    for (var st = 0; st < targetElements.length; st++) {
                        targetElements[st].removeAttribute("id");
                        if (targetElements[st].getAttribute("id") == null) {
                            var slotId = "pgn-native-id-" + PgnN.GenerateRandomString(10);
                            targetElements[st].setAttribute("id", slotId);
                            PgnN.PgnNLog("PgnNative will trigger  with divId  => " + slotId);

                            var itm = document.getElementById(slotId);
                            if (itm != null && itm.getAttribute("id").includes("pgn-native-") && !PgnNParams.pgnNativeViewedSlots.includes(slotId)) {
                                PgnN.InitNativeAds(slotId);
                            }
                        }
                    }
                } catch (err) {
                    console.error(err.message);
                }
            }
        }
    }

    function manageVgnCookieTimeout() {
        return PgnNParams.pgnnVignetteCookieTimeout;
    }

    function manageStandardCookieTimeout() {
        if (PgnNParams.pgnnDomains.includes(document.location.host.replace("https://", "").replace("http://", "").replace("www.", ""))) {
            return 35;
        }
    }

    function manageVgnCloseClick(widgetType) {
        var showedVignetteAmount = PgnN.GetCookie("PgnNVignetteCount") == null ? 0 : parseInt(PgnN.GetCookie("PgnNVignetteCount"));
        if (showedVignetteAmount < PgnNParams.pgnnVignetteLimitInFc) {
            if (widgetType == 'd-vignette') {
                for (let i = 0; i < document.getElementsByClassName('pgnn-d-vignette-container').length; i++) {
                    document.getElementsByClassName('pgnn-d-vignette-container')[i].parentElement.removeAttribute('id');
                    document.getElementsByClassName('pgnn-d-vignette-container')[i].remove();
                    PgnNParams.PGNN_VGN_TIMEELAPSED = 0;
                }
            }
            else if (widgetType == 'm-vignette') {
                for (let i = 0; i < document.getElementsByClassName('pgnn-m-vignette-container').length; i++) {
                    document.getElementsByClassName('pgnn-m-vignette-container')[i].parentElement.removeAttribute('id');
                    document.getElementsByClassName('pgnn-m-vignette-container')[i].remove();
                    PgnNParams.PGNN_VGN_TIMEELAPSED = 0;
                }
            }
        } else {
            if (widgetType == 'd-vignette') {
                document.getElementsByClassName('pgnn-d-vignette-container')[0].style.display = "none";
            }
            else if (widgetType == 'm-vignette') {
                document.getElementsByClassName('pgnn-m-vignette-container')[0].style.display = "none";
            }
        }
    }

    function manageStickyCloseClick(widgetType) {
        if (widgetType == 'm-sticky-bottom') {
            while (document.querySelectorAll(".pgnn-m-sticky-bottom-container").length > 0) {
                document.querySelectorAll(".pgnn-m-sticky-bottom-container")[0].parentElement.removeAttribute('id');
                document.querySelectorAll(".pgnn-m-sticky-bottom-container")[0].remove();
            }
        } else if (widgetType == 'd-sticky-bottom') {
            while (document.querySelectorAll(".pgnn-d-sticky-bottom-container").length > 0) {
                document.querySelectorAll(".pgnn-d-sticky-bottom-container")[0].parentElement.removeAttribute('id');
                document.querySelectorAll(".pgnn-d-sticky-bottom-container")[0].remove();
            }
        }
    }

    function renderpbjsAds(adIds) {
        for (var i = 0; i < adIds.length; i++) {
            var currBid = window[PgnNParams.PBJSINSTANCE_NAME].getHighestCpmBids(adIds[i]);
            if (currBid.length > 0) {
                if (currBid[0].mediaType == "banner") {
                    renderBannerOne(currBid[0]);
                } else if (currBid[0].mediaType == "native") {
                    renderNativeOne(currBid[0]);
                }
            }
        }
    }

    function renderBannerOne(winningBid) {
        if (winningBid && winningBid.adId) {
            var div = document.getElementById(winningBid.adUnitCode);
            if (div) {
                div.innerHTML = "";
                const iframe = document.createElement('iframe');
                iframe.scrolling = 'no';
                iframe.frameBorder = '0';
                iframe.marginHeight = '0';
                iframe.marginHeight = '0';
                iframe.name = `prebid_ads_iframe_${winningBid.adUnitCode}`;
                iframe.title = '3rd party ad content';
                iframe.sandbox.add(
                    'allow-forms',
                    'allow-popups',
                    'allow-popups-to-escape-sandbox',
                    'allow-same-origin',
                    'allow-scripts',
                    'allow-top-navigation-by-user-activation'
                );
                iframe.setAttribute('aria-label', 'Advertisment');
                iframe.style.setProperty('border', '0');
                iframe.style.setProperty('margin', '0');
                iframe.style.setProperty('overflow', 'hidden');
                div.appendChild(iframe);
                const iframeDoc = iframe.contentWindow.document;
                window[PgnNParams.PBJSINSTANCE_NAME].renderAd(iframeDoc, winningBid.adId);

                // most browsers have a default margin of 8px . We add those after prebid has written to the iframe.
                // internally prebid uses document.write or inserts an element. Either way, this is safe to do here.
                // document.write is sync.
                // see https://github.com/prebid/Prebid.js/blob/92daa81f277598cbed486cf8be01ce796aa80c8f/src/prebid.js#L555-L588

                // you may also use "all: unset".
                // @see https://www.youtube.com/shorts/z47iLmBeRXY

                const normalizeCss = `/*! normalize.css v8.0.1 | MIT License | github.com/necolas/normalize.css */button,hr,input{overflow:visible}progress,sub,sup{vertical-align:baseline}[type=checkbox],[type=radio],legend{box-sizing:border-box;padding:0}html{line-height:1.15;-webkit-text-size-adjust:100%}body{margin:0}details,main{display:block}h1{font-size:2em;margin:.67em 0}hr{box-sizing:content-box;height:0}code,kbd,pre,samp{font-family:monospace,monospace;font-size:1em}a{background-color:transparent}abbr[title]{border-bottom:none;text-decoration:underline;text-decoration:underline dotted}b,strong{font-weight:bolder}small{font-size:80%}sub,sup{font-size:75%;line-height:0;position:relative}sub{bottom:-.25em}sup{top:-.5em}img{border-style:none}button,input,optgroup,select,textarea{font-family:inherit;font-size:100%;line-height:1.15;margin:0}button,select{text-transform:none}[type=button],[type=reset],[type=submit],button{-webkit-appearance:button}[type=button]::-moz-focus-inner,[type=reset]::-moz-focus-inner,[type=submit]::-moz-focus-inner,button::-moz-focus-inner{border-style:none;padding:0}[type=button]:-moz-focusring,[type=reset]:-moz-focusring,[type=submit]:-moz-focusring,button:-moz-focusring{outline:ButtonText dotted 1px}fieldset{padding:.35em .75em .625em}legend{color:inherit;display:table;max-width:100%;white-space:normal}textarea{overflow:auto}[type=number]::-webkit-inner-spin-button,[type=number]::-webkit-outer-spin-button{height:auto}[type=search]{-webkit-appearance:textfield;outline-offset:-2px}[type=search]::-webkit-search-decoration{-webkit-appearance:none}::-webkit-file-upload-button{-webkit-appearance:button;font:inherit}summary{display:list-item}[hidden],template{display:none}`;
                const iframeStyle = iframeDoc.createElement('style');
                iframeStyle.appendChild(iframeDoc.createTextNode(normalizeCss));
                iframeDoc.head.appendChild(iframeStyle);
            }
        }
    }

    function renderNativeOne(currBid) {
        if (currBid && currBid.adId) {
            var div = document.getElementById(currBid.adUnitCode);
            throw new Error('Not implemented yet!');
        }
    }

    function isBlockedUrl(url) {
        const excludeUrls = new Array(
            "https://www.kampanyaradar.com/kampanya/bmw-i4",
            "https://www.kampanyaradar.com/kampanya/bmw-3-serisi-sedan",
            "https://www.kampanyaradar.com/kampanya/yeni-bmw-ix1"
        );
        if (excludeUrls.includes(url.split("?")[0])) {
            console.log("PgnNParams.PGNN_ACTIVE:0 => " + document.location.href);
            PgnNParams.PGNN_ACTIVE = 0;
        }
        return PgnNParams.PGNN_ACTIVE;
    }

    function trackNewsItemClick(itm, paramsObj) {
        if (PgnNParams.TrackNewsClick) {
            var url = itm.href.split("?")[0];
            if (url != undefined && url != null) {
                var obj = {};
                obj.url = url;
                obj.widget = paramsObj._widgetType;

                var oXHR = new XMLHttpRequest();
                oXHR.open("POST", 'https://analytics.pigeoon.com/api/pv', true);

                oXHR.setRequestHeader("Content-Type", "application/json");

                oXHR.onreadystatechange = function () {
                    if (oXHR.readyState === 4) {
                        if (oXHR.status === 200) {
                            PgnN.PgnNLog("Pageview recorded => " + url);
                        }
                    }
                }
                oXHR.send(JSON.stringify(obj));
            }
        }
    }

    return {
        TimeLog: function (message) {
            return timeLog(message)
        },
        PgnNLog: function (message) {
            return pgnNLog(message);
        },
        GetCookie: function (cookieName) {
            return getCookie(cookieName);
        },
        SetCookie: function (cname, cvalue, exSeconds) {
            return setCookie(cname, cvalue, exSeconds);
        },
        IsMobile: function () {
            return isMobile();
        },
        IsIpad: function () {
            return isIpad();
        },
        GenerateRandomString: function (length) {
            return generateRandomString(length);
        },
        GetQueryStringByName: function (name) {
            return getQueryStringByName(name);
        },
        InitNativeAds: function (itm) {
            return initNativeAds(itm);
        },
        InitOutstreamAds: function (divId, placementId) {
            return initOutstreamAds(divId, placementId);
        },
        LoadScript: function (url, callback) {
            return loadScript(url, callback);
        },
        LoadCss: function (url, callback) {
            return loadCss(url, callback);
        },
        FixSizeForAdUnit: function (width, height, divId, mediaType, paramsObj) {
            return fixSizeForAdUnit(width, height, divId, mediaType, paramsObj);
        },
        ManageVgnCloseClick: function (widgetType) {
            return manageVgnCloseClick(widgetType);
        },
        ManageStickyCloseClick: function (widgetType) {
            return manageStickyCloseClick(widgetType);
        },
        ManageVignette: function () {
            return manageVignette();
        },
        ManageStandard: function () {
            return manageStandard();
        },
        ManageNative: function () {
            return manageNative();
        },
        RenderpbjsAds: function () {
            return renderpbjsAds();
        },
        TrackNewsItemClick: function (itm, paramsObj) {
            return trackNewsItemClick(itm, paramsObj);
        },
        IsBlockedUrl: function (url) {
            return isBlockedUrl(url);
        }
    }
}());

function pgnnStartListeners() {
    PgnNParams.PGNN_ACTIVE = PgnN.IsBlockedUrl(document.location.href);
    if (PgnNParams.PGNN_ACTIVE) {
        PgnN.ManageVignette();
        PgnN.ManageStandard();
        PgnN.ManageNative();
    }

    document.addEventListener('scroll', (e) => {
        if (PgnNParams.PGNN_ACTIVE) {
            PGNNINPROGRESS = 1;
            var pgnnWidgets = document.querySelectorAll("[class^=pgn-native]");
            for (let k = 0; k < pgnnWidgets.length; k++) {
                if (pgnnWidgets[k].getAttribute("id") == null && (pgnnWidgets[k].getAttribute("pgn-native-trgType") == null || pgnnWidgets[k].getAttribute("pgn-native-trgType") != "instant")) {
                    var slotId = "pgn-native-id-" + PgnN.GenerateRandomString(10);
                    pgnnWidgets[k].setAttribute("id", slotId);
                    PgnN.PgnNLog("New box identified => " + slotId);
                }
            }

            for (let i = 0; i < pgnnWidgets.length; i++) {
                try {
                    if (pgnnWidgets[i].getAttribute("id") != null && (pgnnWidgets[i].getAttribute("pgn-native-trgType") == null || pgnnWidgets[i].getAttribute("pgn-native-trgType") != "instant")) {
                        var pgnLazySlotId = pgnnWidgets[i].getAttribute("id");
                        var itm = document.getElementById(pgnLazySlotId);
                        if (itm != null && itm.getAttribute("id").includes("pgn-native-") && !PgnNParams.pgnNativeViewedSlots.includes(pgnLazySlotId)) {
                            var bounding = itm.getBoundingClientRect();
                            if ((bounding.top - window.innerHeight) < parseInt(PgnNParams.pgnNativeViewableOffset)) {
                                PgnN.PgnNLog(pgnLazySlotId + " now visible!");
                                PgnN.PgnNLog(pgnLazySlotId + "ad initialized from SCROLL! BoundingTop:" + bounding.top + " window Inner Height:" + window.innerHeight + " offset:" + PgnNParams.pgnNativeViewableOffset + " bTop-Height:" + (bounding.top - window.innerHeight));
                                PgnN.InitNativeAds(pgnLazySlotId);
                            }
                        }
                    }
                } catch (err) {
                    console.error(err.message);
                }
            }
        }
    });

    document.addEventListener('click', (e) => {
        try {
            if (e.target.getAttribute('class') == 'pgnn-d-vignette-close-button') {
                PgnN.ManageVgnCloseClick("d-vignette");
            }
            else if (e.target.getAttribute('class') == 'pgnn-m-vignette-close-button') {
                PgnN.ManageVgnCloseClick("m-vignette");
            }
            else if (e.target.getAttribute('class').includes('pgnn-m-sticky-bottom-close-button')) {
                PgnN.ManageStickyCloseClick("m-sticky-bottom");
            }
            else if (e.target.getAttribute('class').includes('pgnn-d-sticky-bottom-close-button')) {
                PgnN.ManageStickyCloseClick("d-sticky-bottom");
            }
        } catch (err) {

        }

    });

    document.addEventListener('mouseover', (e) => {
        try {
            if (e.target.getAttribute('class') == 'pgnn-d-vignette-close-button' || e.target.getAttribute('class') == 'pgnn-m-vignette-close-button') {
                e.target.style.cursor = "pointer";
            }
            else if (e.target.getAttribute('class').includes('pgnn-m-sticky-bottom-close-button') || e.target.getAttribute('class').includes('pgnn-d-sticky-bottom-close-button')) {
                e.target.style.cursor = "pointer";
            }
        } catch (err) {

        }
    });

    document.addEventListener('mouseout', (e) => {
        try {
            if (e.target.getAttribute('class') == 'pgnn-d-vignette-close-button' || e.target.getAttribute('class') == 'pgnn-d-vignette-close-button') {
                e.target.style.cursor = "default";
            }
            else if (e.target.getAttribute('class').includes('pgnn-m-sticky-bottom-close-button') || e.target.getAttribute('class').includes('pgnn-d-sticky-bottom-close-button')) {
                e.target.style.cursor = "default";
            }
        } catch (err) {

        }
    });

    //addEventListener("load", (event) => {
    //    var pgnNIntersectionHandler = (items, observer) => {
    //        var arr = [];
    //        items.forEach((item) => {
    //            if (item.isIntersecting) {
    //                console.log("intersection observer çalıştı! " + item.getAttribute("id"));
    //                observer.unobserve(document.getElementById(item.target.getAttribute("id")));
    //                arr.push(item.target.getAttribute("id"));
    //            }
    //        });
    //        if (arr.length > 0) {
    //            var pgnLazySlotId = pgnnWidgets[i].getAttribute("id");
    //            PgnN.PgnNLog(pgnLazySlotId + " now visible!");
    //            //PgnN.PgnNLog(pgnLazySlotId + "ad initialized from SCROLL! BoundingTop:" + bounding.top + " window Inner Height:" + window.innerHeight + " offset:" + PgnNParams.pgnNativeViewableOffset + " bTop-Height:" + (bounding.top - window.innerHeight));
    //            PgnN.InitNativeAds(pgnLazySlotId);
    //        }
    //    }

    //    const pgnNMutationObserver = new MutationObserver((mutationsList) => {
    //        try {
    //            mutationsList.forEach(mutation => {
    //                mutation.addedNodes.forEach(item => {
    //                    if (PgnNParams.PGNN_ACTIVE) {
    //                        PGNNINPROGRESS = 1;
    //                        if (
    //                            item.tagName != null
    //                            && item.tagName.toLowerCase() === "div"
    //                            && item.getAttribute("class") != null
    //                            && item.getAttribute("class").includes("pgn-native")
    //                            && (item.getAttribute("pgn-native-trgType") == null || item.getAttribute("pgn-native-trgType") != "instant")) {
    //                            var slotId = "pgn-native-id-" + PgnN.GenerateRandomString(10);
    //                            item.setAttribute("id", slotId);
    //                            PgnN.PgnNLog("New box identified => " + slotId);

    //                            var intersectionObserver = new IntersectionObserver(pgnNIntersectionHandler, { root: null, rootMargin: PgnNParams.pgnNativeViewableOffset + "px", threshold: 0 })
    //                            intersectionObserver.observe(item);

    //                            //if (!PgnNParams.pgnNativeViewedSlots.includes(pgnLazySlotId)) {
    //                            //    PgnN.PgnNLog(pgnLazySlotId + " initiating native ads!");
    //                            //    PgnN.InitNativeAds(pgnLazySlotId);
    //                            //    observer.unobserve(document.getElementById(item.target.getAttribute("id")));
    //                            //}
    //                        }
    //                    }
    //                });
    //            });
    //        }
    //        catch (err) {
    //            console.error(err.message);
    //        }
    //    });
    //    pgnNMutationObserver.observe(document.documentElement || document.body, { attributes: true, childList: true, characterData: true, subtree: true });
    //});
}



PgnN.LoadScript('https://securepubads.g.doubleclick.net/tag/js/gpt.js', pgnnStartListeners);