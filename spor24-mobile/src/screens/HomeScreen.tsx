import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
  StatusBar,
  SafeAreaView,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');

// ==========================================
// 1. TYPESCRIPT DATA INTERFACES
// ==========================================
export interface NewsItem {
  id: string | number;
  title: string;
  summary?: string;
  federation: string;
  federation_code?: string;
  image_url: string;
  published_at: string;
  view_count: number;
  is_breaking?: boolean;
  is_featured?: boolean;
  content_id_hash?: string;
  category?: string;
}

export interface FederationChip {
  id: string;
  name: string;
  count: number;
}

// ==========================================
// 2. MOCK & FALLBACK DATA
// ==========================================
const FEDERATION_CATEGORIES: FederationChip[] = [
  { id: 'all', name: 'Tümü (44)', count: 184 },
  { id: 'boxing', name: 'Boks', count: 69 },
  { id: 'wrestling', name: 'Güreş', count: 58 },
  { id: 'cycling', name: 'Bisiklet', count: 42 },
  { id: 'wushu', name: 'Wushu Kung Fu', count: 31 },
  { id: 'karate', name: 'Karate', count: 28 },
  { id: 'muaythai', name: 'Muay Thai', count: 24 },
  { id: 'taekwondo', name: 'Tekvando', count: 19 },
  { id: 'archery', name: 'Okçuluk', count: 15 },
];

const FALLBACK_HEADLINES: NewsItem[] = [
  {
    id: '1',
    title:
      '59. Cumhurbaşkanlığı Bisiklet Turu Başladı: 25 Ülkeden 170 Dünya Yıldızı Pedal Çeviriyor',
    summary:
      'Antalya-Kemer etabıyla start alan TUR 2024, 1.250 kilometrelik dev parkurda dünyanın en prestijli WorldTour bisiklet takımlarını buluşturuyor.',
    federation: 'TÜRKİYE BİSİKLET FEDERASYONU',
    image_url:
      'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=800&q=80',
    published_at: '11:45',
    view_count: 2150,
    is_featured: true,
  },
  {
    id: '2',
    title:
      'Milli Boksörlerimiz Paris Olimpiyat Kotası İçin Kastamonu Kampında',
    summary:
      'Avrupa ve Dünya Şampiyonu boksörlerimiz, olimpiyat eleme müsabakaları öncesi son hazırlıklarını sürdürüyor.',
    federation: 'TÜRKİYE BOKS FEDERASYONU',
    image_url:
      'https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?auto=format&fit=crop&w=800&q=80',
    published_at: '14:32',
    view_count: 3420,
    is_featured: true,
  },
];

const FALLBACK_STREAM: NewsItem[] = [
  {
    id: '3',
    title: 'Minderde Taktik Devrimi: Ağır Sıklette Altın Madalyaya Giden Yol',
    federation: 'TÜRKİYE GÜREŞ FEDERASYONU',
    image_url:
      'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=600&q=80',
    published_at: '2 saat önce',
    view_count: 3120,
    is_breaking: true,
  },
  {
    id: '4',
    title:
      'Balkan Wushu Şampiyonası’nda Ay-Yıldızlı Ekibimizden 8 Altın Madalya',
    federation: 'TÜRKİYE WUSHU KUNG FU FEDERASYONU',
    image_url:
      'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=600&q=80',
    published_at: '3 saat önce',
    view_count: 1890,
  },
  {
    id: '5',
    title:
      'Karate 1 Premier Lig Paris Etabında Milli Takımımızdan 4 Final',
    federation: 'TÜRKİYE KARATE FEDERASYONU',
    image_url:
      'https://images.unsplash.com/photo-1599058945522-28d584b6f0ff?auto=format&fit=crop&w=600&q=80',
    published_at: '5 saat önce',
    view_count: 2450,
  },
  {
    id: '6',
    title:
      'Dünya Gençler Muay Thai Şampiyonası İçin Milli Takım Kadrosu Belirlendi',
    federation: 'TÜRKİYE MUAY THAI FEDERASYONU',
    image_url:
      'https://images.unsplash.com/photo-1517438322307-e67111335449?auto=format&fit=crop&w=600&q=80',
    published_at: 'Dün',
    view_count: 1420,
  },
];

