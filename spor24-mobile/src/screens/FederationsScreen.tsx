import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Linking,
  StatusBar,
  SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

// ==========================================
// 1. TYPESCRIPT DATA INTERFACES
// ==========================================
export type TabType = 'federations' | 'branches';
export type SortOption = 'views' | 'news' | 'alphabetical';

export interface FederationItem {
  id: string;
  name: string;
  code: string;
  tagline: string;
  icon: string;
  accent_color: string;
  status: 'live' | 'pool';
  news_count: number;
  total_views: number;
  media_share_percentage: number;
  latest_news: {
    title: string;
    timestamp: string;
  };
  official_website: string;
  category: 'combat' | 'olympic' | 'team' | 'racket' | 'water';
}

export interface BranchItem {
  id: string;
  name: string;
  federation_name: string;
  active_athletes: number;
  total_clubs: number;
  news_count: number;
}

// ==========================================
// 2. FALLBACK / OFFLINE MOCK DATA
// ==========================================
const FALLBACK_FEDERATIONS: FederationItem[] = [
  {
    id: 'tbf-boxing',
    name: 'Türkiye Boks Federasyonu',
    code: 'TBF',
    tagline: 'Olimpik & Ulusal Branş Komitesi',
    icon: '🥊',
    accent_color: '#E11D48',
    status: 'live',
    news_count: 69,
    total_views: 21210,
    media_share_percentage: 18.7,
    latest_news: {
      title: 'Milli Boksörlerimiz Paris Olimpiyat Kotası İçin Kastamonu Kampında',
      timestamp: '14:32',
    },
    official_website: 'https://boks.gov.tr',
    category: 'combat',
  },
  {
    id: 'tgf-wrestling',
    name: 'Türkiye Güreş Federasyonu',
    code: 'TGF',
    tagline: 'Ata Sporu & Dünya Şampiyonaları Masası',
    icon: '🤼',
    accent_color: '#F59E0B',
    status: 'live',
    news_count: 58,
    total_views: 19450,
    media_share_percentage: 16.2,
    latest_news: {
      title: 'Taha Akgül ve Rıza Kayaalp\'ten Genç Güreşçilere Altın Tavsiyeler',
      timestamp: '3 saat önce',
    },
    official_website: 'https://tgf.gov.tr',
    category: 'combat',
  },
  {
    id: 'tbf-cycling',
    name: 'Türkiye Bisiklet Federasyonu',
    code: 'TBF',
    tagline: 'UCI ProSeries & Yol Yarışları Kurulu',
    icon: '🚴',
    accent_color: '#3B82F6',
    status: 'live',
    news_count: 42,
    total_views: 15820,
    media_share_percentage: 13.1,
    latest_news: {
      title: '59. Cumhurbaşkanlığı Türkiye Bisiklet Turu\'nda Tarihi Start',
      timestamp: '11:45',
    },
    official_website: 'https://bisiklet.gov.tr',
    category: 'olympic',
  },
  {
    id: 'twkf-wushu',
    name: 'Türkiye Wushu Kung Fu Federasyonu',
    code: 'TWKF',
    tagline: 'Taolu & Sanda Dallar Arşivi',
    icon: '🥋',
    accent_color: '#8B5CF6',
    status: 'pool',
    news_count: 31,
    total_views: 9410,
    media_share_percentage: 7.8,
    latest_news: {
      title: 'Balkan Wushu Şampiyonası\'nda Ay-Yıldızlı Ekibimizden 8 Altın',
      timestamp: 'Dün',
    },
    official_website: 'https://wushu.gov.tr',
    category: 'combat',
  },
  {
    id: 'tkf-karate',
    name: 'Türkiye Karate Federasyonu',
    code: 'TKF',
    tagline: 'Kata & Kumite Dünya Turnuva Masası',
    icon: '🥋',
    accent_color: '#EC4899',
    status: 'live',
    news_count: 28,
    total_views: 8120,
    media_share_percentage: 6.7,
    latest_news: {
      title: 'Karate 1 Premier Lig Paris Etabında Milli Takımımızdan 4 Final',
      timestamp: '1 gün önce',
    },
    official_website: 'https://karate.gov.tr',
    category: 'combat',
  },
  {
    id: 'tmtf-muaythai',
    name: 'Türkiye Muay Thai Federasyonu',
    code: 'TMTF',
    tagline: 'IFMA & Gençler Ligi',
    icon: '🥊',
    accent_color: '#64748B',
    status: 'pool',
    news_count: 24,
    total_views: 6890,
    media_share_percentage: 5.7,
    latest_news: {
      title: 'Dünya Gençler Muay Thai Şampiyonası Kadrosu Belirlendi',
      timestamp: '2 gün önce',
    },
    official_website: 'https://muaythai.gov.tr',
    category: 'combat',
  },
];

