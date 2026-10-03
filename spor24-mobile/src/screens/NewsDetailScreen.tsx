import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  FlatList,
  ActivityIndicator,
  Share,
  Clipboard,
  Dimensions,
  StatusBar,
  SafeAreaView,
  Linking,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');

// ==========================================
// 1. TYPESCRIPT DATA INTERFACES
// ==========================================
export interface NewsDetailItem {
  id: string | number;
  federation: string;
  sub_category?: string;
  title: string;
  lead: string;
  author: {
    name: string;
    role: string;
    avatar?: string;
  };
  published_at: string;
  read_time: string;
  view_count: number;
  likes_count: number;
  comments_count: number;
  hero_image: {
    url: string;
    caption: string;
    source: string;
  };
  body_paragraphs: string[];
  quote?: {
    text: string;
    author: string;
    role: string;
  };
  gallery_images: string[];
  digital_seal: {
    hash_sha256: string;
    registered_at: string;
    protocol_node: string;
    official_source_url: string;
    is_verified: boolean;
  };
  related_news: {
    id: string | number;
    title: string;
    tag: string;
    image_url: string;
    time_ago: string;
    views: number;
  }[];
}

// ==========================================
// 2. FALLBACK / OFFLINE DATA MODEL
// ==========================================
const FALLBACK_DETAIL: NewsDetailItem = {
  id: '59-cumhurbaskanligi-bisiklet-turu',
  federation: 'TÜRKİYE BİSİKLET FEDERASYONU',
  sub_category: '59. CUMHURBAŞKANLIĞI BİSİKLET TURU (TUR 2024)',
  title:
    '59. Cumhurbaşkanlığı Türkiye Bisiklet Turu\'nda Tarihi Start: 25 Ülkeden 170 Dünya Yıldızı Pedal Çeviriyor',
  lead:
    'Antalya-Kemer etabıyla start alan TUR 2024, 1.250 kilometrelik dev parkurda dünyanın en prestijli WorldTour bisiklet takımlarını ve milli sporcularımızı buluşturuyor.',
  author: {
    name: 'Spor24 Özel İstihbarat & Bülten Servisi',
    role: 'Resmi Bülten Masası',
  },
  published_at: '18 Nisan 2025 • 11:45',
  read_time: '4 dk okuma süresi',
  view_count: 2150,
  likes_count: 342,
  comments_count: 24,
  hero_image: {
    url: 'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=1000&q=80',
    caption: 'Kemer Etabı Başlangıç Anı • Peloton Akdeniz Hattında',
    source: 'Spor24 Medya Havuzu / TUR Resmi Arşivi',
  },
  body_paragraphs: [
    'Akdeniz çanağının eşsiz coğrafyasında start alan 59. Cumhurbaşkanlığı Türkiye Bisiklet Turu, bu yıl UCI ProSeries takviminin en kritik virajlarından biri olarak kayda geçiyor. 25 farklı ülkeden gelen 170 seçkin sporcu, Paris 2024 Olimpiyat Oyunları kota puanları öncesindeki son büyük testte Kemer\'in virajlı sahil şeridinde kıyasıya bir mücadeleye girişti.',
    'Yarışın ilk 40 kilometresinde oluşan şiddetli rüzgar esintileri pelotonu iki ana gruba ayırırken taktiksel echelons hamleleri ilk dakikalardan itibaren tansiyonu zirveye taşıdı.',
    'Milli Takım kadrosunda yer alan tecrübeli sprinterlerimiz, ilk tırmanış kapısı öncesinde ana grubu kontrol altında tutmak adına ön saflarda yer aldı. 3. kategori tırmanış finişine 15 kilometre kala lider gruptan kaçan 4 kişilik atak grubu, peloton ile olan farkı 1 dakika 45 saniyeye kadar çıkarırken Kırmızı Mayo mücadelesinde iddialı konuma yükseldi.',
  ],
  quote: {
    text: '“Cumhurbaşkanlığı Türkiye Bisiklet Turu, sadece bir spor müsabakası değil, ülkemizin kıtalararası kültürel ve coğrafi zenginliğinin dünyaya naklen aktarıldığı küresel bir vitrindir.”',
    author: 'Emin Müftüoğlu',
    role: 'Türkiye Bisiklet Federasyonu Başkanı',
  },
  gallery_images: [
    'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1517649763962-0c623266ddc0?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1519766304817-4f37bda74a29?auto=format&fit=crop&w=600&q=80',
    'https://images.unsplash.com/photo-1485965120184-e220f721d03e?auto=format&fit=crop&w=600&q=80',
  ],
  digital_seal: {
    hash_sha256: '8f4e2b901a88c34fbc908127d41a54c99e120f871a2b',
    registered_at: '18.04.2025 - 11:45:12 UTC+3',
    protocol_node: 'TBF-NODE-04 #ANKARA',
    official_source_url: 'https://bisiklet.gov.tr',
    is_verified: true,
  },
  related_news: [
    {
      id: 'rel-1',
      title: 'Konya Olimpik Veledromu\'nda Türkiye Şampiyonası Heyecanı',
      tag: 'VELEDROM',
      image_url:
        'https://images.unsplash.com/photo-1517649763962-0c623266ddc0?auto=format&fit=crop&w=400&q=80',
      time_ago: '3 saat önce',
      views: 1240,
    },
    {
      id: 'rel-2',
      title: 'Kapadokya MTB Cup Hazırlıkları: 12 Ülkeden Milli Sporcular Vadide',
      tag: 'DAĞ BİSİKLETİ (MTB)',
      image_url:
        'https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?auto=format&fit=crop&w=400&q=80',
      time_ago: 'Dün',
      views: 890,
    },
  ],
};