// ==========================================
// 3. MAIN COMPONENT: HomeScreen
// ==========================================
export const HomeScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  const [selectedFederation, setSelectedFederation] = useState<string>('all');
  const [featuredNews, setFeaturedNews] = useState<NewsItem[]>(FALLBACK_HEADLINES);
  const [newsStream, setNewsStream] = useState<NewsItem[]>(FALLBACK_STREAM);
  const [breakingNews, setBreakingNews] = useState<string>(
    '59. Cumhurbaşkanlığı Bisiklet Turu için Kemer etabı startı verildi. 25 ülkeden 170 sporcu yarışıyor...'
  );
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Map Backend API object to NewsItem
  const mapApiNewsToNewsItem = (raw: any): NewsItem => {
    const imageUrl = raw.image || raw.resim || raw.image_url || '';
    const fullImage = imageUrl.startsWith('http')
      ? imageUrl
      : imageUrl.startsWith('/')
      ? `https://spor24.net${imageUrl}`
      : imageUrl
      ? `https://spor24.net/${imageUrl}`
      : 'https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?auto=format&fit=crop&w=800&q=80';

    const dateStr = raw.created_at || raw.published_at || '';
    let formattedDate = 'Bugün';
    if (dateStr) {
      try {
        const d = new Date(dateStr);
        if (!isNaN(d.getTime())) {
          formattedDate = d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
        }
      } catch {
        formattedDate = dateStr;
      }
    }

    return {
      id: raw.id,
      title: raw.title || '',
      summary: raw.summary || (raw.content ? raw.content.substring(0, 140) + '...' : ''),
      federation: raw.category_name || raw.federation || 'TÜRKİYE SPOR FEDERASYONLARI',
      federation_code: raw.federation_code || 'S24',
      image_url: fullImage,
      published_at: formattedDate,
      view_count: Number(raw.views ?? raw.view_count ?? raw.goruntulenme_sayisi ?? 0),
      is_breaking: Boolean(raw.is_breaking),
      is_featured: Boolean(raw.is_manset ?? raw.is_featured),
      content_id_hash: raw.content_id_hash || `SPOR24-${raw.id}`,
      category: raw.category_name || raw.category || 'Genel',
    };
  };

  // Live API Fetch
  const fetchNewsData = async () => {
    try {
      setLoading(true);
      const response = await fetch('https://spor24.net/api/news/');
      if (response.ok) {
        const data = await response.json();
        const rawList = data.results || (Array.isArray(data) ? data : []);
        if (Array.isArray(rawList) && rawList.length > 0) {
          const list: NewsItem[] = rawList.map(mapApiNewsToNewsItem);
          const featured = list.filter((n) => n.is_featured);
          const others = list.filter((n) => !n.is_featured);
          if (featured.length > 0) {
            setFeaturedNews(featured);
          } else {
            setFeaturedNews(list.slice(0, 4));
          }
          if (others.length > 0) {
            setNewsStream(others);
          } else {
            setNewsStream(list);
          }
        }
      }
    } catch (error) {
      console.warn(
        'API Bağlantısı sağlanamadı, çevrimdışı/yedek veri kullanılıyor:',
        error
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNewsData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchNewsData();
  };

  // Filter Stream based on Selected Federation Chip
  const filteredStream =
    selectedFederation === 'all'
      ? newsStream
      : newsStream.filter((item) =>
          item.federation.toLowerCase().includes(selectedFederation.toLowerCase())
        );

  return (
    <SafeAreaView className="flex-1 bg-[#0B0E14]">
      <StatusBar barStyle="light-content" backgroundColor="#0B0E14" />

      {/* TOP HEADER / APP BAR */}
      <View className="flex-row items-center justify-between px-4 py-3 border-b border-[#1E232E] bg-[#10131A]">
        <View className="flex-row items-center space-x-2">
          <View className="w-8 h-8 rounded-lg bg-[#E11D48] items-center justify-center shadow-lg shadow-[#E11D48]/30">
            <Text className="text-white font-black text-sm tracking-tighter">S24</Text>
          </View>
          <View>
            <View className="flex-row items-center">
              <Text className="text-white font-black text-lg tracking-wider">SPOR</Text>
              <Text className="text-[#E11D48] font-black text-lg">24</Text>
            </View>
            <Text className="text-[9px] text-[#94A3B8] font-medium tracking-widest uppercase -mt-1">
              44 Federasyon Medya Havuzu
            </Text>
          </View>
        </View>

        <View className="flex-row items-center space-x-3">
          <TouchableOpacity
            className="w-9 h-9 rounded-full bg-[#181C24] items-center justify-center border border-[#262B36]"
            onPress={() => navigation.navigate('LiveTvScreen')}
          >
            <View className="w-2 h-2 rounded-full bg-[#E11D48] absolute top-2 right-2 animate-ping" />
            <Text className="text-xs">📺</Text>
          </TouchableOpacity>
          <TouchableOpacity className="w-9 h-9 rounded-full bg-[#181C24] items-center justify-center border border-[#262B36]">
            <Text className="text-xs">🔔</Text>
          </TouchableOpacity>
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
        {/* 1. BREAKING NEWS FLASHTICKER */}
        <View className="bg-[#181C24] border-b border-[#262B36] flex-row items-center px-3 py-2">
          <View className="bg-[#E11D48] px-2 py-0.5 rounded mr-2 flex-row items-center">
            <View className="w-1.5 h-1.5 rounded-full bg-white mr-1" />
            <Text className="text-white text-[10px] font-black tracking-wider uppercase">
              SON DAKİKA
            </Text>
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} className="flex-1">
            <Text className="text-[#E2E8F0] text-xs font-medium" numberOfLines={1}>
              {breakingNews}
            </Text>
          </ScrollView>
        </View>

        {/* 2. SPOR24 CANLI YAYIN MINI BANNER */}
        <TouchableOpacity
          activeOpacity={0.9}
          onPress={() => navigation.navigate('LiveTvScreen')}
          className="mx-4 mt-3 p-3 rounded-xl bg-gradient-to-r bg-[#161B26] border border-[#E11D48]/30 flex-row items-center justify-between"
        >
          <View className="flex-row items-center space-x-3 flex-1 mr-2">
            <View className="w-10 h-10 rounded-lg bg-[#0B0E14] border border-[#E11D48] items-center justify-center">
              <Text className="text-xs">🔴</Text>
              <Text className="text-[8px] text-[#E11D48] font-bold mt-0.5">CANLI</Text>
            </View>
            <View className="flex-1">
              <View className="flex-row items-center">
                <Text className="text-white text-xs font-bold" numberOfLines={1}>
                  Özel Maç & Federasyon Arşiv Kuşağı
                </Text>
              </View>
              <Text className="text-[10px] text-[#94A3B8]" numberOfLines={1}>
                Spor24 Web TV 1080p Kesintisiz Yayın
              </Text>
            </View>
          </View>
          <View className="bg-[#1E232E] px-2.5 py-1 rounded-full border border-[#2E3646] flex-row items-center">
            <Text className="text-[#FFD700] text-[10px] font-bold mr-1">👁 1.842</Text>
            <Text className="text-[#94A3B8] text-[9px]">İzle ➔</Text>
          </View>
        </TouchableOpacity>

        {/* 3. HERO HEADLINES SLIDER */}
        <View className="mt-4">
          <View className="flex-row items-center justify-between px-4 mb-2">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-sm font-black tracking-wider uppercase">
                Günün Manşetleri
              </Text>
            </View>
            <Text className="text-xs text-[#E11D48] font-semibold">Tümü (12)</Text>
          </View>

          <FlatList
            data={featuredNews}
            keyExtractor={(item) => item.id.toString()}
            horizontal
            showsHorizontalScrollIndicator={false}
            snapToInterval={width - 48}
            decelerationRate="fast"
            contentContainerStyle={{ paddingHorizontal: 16 }}
            renderItem={({ item }) => (
              <TouchableOpacity
                activeOpacity={0.92}
                onPress={() =>
                  navigation.navigate('NewsDetailScreen', { newsId: item.id })
                }
                style={{ width: width - 64 }}
                className="mr-3 rounded-2xl overflow-hidden bg-[#181C24] border border-[#262B36]"
              >
                <View className="relative h-44 w-full">
                  <Image
                    source={{ uri: item.image_url }}
                    className="w-full h-full"
                    resizeMode="cover"
                  />
                  <View className="absolute inset-0 bg-black/40" />

                  {/* FEDERATION BADGE */}
                  <View className="absolute top-3 left-3 bg-[#0B0E14]/85 px-2.5 py-1 rounded-md border border-white/10">
                    <Text className="text-white text-[9px] font-black tracking-wider uppercase">
                      {item.federation}
                    </Text>
                  </View>

                  {/* SPOR24 MÜHÜR */}
                  <View className="absolute top-3 right-3 bg-[#E11D48] px-2 py-0.5 rounded">
                    <Text className="text-white text-[8px] font-black tracking-widest">
                      ÖZEL BÜLTEN
                    </Text>
                  </View>
                </View>

                {/* CONTENT */}
                <View className="p-3.5">
                  <Text
                    className="text-white font-bold text-sm leading-5 mb-1.5"
                    numberOfLines={2}
                  >
                    {item.title}
                  </Text>
                  {item.summary ? (
                    <Text
                      className="text-[#94A3B8] text-xs leading-4 mb-3"
                      numberOfLines={2}
                    >
                      {item.summary}
                    </Text>
                  ) : null}

                  {/* META BAND */}
                  <View className="flex-row items-center justify-between pt-2 border-t border-[#262B36]">
                    <Text className="text-[#94A3B8] text-[10px]">
                      {item.published_at}
                    </Text>
                    <View className="flex-row items-center">
                      <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                      <Text className="text-[#FFD700] text-xs font-bold">
                        {(item.view_count || 0).toLocaleString('tr-TR')}
                      </Text>
                      <Text className="text-[#64748B] text-[10px] ml-1">okunma</Text>
                    </View>
                  </View>
                </View>
              </TouchableOpacity>
            )}
          />
        </View>

        {/* 4. 44 FEDERATION QUICK FILTER CHIPS */}
        <View className="mt-5">
          <View className="flex-row items-center justify-between px-4 mb-2.5">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-sm font-black tracking-wider uppercase">
                44 Federasyon Havuzu
              </Text>
            </View>
            <TouchableOpacity onPress={() => navigation.navigate('FederationsScreen')}>
              <Text className="text-xs text-[#94A3B8]">Tümünü Gör (44) ➔</Text>
            </TouchableOpacity>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16 }}
            className="flex-row"
          >
            {FEDERATION_CATEGORIES.map((chip) => {
              const isActive = selectedFederation === chip.id;
              return (
                <TouchableOpacity
                  key={chip.id}
                  onPress={() => setSelectedFederation(chip.id)}
                  className={`px-3.5 py-1.5 rounded-full mr-2 border flex-row items-center ${
                    isActive
                      ? 'bg-[#E11D48] border-[#E11D48]'
                      : 'bg-[#181C24] border-[#262B36]'
                  }`}
                >
                  <Text
                    className={`text-xs font-bold ${
                      isActive ? 'text-white' : 'text-[#94A3B8]'
                    }`}
                  >
                    {chip.name}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {/* 5. NEWS STREAM CARDS (AKINTI) */}
        <View className="mt-5 px-4 pb-12">
          <View className="flex-row items-center justify-between mb-3">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-sm font-black tracking-wider uppercase">
                Federasyon Medya Akışı
              </Text>
            </View>
            <Text className="text-[10px] text-[#10B981] font-semibold">
              ● Canlı Veri Akışı
            </Text>
          </View>

          {loading && !refreshing ? (
            <ActivityIndicator color="#E11D48" size="large" className="my-8" />
          ) : (
            filteredStream.map((news) => (
              <TouchableOpacity
                key={news.id}
                activeOpacity={0.88}
                onPress={() =>
                  navigation.navigate('NewsDetailScreen', { newsId: news.id })
                }
                className="mb-3.5 p-3 rounded-xl bg-[#141720] border border-[#202530] flex-row items-center"
              >
                {/* THUMBNAIL */}
                <View className="w-24 h-24 rounded-lg overflow-hidden bg-[#1E232E] relative mr-3">
                  <Image
                    source={{ uri: news.image_url }}
                    className="w-full h-full"
                    resizeMode="cover"
                  />
                  {news.is_breaking ? (
                    <View className="absolute top-1 left-1 bg-[#E11D48] px-1.5 py-0.5 rounded">
                      <Text className="text-white text-[7px] font-black uppercase">
                        FLAŞ
                      </Text>
                    </View>
                  ) : null}
                </View>

                {/* DETAILS */}
                <View className="flex-1 justify-between h-24 py-0.5">
                  <View>
                    <Text
                      className="text-[#E11D48] text-[9px] font-bold uppercase tracking-wider mb-0.5"
                      numberOfLines={1}
                    >
                      {news.federation}
                    </Text>
                    <Text
                      className="text-[#F1F5F9] font-bold text-xs leading-4"
                      numberOfLines={2}
                    >
                      {news.title}
                    </Text>
                  </View>

                  {/* FOOTER META & GOLD VIEW COUNT */}
                  <View className="flex-row items-center justify-between pt-1">
                    <Text className="text-[#64748B] text-[10px]">
                      {news.published_at}
                    </Text>
                    <View className="flex-row items-center bg-[#1B1F2A] px-2 py-0.5 rounded border border-[#262B36]">
                      <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                      <Text className="text-[#FFD700] text-[11px] font-bold">
                        {(news.view_count || 0).toLocaleString('tr-TR')}
                      </Text>
                    </View>
                  </View>
                </View>
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default HomeScreen;