const CATEGORY_CHIPS = [
  { id: 'all', label: 'Tümü (44)' },
  { id: 'combat', label: 'Dövüş Sporları (14)' },
  { id: 'olympic', label: 'Olimpik Dallar (18)' },
  { id: 'team', label: 'Takım Sporları (8)' },
  { id: 'water', label: 'Su Sporları (4)' },
];

// ==========================================
// 3. MAIN COMPONENT: FederationsScreen
// ==========================================
export const FederationsScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  // State Management
  const [activeTab, setActiveTab] = useState<TabType>('federations');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('views');
  const [federations, setFederations] = useState<FederationItem[]>(FALLBACK_FEDERATIONS);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>('2 dk önce');

  // Dynamic Backend Fetch: https://spor24.net/api/categories/
  const fetchFederationData = async () => {
    try {
      setLoading(true);
      const res = await fetch('https://spor24.net/api/categories/');
      if (res.ok) {
        const data = await res.json();
        if (data && Array.isArray(data.results || data)) {
          setFederations(data.results || data);
          setLastSyncTime('Şimdi güncellendi');
        }
      }
    } catch (error) {
      console.warn(
        'Federasyon API bağlantısı sağlanamadı, çevrimdışı model devrede:',
        error
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFederationData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchFederationData();
  };

  // Filter & Sort Logic
  const processedFederations = useMemo(() => {
    return federations
      .filter((item) => {
        const matchesSearch =
          item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.tagline.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesCategory =
          selectedCategory === 'all' ? true : item.category === selectedCategory;
        return matchesSearch && matchesCategory;
      })
      .sort((a, b) => {
        if (sortBy === 'views') return b.total_views - a.total_views;
        if (sortBy === 'news') return b.news_count - a.news_count;
        if (sortBy === 'alphabetical') return a.name.localeCompare(b.name, 'tr-TR');
        return 0;
      });
  }, [federations, searchQuery, selectedCategory, sortBy]);

  // Open External Official Portal
  const handleOpenWebsite = (url: string) => {
    if (url) {
      Linking.openURL(url).catch((err) => console.error('Link açılamadı:', err));
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-[#0B0E14]">
      <StatusBar barStyle="light-content" backgroundColor="#0B0E14" />

      {/* 1. TOP APP BAR & OTONOM SENKRONİZASYON BANDI */}
      <View className="bg-[#10131A] border-b border-[#1E232E] px-4 pt-3 pb-2.5">
        <View className="flex-row items-center justify-between mb-2">
          <View className="flex-row items-center">
            <View className="w-2.5 h-2.5 rounded-full bg-[#E11D48] mr-2 animate-ping" />
            <Text className="text-white text-base font-black tracking-tight">
              Federasyon & Branş Havuzu
            </Text>
          </View>
          <View className="bg-[#181C24] px-2 py-0.5 rounded border border-[#262B36]">
            <Text className="text-[#E11D48] text-[9px] font-black tracking-wider uppercase">
              CANLI VERİ
            </Text>
          </View>
        </View>

        {/* METRİK DURUM BİLGİSİ */}
        <View className="flex-row items-center justify-between pt-1 border-t border-[#1C212B]">
          <View className="flex-row items-center">
            <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
            <Text className="text-[#94A3B8] text-[10px] font-medium">
              <Text className="text-[#F1F5F9] font-bold">44</Text> Aktif Kaynak •{' '}
              <Text className="text-[#10B981] font-bold">27</Text> Canlı Akışta •{' '}
              <Text className="text-[#64748B] font-bold">17</Text> Havuzda
            </Text>
          </View>
          <Text className="text-[#64748B] text-[9px] font-mono">⚡ {lastSyncTime}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#E11D48"
          />
        }
      >
        {/* 2. ÇİFT SEKMELİ GEÇİŞ (SEGMENTED TABS) */}
        <View className="flex-row mx-4 mt-3.5 p-1 rounded-xl bg-[#141822] border border-[#202532]">
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => setActiveTab('federations')}
            className={`flex-1 py-2 rounded-lg flex-row items-center justify-center ${
              activeTab === 'federations' ? 'bg-[#E11D48]' : 'bg-transparent'
            }`}
          >
            <Text className="text-xs mr-1.5">🛡</Text>
            <Text
              className={`text-xs font-black tracking-wider uppercase ${
                activeTab === 'federations' ? 'text-white' : 'text-[#94A3B8]'
              }`}
            >
              Federasyonlar (44)
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            activeOpacity={0.85}
            onPress={() => setActiveTab('branches')}
            className={`flex-1 py-2 rounded-lg flex-row items-center justify-center ${
              activeTab === 'branches' ? 'bg-[#E11D48]' : 'bg-transparent'
            }`}
          >
            <Text className="text-xs mr-1.5">⚖️</Text>
            <Text
              className={`text-xs font-black tracking-wider uppercase ${
                activeTab === 'branches' ? 'text-white' : 'text-[#94A3B8]'
              }`}
            >
              Spor Branşları (48)
            </Text>
          </TouchableOpacity>
        </View>

        {/* 3. AKILLI ARAMA ÇUBUĞU */}
        <View className="mx-4 mt-3">
          <View className="flex-row items-center bg-[#141822] px-3.5 py-2.5 rounded-xl border border-[#202532]">
            <Text className="text-sm mr-2 text-[#64748B]">🔍</Text>
            <TextInput
              placeholder="Federasyon veya branş filtrele (Boks, Güreş...)"
              placeholderTextColor="#64748B"
              value={searchQuery}
              onChangeText={setSearchQuery}
              className="flex-1 text-white text-xs p-0 font-medium"
            />
            {searchQuery.length > 0 && (
              <TouchableOpacity onPress={() => setSearchQuery('')}>
                <Text className="text-[#94A3B8] text-xs">✕</Text>
              </TouchableOpacity>
            )}
          </View>
        </View>

        {/* 4. YATAY KATEGORİ ÇİPLERİ */}
        <View className="mt-3">
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16 }}
            className="flex-row"
          >
            {CATEGORY_CHIPS.map((chip) => {
              const isSelected = selectedCategory === chip.id;
              return (
                <TouchableOpacity
                  key={chip.id}
                  onPress={() => setSelectedCategory(chip.id)}
                  className={`px-3 py-1.5 rounded-full mr-2 border ${
                    isSelected
                      ? 'bg-[#E11D48] border-[#E11D48]'
                      : 'bg-[#141822] border-[#222836]'
                  }`}
                >
                  <Text
                    className={`text-[11px] font-bold ${
                      isSelected ? 'text-white' : 'text-[#94A3B8]'
                    }`}
                  >
                    {chip.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* 5. SIRALAMA FİLTRE MATRİSİ */}
        <View className="flex-row items-center justify-between px-4 mt-4 mb-2">
          <View className="flex-row items-center">
            <Text className="text-[#64748B] text-[10px] font-bold mr-1">SIRALA:</Text>
          </View>
          <View className="flex-row items-center space-x-1.5">
            <TouchableOpacity
              onPress={() => setSortBy('views')}
              className={`px-2.5 py-1 rounded-md border flex-row items-center ${
                sortBy === 'views'
                  ? 'bg-[#1E232E] border-[#FFD700]'
                  : 'bg-[#12161F] border-[#1E232E]'
              }`}
            >
              <Text className="text-[10px] text-[#FFD700] mr-1">🔥</Text>
              <Text
                className={`text-[10px] font-bold ${
                  sortBy === 'views' ? 'text-[#FFD700]' : 'text-[#94A3B8]'
                }`}
              >
                Okunma
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setSortBy('news')}
              className={`px-2.5 py-1 rounded-md border flex-row items-center ${
                sortBy === 'news'
                  ? 'bg-[#1E232E] border-[#E11D48]'
                  : 'bg-[#12161F] border-[#1E232E]'
              }`}
            >
              <Text className="text-[10px] text-white mr-1">📰</Text>
              <Text
                className={`text-[10px] font-bold ${
                  sortBy === 'news' ? 'text-white' : 'text-[#94A3B8]'
                }`}
              >
                Haber
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={() => setSortBy('alphabetical')}
              className={`px-2.5 py-1 rounded-md border flex-row items-center ${
                sortBy === 'alphabetical'
                  ? 'bg-[#1E232E] border-white'
                  : 'bg-[#12161F] border-[#1E232E]'
              }`}
            >
              <Text className="text-[10px] text-white mr-1">🔤</Text>
              <Text
                className={`text-[10px] font-bold ${
                  sortBy === 'alphabetical' ? 'text-white' : 'text-[#94A3B8]'
                }`}
              >
                A-Z
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* 6. FEDERASYON KARTLARI LİSTESİ */}
        <View className="px-4 pb-20">
          {loading && !refreshing ? (
            <ActivityIndicator color="#E11D48" size="large" className="my-10" />
          ) : processedFederations.length === 0 ? (
            <View className="py-12 items-center justify-center">
              <Text className="text-3xl mb-2">🔍</Text>
              <Text className="text-white text-sm font-bold">Sonuç Bulunamadı</Text>
              <Text className="text-[#64748B] text-xs mt-1 text-center">
                Arama kriterlerinize uygun federasyon veya branş kaydı mevcut değil.
              </Text>
            </View>
          ) : (
            processedFederations.map((fed) => (
              <View
                key={fed.id}
                className="mb-3.5 p-3.5 rounded-2xl bg-[#121620] border border-[#1E2432] shadow-xl"
              >
                {/* HEADER ROW: ICON, NAME, STATUS */}
                <View className="flex-row items-center justify-between mb-2">
                  <View className="flex-row items-center flex-1 mr-2">
                    <View
                      style={{ backgroundColor: `${fed.accent_color}20` }}
                      className="w-10 h-10 rounded-xl items-center justify-center mr-3 border border-white/10"
                    >
                      <Text className="text-base">{fed.icon}</Text>
                    </View>
                    <View className="flex-1">
                      <Text className="text-white font-black text-sm leading-5" numberOfLines={1}>
                        {fed.name}
                      </Text>
                      <Text className="text-[#94A3B8] text-[10px] font-medium" numberOfLines={1}>
                        {fed.code} • {fed.tagline}
                      </Text>
                    </View>
                  </View>

                  {/* STATUS BADGE */}
                  <View
                    className={`px-2 py-0.5 rounded-full flex-row items-center border ${
                      fed.status === 'live'
                        ? 'bg-[#10B981]/10 border-[#10B981]/30'
                        : 'bg-[#1E232E] border-[#2E3646]'
                    }`}
                  >
                    <View
                      className={`w-1.5 h-1.5 rounded-full mr-1.5 ${
                        fed.status === 'live' ? 'bg-[#10B981] animate-pulse' : 'bg-[#64748B]'
                      }`}
                    />
                    <Text
                      className={`text-[9px] font-bold ${
                        fed.status === 'live' ? 'text-[#10B981]' : 'text-[#94A3B8]'
                      }`}
                    >
                      {fed.status === 'live' ? 'Canlı Akış' : 'Havuzda'}
                    </Text>
                  </View>
                </View>

                {/* METRICS ROW */}
                <View className="flex-row items-center justify-between py-2 border-t border-[#1C212D]">
                  <View className="flex-row items-center">
                    <Text className="text-xs mr-1 text-[#94A3B8]">📰</Text>
                    <Text className="text-white text-xs font-bold mr-1">{fed.news_count}</Text>
                    <Text className="text-[#64748B] text-[10px]">Haber</Text>
                  </View>
                  <View className="flex-row items-center">
                    <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                    <Text className="text-[#FFD700] text-xs font-bold mr-1">
                      {(fed.total_views || 0).toLocaleString('tr-TR')}
                    </Text>
                    <Text className="text-[#64748B] text-[10px]">Okunma</Text>
                  </View>
                  <View className="bg-[#181C26] px-2 py-0.5 rounded border border-[#252C3A]">
                    <Text className="text-[#E11D48] text-[10px] font-black">
                      %{fed.media_share_percentage} Pay
                    </Text>
                  </View>
                </View>

                {/* MICRO VOLUME PROGRESS BAR */}
                <View className="w-full h-1 bg-[#1A1E29] rounded-full overflow-hidden my-1">
                  <View
                    style={{
                      width: `${Math.min(fed.media_share_percentage * 3.5, 100)}%`,
                      backgroundColor: fed.accent_color,
                    }}
                    className="h-full rounded-full"
                  />
                </View>

                {/* LATEST NEWS TICKER */}
                {fed.latest_news ? (
                  <TouchableOpacity
                    activeOpacity={0.85}
                    onPress={() =>
                      navigation.navigate('NewsDetailScreen', {
                        newsId: fed.id,
                      })
                    }
                    className="mt-2 p-2 rounded-lg bg-[#0D1017] border border-[#181D28] flex-row items-center justify-between"
                  >
                    <View className="flex-row items-center flex-1 mr-2">
                      <Text className="text-[#E11D48] text-[9px] mr-1.5 font-bold">⚡ SON GELİŞME</Text>
                      <Text className="text-[#CBD5E1] text-[11px] font-medium flex-1" numberOfLines={1}>
                        {fed.latest_news.title}
                      </Text>
                    </View>
                    <Text className="text-[#64748B] text-[9px] font-mono">
                      {fed.latest_news.timestamp}
                    </Text>
                  </TouchableOpacity>
                ) : null}

                {/* FOOTER ACTIONS: OFFICIAL SITE & DRILLDOWN */}
                <View className="flex-row items-center justify-between pt-2.5 mt-2 border-t border-[#1C212D]">
                  <TouchableOpacity
                    onPress={() => handleOpenWebsite(fed.official_website)}
                    className="flex-row items-center"
                  >
                    <Text className="text-[#E11D48] text-xs font-bold mr-1">
                      Resmi Portala Git
                    </Text>
                    <Text className="text-[#E11D48] text-xs">↗</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() =>
                      navigation.navigate('NewsDetailScreen', {
                        newsId: fed.id,
                      })
                    }
                    className="w-6 h-6 rounded-full bg-[#181C26] items-center justify-center border border-[#252C3A]"
                  >
                    <Text className="text-[#94A3B8] text-xs font-bold">→</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}

          {/* OTONOM BOTLAR TALEP ET FOOTER BAND */}
          <View className="p-3.5 rounded-xl bg-[#141822] border border-[#222836] flex-row items-center justify-between mt-2">
            <View className="flex-row items-center flex-1 mr-2">
              <Text className="text-base mr-2">🤖</Text>
              <Text className="text-[#94A3B8] text-[10px] leading-4 flex-1">
                44 Federasyonun tümü 7/24 otonom botlarla taranarak medyaya aktarılmaktadır.
              </Text>
            </View>
            <TouchableOpacity onPress={() => Linking.openURL('https://spor24.net/iletisim')}>
              <Text className="text-[#FFD700] text-[10px] font-bold">Talep Et ↗</Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default FederationsScreen;