// ==========================================
// 3. MAIN COMPONENT: NewsDetailScreen
// ==========================================
export const NewsDetailScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const newsId = route.params?.newsId || 'default';

  const [news, setNews] = useState<NewsDetailItem>(FALLBACK_DETAIL);
  const [loading, setLoading] = useState<boolean>(false);
  const [fontSizeOffset, setFontSizeOffset] = useState<number>(0);
  const [isBookmarked, setIsBookmarked] = useState<boolean>(false);
  const [isLiked, setIsLiked] = useState<boolean>(false);
  const [likesCount, setLikesCount] = useState<number>(FALLBACK_DETAIL.likes_count);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);

  // Live Backend Fetch
  useEffect(() => {
    const fetchDetail = async () => {
      try {
        setLoading(true);
        const res = await fetch(`https://spor24.net/api/news/${newsId}/`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.title) {
            setNews(data);
            setLikesCount(data.likes_count || FALLBACK_DETAIL.likes_count);
          }
        }
      } catch (err) {
        console.warn('Haber detay servisi yanıt vermedi, yedek veri yüklendi:', err);
      } finally {
        setLoading(false);
      }
    };

    if (newsId && newsId !== 'default') {
      fetchDetail();
    }
  }, [newsId]);

  // Actions
  const handleShare = async () => {
    try {
      await Share.share({
        message: `${news.title} - SPOR24 Resmi Medya Havuzu: https://spor24.net/haber/${news.id}`,
        title: news.title,
      });
    } catch (e) {
      console.error(e);
    }
  };

  const handleCopyHash = () => {
    Clipboard.setString(news.digital_seal.hash_sha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2500);
  };

  const toggleLike = () => {
    if (isLiked) {
      setLikesCount((prev) => prev - 1);
      setIsLiked(false);
    } else {
      setLikesCount((prev) => prev + 1);
      setIsLiked(true);
    }
  };

  const handleOpenSource = () => {
    if (news.digital_seal?.official_source_url) {
      Linking.openURL(news.digital_seal.official_source_url);
    }
  };

  if (loading) {
    return (
      <View className="flex-1 bg-[#0B0E14] items-center justify-center">
        <ActivityIndicator color="#E11D48" size="large" />
        <Text className="text-[#94A3B8] text-xs font-semibold mt-3">
          Haber ve Mühür Doğrulanıyor...
        </Text>
      </View>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-[#0B0E14]">
      <StatusBar barStyle="light-content" backgroundColor="#0B0E14" />

      {/* 1. TOP APP BAR (HEADER) */}
      <View className="flex-row items-center justify-between px-4 py-3 bg-[#10131A] border-b border-[#1E232E]">
        <TouchableOpacity
          onPress={() => navigation.goBack()}
          className="w-9 h-9 rounded-full bg-[#181C24] items-center justify-center border border-[#262B36]"
        >
          <Text className="text-white text-base font-bold">←</Text>
        </TouchableOpacity>

        {/* SPOR24 BÜLTEN MÜHRÜ */}
        <View className="flex-row items-center bg-[#1B1F2A] px-3 py-1 rounded-full border border-[#E11D48]/40">
          <View className="w-2 h-2 rounded-full bg-[#E11D48] mr-2 animate-pulse" />
          <Text className="text-white text-[10px] font-black tracking-widest uppercase">
            SPOR24 BÜLTEN
          </Text>
        </View>

        <View className="flex-row items-center space-x-2">
          <TouchableOpacity
            onPress={() => setIsBookmarked(!isBookmarked)}
            className={`w-9 h-9 rounded-full items-center justify-center border ${
              isBookmarked
                ? 'bg-[#E11D48] border-[#E11D48]'
                : 'bg-[#181C24] border-[#262B36]'
            }`}
          >
            <Text className="text-xs">{isBookmarked ? '★' : '☆'}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={handleShare}
            className="w-9 h-9 rounded-full bg-[#181C24] items-center justify-center border border-[#262B36]"
          >
            <Text className="text-xs">↗</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* MAIN ARTICLE BODY SCROLL */}
      <ScrollView showsVerticalScrollIndicator={false} className="flex-1">
        {/* FEDERATION & CATEGORY PILLS */}
        <View className="px-4 pt-4">
          <View className="self-start flex-row items-center bg-[#181C24] px-2.5 py-1 rounded-md border border-[#262B36] mb-2">
            <Text className="text-[#10B981] text-[10px] mr-1.5">✓</Text>
            <Text className="text-[#E2E8F0] text-[10px] font-black uppercase tracking-wider">
              {news.federation}
            </Text>
          </View>

          {news.sub_category ? (
            <Text className="text-[#94A3B8] text-[10px] font-bold tracking-widest uppercase mb-2">
              {news.sub_category}
            </Text>
          ) : null}

          {/* MAIN ARTICLE TITLE */}
          <Text className="text-white font-black text-xl leading-7 tracking-tight mb-3">
            {news.title}
          </Text>

          {/* LEAD / SPOT SUMMARY */}
          <Text
            style={{ fontSize: 14 + fontSizeOffset, lineHeight: 22 + fontSizeOffset }}
            className="text-[#CBD5E1] font-semibold mb-4 border-l-2 border-[#E11D48] pl-3"
          >
            {news.lead}
          </Text>

          {/* REPORTER / BYLINE & STATS BAR */}
          <View className="p-3 rounded-xl bg-[#141720] border border-[#202530] mb-4">
            <View className="flex-row items-center justify-between mb-2">
              <View className="flex-row items-center flex-1 mr-2">
                <View className="w-8 h-8 rounded-full bg-[#E11D48]/20 border border-[#E11D48] items-center justify-center mr-2.5">
                  <Text className="text-[#E11D48] text-xs font-black">S24</Text>
                </View>
                <View className="flex-1">
                  <Text className="text-white text-xs font-bold" numberOfLines={1}>
                    {news.author.name}
                  </Text>
                  <Text className="text-[#64748B] text-[10px]">{news.published_at}</Text>
                </View>
              </View>
              <View className="bg-[#E11D48] px-2 py-0.5 rounded">
                <Text className="text-white text-[8px] font-black uppercase tracking-wider">
                  ÖZEL HABER
                </Text>
              </View>
            </View>

            <View className="flex-row items-center justify-between pt-2 border-t border-[#1E232E]">
              <View className="flex-row items-center">
                <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                <Text className="text-[#FFD700] text-xs font-bold mr-1">
                  {(news.view_count || 0).toLocaleString('tr-TR')}
                </Text>
                <Text className="text-[#64748B] text-[10px]">Okunma</Text>
              </View>
              <Text className="text-[#94A3B8] text-[10px]">⏱ {news.read_time}</Text>
            </View>
          </View>
        </View>

        {/* 2. HERO IMAGE WITH HUD OVERLAY */}
        <View className="relative mx-4 mb-4 rounded-2xl overflow-hidden border border-[#262B36]">
          <Image
            source={{ uri: news.hero_image.url }}
            style={{ width: width - 32, height: ((width - 32) * 9) / 16 }}
            resizeMode="cover"
          />
          <View className="absolute top-2.5 left-2.5 bg-[#0B0E14]/85 px-2 py-0.5 rounded border border-white/10 flex-row items-center">
            <View className="w-1.5 h-1.5 rounded-full bg-[#E11D48] mr-1.5" />
            <Text className="text-white text-[9px] font-bold tracking-wider">
              CANLI AKTARIM
            </Text>
          </View>
          <View className="p-2.5 bg-[#10131A] border-t border-[#1E232E]">
            <Text className="text-[#94A3B8] text-[10px] font-medium" numberOfLines={1}>
              Fotoğraf: {news.hero_image.source} • {news.hero_image.caption}
            </Text>
          </View>
        </View>

        {/* 3. EDITORIAL ARTICLE PARAGRAPHS */}
        <View className="px-4 mb-5">
          {news.body_paragraphs.map((paragraph, index) => (
            <Text
              key={index}
              style={{ fontSize: 13 + fontSizeOffset, lineHeight: 22 + fontSizeOffset }}
              className="text-[#94A3B8] mb-3.5 font-normal tracking-wide"
            >
              {paragraph}
            </Text>
          ))}
        </View>

        {/* 4. FEDERATION PRESIDENT BLOCKQUOTE */}
        {news.quote ? (
          <View className="mx-4 mb-6 p-4 rounded-xl bg-[#161B26] border-l-4 border-[#E11D48] border border-[#262B36]">
            <Text className="text-[#E11D48] text-2xl font-black mb-1">“</Text>
            <Text
              style={{ fontSize: 13 + fontSizeOffset, lineHeight: 20 + fontSizeOffset }}
              className="text-[#E2E8F0] font-semibold italic mb-3 -mt-2"
            >
              {news.quote.text.replace(/“|”/g, '')}
            </Text>
            <View className="flex-row items-center pt-2 border-t border-[#262B36]/60">
              <View className="w-1.5 h-1.5 rounded-full bg-[#E11D48] mr-2" />
              <View>
                <Text className="text-white text-xs font-bold">{news.quote.author}</Text>
                <Text className="text-[#94A3B8] text-[10px]">{news.quote.role}</Text>
              </View>
            </View>
          </View>
        ) : null}

        {/* 5. 5-PHOTO HORIZONTAL GALLERY */}
        <View className="mb-6">
          <View className="flex-row items-center justify-between px-4 mb-2.5">
            <View className="flex-row items-center">
              <Text className="text-sm mr-1.5">📷</Text>
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                Haber Foto Galeri
              </Text>
            </View>
            <View className="bg-[#181C24] px-2 py-0.5 rounded border border-[#262B36]">
              <Text className="text-[#94A3B8] text-[9px] font-bold">5 Kare</Text>
            </View>
          </View>

          <FlatList
            data={news.gallery_images}
            horizontal
            showsHorizontalScrollIndicator={false}
            keyExtractor={(_, index) => index.toString()}
            contentContainerStyle={{ paddingHorizontal: 16 }}
            renderItem={({ item, index }) => (
              <View className="w-64 h-36 rounded-xl overflow-hidden mr-3 bg-[#181C24] border border-[#262B36] relative">
                <Image source={{ uri: item }} className="w-full h-full" resizeMode="cover" />
                <View className="absolute bottom-2 right-2 bg-black/75 px-1.5 py-0.5 rounded">
                  <Text className="text-white text-[8px] font-bold">{index + 1}/5</Text>
                </View>
              </View>
            )}
          />
        </View>

        {/* 6. SHA-256 DİJİTAL MÜHÜR & CONTENT ID TESCİL KARTI */}
        <View className="mx-4 mb-6 p-4 rounded-2xl bg-[#0D111A] border border-[#1E293B] shadow-2xl">
          <View className="flex-row items-center justify-between pb-3 border-b border-[#1E293B]">
            <View className="flex-row items-center">
              <View className="w-8 h-8 rounded-lg bg-[#10B981]/15 border border-[#10B981] items-center justify-center mr-2.5">
                <Text className="text-[#10B981] text-sm font-black">🛡</Text>
              </View>
              <View>
                <Text className="text-white text-xs font-black tracking-wider uppercase">
                  DİJİTAL MÜHÜR & CONTENT ID
                </Text>
                <Text className="text-[#10B981] text-[9px] font-bold tracking-wide">
                  RESMİ TELİF VE VERİ TESCİL BELGESİ
                </Text>
              </View>
            </View>
            <View className="w-6 h-6 rounded-full bg-[#181C24] items-center justify-center border border-[#334155]">
              <Text className="text-[10px]">🔒</Text>
            </View>
          </View>

          {/* CRYPTO HASH BOX */}
          <View className="mt-3 p-2.5 rounded-lg bg-[#07090E] border border-[#202530] flex-row items-center justify-between">
            <View className="flex-1 mr-2">
              <Text className="text-[#64748B] text-[8px] font-black uppercase tracking-wider mb-0.5">
                SHA-256 HASH
              </Text>
              <Text className="text-[#38BDF8] font-mono text-[10px]" numberOfLines={1}>
                {news.digital_seal.hash_sha256}
              </Text>
            </View>
            <TouchableOpacity
              onPress={handleCopyHash}
              className={`px-2.5 py-1.5 rounded-md border ${
                copiedHash
                  ? 'bg-[#10B981] border-[#10B981]'
                  : 'bg-[#181C24] border-[#334155]'
              }`}
            >
              <Text className="text-white text-[9px] font-bold">
                {copiedHash ? '✓ Kopyalandı' : 'Kopyala'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* LEGAL TEXT */}
          <Text className="text-[#64748B] text-[10px] leading-4 mt-2.5 mb-3 font-normal">
            Bu haber metni, istatistiki veriler ve görsel içerikler{' '}
            <Text className="text-[#CBD5E1] font-bold">
              SPOR24 Bağımsız Ajans Çekirdeği
            </Text>{' '}
            tarafından kriptografik olarak tescillenmiş olup, 44 Resmi Federasyon Dijital
            Protokolü ve Fikir ve Sanat Eserleri Kanunu kapsamında tam koruma altındadır.
          </Text>

          {/* PROTOCOL METRICS */}
          <View className="pt-2.5 border-t border-[#1E293B] space-y-1.5">
            <View className="flex-row justify-between">
              <Text className="text-[#64748B] text-[10px]">Tescil Zamanı:</Text>
              <Text className="text-[#94A3B8] text-[10px] font-mono">
                {news.digital_seal.registered_at}
              </Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-[#64748B] text-[10px]">Protokol Düğümü:</Text>
              <Text className="text-[#E11D48] text-[10px] font-mono font-bold">
                {news.digital_seal.protocol_node}
              </Text>
            </View>
          </View>

          {/* OFFICIAL SOURCE ACTION BUTTON */}
          <TouchableOpacity
            activeOpacity={0.88}
            onPress={handleOpenSource}
            className="mt-3.5 py-2.5 px-4 rounded-xl bg-[#161B26] border border-[#2E3646] flex-row items-center justify-center"
          >
            <Text className="text-white text-xs font-bold mr-1.5">
              Resmi Federasyon Kaynağına Git
            </Text>
            <Text className="text-[#38BDF8] text-xs">↗</Text>
          </TouchableOpacity>
        </View>

        {/* 7. RELATED FEDERATION NEWS */}
        <View className="px-4 mb-24">
          <View className="flex-row items-center justify-between mb-3">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                {news.federation}
              </Text>
            </View>
            <Text className="text-[#94A3B8] text-xs">Tümünü Gör (18) ➔</Text>
          </View>

          {news.related_news.map((item) => (
            <TouchableOpacity
              key={item.id}
              activeOpacity={0.88}
              onPress={() => navigation.push('NewsDetailScreen', { newsId: item.id })}
              className="p-3 mb-2.5 rounded-xl bg-[#141720] border border-[#202530] flex-row items-center"
            >
              <Image
                source={{ uri: item.image_url }}
                className="w-20 h-20 rounded-lg mr-3 bg-[#1E232E]"
                resizeMode="cover"
              />
              <View className="flex-1 justify-between h-20 py-0.5">
                <View>
                  <Text className="text-[#E11D48] text-[9px] font-bold uppercase tracking-wider mb-0.5">
                    {item.tag}
                  </Text>
                  <Text className="text-[#F1F5F9] font-bold text-xs leading-4" numberOfLines={2}>
                    {item.title}
                  </Text>
                </View>
                <View className="flex-row items-center justify-between">
                  <Text className="text-[#64748B] text-[10px]">{item.time_ago}</Text>
                  <View className="flex-row items-center">
                    <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                    <Text className="text-[#FFD700] text-[10px] font-bold">
                      {(item.views || 0).toLocaleString('tr-TR')}
                    </Text>
                  </View>
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      {/* 8. BOTTOM FIXED INTERACTION DOCK */}
      <View className="absolute bottom-0 left-0 right-0 bg-[#10131A] border-t border-[#1E232E] px-4 py-3 flex-row items-center justify-between">
        {/* FONT SIZE SCALER (A- / A+) */}
        <View className="flex-row items-center bg-[#181C24] rounded-lg border border-[#262B36] p-0.5">
          <TouchableOpacity
            onPress={() => setFontSizeOffset((prev) => Math.max(prev - 1, -2))}
            className="px-2 py-1"
          >
            <Text className="text-[#94A3B8] text-xs font-bold">A-</Text>
          </TouchableOpacity>
          <View className="w-[1px] h-3 bg-[#262B36]" />
          <TouchableOpacity
            onPress={() => setFontSizeOffset((prev) => Math.min(prev + 1, 4))}
            className="px-2 py-1"
          >
            <Text className="text-white text-xs font-bold">A+</Text>
          </TouchableOpacity>
        </View>

        {/* LIKE BUTTON */}
        <TouchableOpacity
          onPress={toggleLike}
          className={`flex-row items-center px-3 py-1.5 rounded-lg border ${
            isLiked
              ? 'bg-[#E11D48]/20 border-[#E11D48]'
              : 'bg-[#181C24] border-[#262B36]'
          }`}
        >
          <Text className="mr-1 text-xs">{isLiked ? '❤️' : '🤍'}</Text>
          <Text className={`text-xs font-bold ${isLiked ? 'text-[#E11D48]' : 'text-white'}`}>
            {likesCount}
          </Text>
        </TouchableOpacity>

        {/* COMMENT BUTTON */}
        <TouchableOpacity className="flex-row items-center bg-[#181C24] px-3 py-1.5 rounded-lg border border-[#262B36]">
          <Text className="mr-1 text-xs">💬</Text>
          <Text className="text-white text-xs font-bold">{news.comments_count}</Text>
        </TouchableOpacity>

        {/* CTA PAYLAŞ BUTTON */}
        <TouchableOpacity
          activeOpacity={0.88}
          onPress={handleShare}
          className="flex-row items-center bg-[#E11D48] px-4 py-2 rounded-xl shadow-lg shadow-[#E11D48]/30"
        >
          <Text className="text-white text-xs font-black mr-1 tracking-wider uppercase">
            PAYLAŞ
          </Text>
          <Text className="text-white text-xs font-bold">↗</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

export default NewsDetailScreen;
