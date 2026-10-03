import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  TextInput,
  ActivityIndicator,
  RefreshControl,
  Share,
  Dimensions,
  StatusBar,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');

// ==========================================
// 1. TYPESCRIPT DATA INTERFACES
// ==========================================
export interface Author {
  id: string;
  name: string;
  role: string;
  avatar_url: string;
  has_new_article?: boolean;
  total_articles: number;
  is_following?: boolean;
}

export interface ColumnArticle {
  id: string;
  title: string;
  summary: string;
  author: Author;
  category: string;
  read_time: string;
  view_count: number;
  published_at: string;
  is_featured?: boolean;
  is_sealed?: boolean;
  seal_node?: string;
}

// ==========================================
// 2. FALLBACK / OFFLINE MOCK DATA
// ==========================================
const FALLBACK_AUTHORS: Author[] = [
  {
    id: 'kenan-demirel',
    name: 'Kenan Demirel',
    role: 'Genel Yayın Yönetmeni & Kıdemli Analist',
    avatar_url:
      'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
    has_new_article: true,
    total_articles: 148,
    is_following: true,
  },
  {
    id: 'dr-hakan-yildiz',
    name: 'Dr. Hakan Yıldız',
    role: 'Olimpik Dallar & Performans Bilimi',
    avatar_url:
      'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
    has_new_article: true,
    total_articles: 62,
    is_following: false,
  },
  {
    id: 'selin-kurtay',
    name: 'Selin Kurtay',
    role: 'Dövüş Sporları & Minder Kulisleri',
    avatar_url:
      'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=300&q=80',
    has_new_article: false,
    total_articles: 84,
    is_following: false,
  },
  {
    id: 'murat-erenler',
    name: 'Murat Erenler',
    role: 'Bisiklet & Dayanıklılık Sporları',
    avatar_url:
      'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
    has_new_article: true,
    total_articles: 53,
    is_following: false,
  },
  {
    id: 'ayse-deniz',
    name: 'Ayşe Deniz',
    role: 'Spor Hukuku & Federasyon Mevzuatı',
    avatar_url:
      'https://images.unsplash.com/photo-1580489944761-15a19d654956?auto=format&fit=crop&w=300&q=80',
    has_new_article: false,
    total_articles: 39,
    is_following: false,
  },
];

const FALLBACK_FEATURED: ColumnArticle = {
  id: 'kenan-paris-donemi',
  title: '44 Federasyonun Geleceği: Paris Sonrası Türk Sporunda Yeni Dönem',
  summary:
    'Olimpiyat kotası ve altyapı seferberliğinde branşların karşılaştığı finansal ve idari darboğazlar nasıl aşılır? Spor24 Analiz Masası masaya yatırıyor.',
  author: FALLBACK_AUTHORS[0],
  category: 'OLİMPİK VİZYON & STRATEJİ',
  read_time: '4 dk',
  view_count: 4850,
  published_at: 'Bugün • 09:30',
  is_featured: true,
  is_sealed: true,
  seal_node: 'SPOR24-ED-NODE-01',
};

const FALLBACK_ARTICLES: ColumnArticle[] = [
  {
    id: 'art-1',
    title: 'Minderde Taktik Reformu: Ağır Sıklette Altın Madalyanın Şifreleri',
    summary:
      'Grekoromen ve serbest güreşte değişen ceza puanlama kurallarının sporcularımızın kondisyon dağılımına etkileri.',
    author: FALLBACK_AUTHORS[2], // Selin Kurtay
    category: 'MİNDER & GÜREŞ',
    read_time: '5 dk',
    view_count: 3120,
    published_at: '3 saat önce',
  },
  {
    id: 'art-2',
    title: '59. Cumhurbaşkanlığı Turu Bize Ne Söyledi? Rüzgar ve Echelon Savaşları',
    summary:
      'WorldTour seviyesinde takımların Akdeniz etabındaki taktik hamleleri ve Türk bisikletinin küresel vitrindeki sıçrayışı.',
    author: FALLBACK_AUTHORS[3], // Murat Erenler
    category: 'BİSİKLET & TUR',
    read_time: '6 dk',
    view_count: 2450,
    published_at: 'Dün',
  },
  {
    id: 'art-3',
    title: 'Boks Milli Takımında Yeni Nesil Kondisyoner Yaklaşımı',
    summary:
      'Kastamonu kampında uygulanan biyomekanik testler ve Olimpiyat öncesi nabız optimizasyonu üzerine saha gözlemleri.',
    author: FALLBACK_AUTHORS[1], // Dr. Hakan Yıldız
    category: 'BOKS & DÖVÜŞ',
    read_time: '3 dk',
    view_count: 1890,
    published_at: '2 gün önce',
  },
  {
    id: 'art-4',
    title: 'Özerk Federasyonlarda Bütçe ve Denetim Reformu',
    summary:
      'Spor Kulüpleri ve Federasyonları Kanunu ile gelen yeni mali kriterlerin branşlara getirdiği sorumluluklar.',
    author: FALLBACK_AUTHORS[4], // Ayşe Deniz
    category: 'SPOR HUKUKU',
    read_time: '7 dk',
    view_count: 1640,
    published_at: '3 gün önce',
  },
];

const CATEGORY_FILTERS = [
  { id: 'all', label: 'Tümü' },
  { id: 'combat', label: 'Boks & Dövüş' },
  { id: 'wrestling', label: 'Minder & Güreş' },
  { id: 'olympic', label: 'Olimpik Dallar' },
  { id: 'cycling', label: 'Bisiklet & Yol' },
  { id: 'law', label: 'Spor Hukuku' },
];

// ==========================================
// 3. MAIN COMPONENT: ColumnistsScreen
// ==========================================
export const ColumnistsScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  // State Management
  const [authors, setAuthors] = useState<Author[]>(FALLBACK_AUTHORS);
  const [featuredArticle, setFeaturedArticle] = useState<ColumnArticle>(FALLBACK_FEATURED);
  const [articles, setArticles] = useState<ColumnArticle[]>(FALLBACK_ARTICLES);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [newsletterEmail, setNewsletterEmail] = useState<string>('');
  const [isSubscribed, setIsSubscribed] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Dynamic Backend Fetch: https://spor24.net/api/columnists/
  const fetchColumnistsData = async () => {
    try {
      setLoading(true);
      const res = await fetch('https://spor24.net/api/columnists/');
      if (res.ok) {
        const data = await res.json();
        if (data.authors) setAuthors(data.authors);
        if (data.featured) setFeaturedArticle(data.featured);
        if (data.articles) setArticles(data.articles);
      }
    } catch (error) {
      console.warn('Yazarlar API servisi bağlantısı kurulamadı, yedek veri yüklendi:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchColumnistsData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchColumnistsData();
  };

  // Follow / Unfollow Author Action
  const toggleFollowAuthor = (authorId: string) => {
    setAuthors((prev) =>
      prev.map((a) =>
        a.id === authorId ? { ...a, is_following: !a.is_following } : a
      )
    );
  };

  // Filter Articles
  const filteredArticles = useMemo(() => {
    return articles.filter((art) => {
      const matchesSearch =
        art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        art.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
        art.author.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        art.category.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory =
        selectedCategory === 'all'
          ? true
          : art.category.toLowerCase().includes(selectedCategory.toLowerCase());
      return matchesSearch && matchesCategory;
    });
  }, [articles, searchQuery, selectedCategory]);

  // Newsletter Submit
  const handleNewsletterSubmit = () => {
    if (!newsletterEmail || !newsletterEmail.includes('@')) {
      Alert.alert('Hata', 'Lütfen geçerli bir e-posta adresi giriniz.');
      return;
    }
    setIsSubscribed(true);
    setNewsletterEmail('');
    Alert.alert(
      'Kaydınız Alındı',
      'Spor24 Özel Kulis ve Editoryal Analiz bültenimize başarıyla abone oldunuz.'
    );
  };

  // Share Article
  const handleShareArticle = async (article: ColumnArticle) => {
    try {
      await Share.share({
        message: `🖋 ${article.author.name}: "${article.title}" - SPOR24 Editoryal Analiz Masası: https://spor24.net/yazarlar/${article.id}`,
        title: article.title,
      });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <SafeAreaView className="flex-1 bg-[#0B0E14]">
      <StatusBar barStyle="light-content" backgroundColor="#0B0E14" />

      {/* 1. ÜST APP BAR & EDITORYAL MÜHÜR */}
      <View className="bg-[#10131A] border-b border-[#1E232E] px-4 pt-3 pb-3">
        <View className="flex-row items-center justify-between">
          <View className="flex-row items-center">
            <View className="w-8 h-8 rounded-lg bg-[#E11D48]/20 border border-[#E11D48] items-center justify-center mr-2.5">
              <Text className="text-[#E11D48] text-base">🖋</Text>
            </View>
            <View>
              <Text className="text-white font-black text-base tracking-wide">
                Köşe Yazarları & Analiz
              </Text>
              <Text className="text-[#94A3B8] text-[9px] font-medium tracking-wider">
                Bağımsız Yorumcular & 44 Federasyon Özel Analizleri
              </Text>
            </View>
          </View>
          <View className="bg-[#181C24] px-2.5 py-1 rounded-full border border-[#262B36] flex-row items-center">
            <View className="w-1.5 h-1.5 rounded-full bg-[#10B981] mr-1.5" />
            <Text className="text-white text-[9px] font-bold">EDİTORYAL</Text>
          </View>
        </View>

        {/* AKILLI ARAMA ÇUBUĞU */}
        <View className="flex-row items-center bg-[#141822] px-3.5 py-2 rounded-xl border border-[#202532] mt-3">
          <Text className="text-xs mr-2 text-[#64748B]">🔍</Text>
          <TextInput
            placeholder="Yazar, makale başlığı veya branş ara..."
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

        {/* BRANŞ VE KATEGORİ ÇİPLERİ */}
        <View className="mt-2.5">
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingRight: 8 }}
            className="flex-row"
          >
            {CATEGORY_FILTERS.map((chip) => {
              const isSelected = selectedCategory === chip.id;
              return (
                <TouchableOpacity
                  key={chip.id}
                  onPress={() => setSelectedCategory(chip.id)}
                  className={`px-3 py-1 rounded-full mr-2 border ${
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
        {/* 2. YAZARLARIMIZ YATAY ŞERİDİ (AUTHORS CAROUSEL) */}
        <View className="mt-4">
          <View className="flex-row items-center justify-between px-4 mb-2.5">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                Yazarlarımız
              </Text>
            </View>
            <Text className="text-[#94A3B8] text-[10px] font-medium">Kadro (14)</Text>
          </View>

          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingHorizontal: 16 }}
            className="flex-row"
          >
            {authors.map((author) => (
              <TouchableOpacity
                key={author.id}
                activeOpacity={0.85}
                onPress={() => setSearchQuery(author.name)}
                className="items-center mr-4 w-18"
              >
                {/* AVATAR WITH ACTIVE DOT */}
                <View className="relative mb-1.5">
                  <Image
                    source={{ uri: author.avatar_url }}
                    className="w-14 h-14 rounded-full border-2 border-[#E11D48]"
                  />
                  {author.has_new_article && (
                    <View className="absolute top-0 right-0 w-3 h-3 rounded-full bg-[#E11D48] border-2 border-[#0B0E14] shadow-md shadow-[#E11D48]/50" />
                  )}
                </View>
                {/* NAME & ROLE */}
                <Text
                  className="text-white text-[11px] font-bold text-center tracking-tight"
                  numberOfLines={1}
                >
                  {author.name}
                </Text>
                <Text
                  className="text-[#64748B] text-[9px] text-center"
                  numberOfLines={1}
                >
                  {author.role.split('&')[0]}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        {/* 3. GÜNÜN MANŞET BAŞYAZISI (FEATURED ARTICLE CARD) */}
        <View className="mt-5 px-4">
          <View className="flex-row items-center justify-between mb-2">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                Günün Manşet Başyazısı
              </Text>
            </View>
            <View className="bg-[#181C24] px-2 py-0.5 rounded border border-[#262B36]">
              <Text className="text-[#FFD700] text-[9px] font-black uppercase">
                ÖZEL VİTRİN
              </Text>
            </View>
          </View>

          <TouchableOpacity
            activeOpacity={0.92}
            onPress={() =>
              navigation.navigate('NewsDetailScreen', {
                newsId: featuredArticle.id,
              })
            }
            className="p-4 rounded-2xl bg-[#131722] border border-[#222838] shadow-2xl relative overflow-hidden"
          >
            {/* BACKGROUND ACCENT GLOW */}
            <View className="absolute -top-10 -right-10 w-32 h-32 rounded-full bg-[#E11D48]/10 blur-2xl" />

            {/* AUTHOR BYLINE ROW */}
            <View className="flex-row items-center justify-between mb-3">
              <View className="flex-row items-center flex-1 mr-2">
                <Image
                  source={{ uri: featuredArticle.author.avatar_url }}
                  className="w-11 h-11 rounded-full border border-[#E11D48] mr-2.5"
                />
                <View className="flex-1">
                  <Text className="text-white text-xs font-bold" numberOfLines={1}>
                    {featuredArticle.author.name}
                  </Text>
                  <Text className="text-[#94A3B8] text-[10px]" numberOfLines={1}>
                    {featuredArticle.author.role}
                  </Text>
                </View>
              </View>

              {/* MÜHÜRLÜ ANALİZ ROZETİ */}
              <View className="bg-[#10B981]/15 px-2 py-0.5 rounded-full border border-[#10B981]/40 flex-row items-center">
                <Text className="text-[#10B981] text-[8px] mr-1">🛡</Text>
                <Text className="text-[#10B981] text-[8px] font-black uppercase tracking-wider">
                  MÜHÜRLÜ ANALİZ
                </Text>
              </View>
            </View>

            {/* CATEGORY TAG */}
            <Text className="text-[#E11D48] text-[9px] font-black tracking-widest uppercase mb-1">
              {featuredArticle.category}
            </Text>

            {/* TITLE & SUMMARY */}
            <Text className="text-white font-black text-base leading-6 mb-2">
              {featuredArticle.title}
            </Text>
            <Text className="text-[#94A3B8] text-xs leading-5 mb-4">
              {featuredArticle.summary}
            </Text>

            {/* FOOTER METRICS & ACTIONS */}
            <View className="flex-row items-center justify-between pt-3 border-t border-[#1E2434]">
              <View className="flex-row items-center space-x-3">
                <View className="flex-row items-center">
                  <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                  <Text className="text-[#FFD700] text-xs font-bold mr-1">
                    {(featuredArticle.view_count || 0).toLocaleString('tr-TR')}
                  </Text>
                  <Text className="text-[#64748B] text-[10px]">Okunma</Text>
                </View>
                <Text className="text-[#64748B] text-[10px]">
                  ⏱ {featuredArticle.read_time}
                </Text>
              </View>
              <TouchableOpacity
                onPress={() => handleShareArticle(featuredArticle)}
                className="w-7 h-7 rounded-full bg-[#181C26] items-center justify-center border border-[#2B3346]"
              >
                <Text className="text-[#CBD5E1] text-[10px]">↗</Text>
              </TouchableOpacity>
            </View>
          </TouchableOpacity>
        </View>

        {/* 4. SON EDİTORYAL ANALİZLER AKIŞI (ARTICLES LIST) */}
        <View className="mt-6 px-4">
          <View className="flex-row items-center justify-between mb-3">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                Son Editoryal Analizler
              </Text>
            </View>
            <Text className="text-[#64748B] text-[10px] font-mono">
              {filteredArticles.length} Makale
            </Text>
          </View>

          {loading && !refreshing ? (
            <ActivityIndicator color="#E11D48" size="large" className="my-8" />
          ) : (
            filteredArticles.map((article) => {
              const isFollowing = article.author.is_following;
              return (
                <View
                  key={article.id}
                  className="mb-3.5 p-3.5 rounded-2xl bg-[#121620] border border-[#1E2432] shadow-xl"
                >
                  {/* AUTHOR ROW & FOLLOW BUTTON */}
                  <View className="flex-row items-center justify-between mb-2.5">
                    <View className="flex-row items-center flex-1 mr-2">
                      <Image
                        source={{ uri: article.author.avatar_url }}
                        className="w-9 h-9 rounded-full border border-white/10 mr-2.5"
                      />
                      <View className="flex-1">
                        <Text className="text-white text-xs font-bold" numberOfLines={1}>
                          {article.author.name}
                        </Text>
                        <Text className="text-[#64748B] text-[9px]" numberOfLines={1}>
                          {article.author.role}
                        </Text>
                      </View>
                    </View>

                    {/* FOLLOW BUTTON */}
                    <TouchableOpacity
                      onPress={() => toggleFollowAuthor(article.author.id)}
                      className={`px-2.5 py-1 rounded-full border ${
                        isFollowing
                          ? 'bg-[#181C26] border-[#2E3646]'
                          : 'bg-[#E11D48]/15 border-[#E11D48]'
                      }`}
                    >
                      <Text
                        className={`text-[9px] font-bold ${
                          isFollowing ? 'text-[#94A3B8]' : 'text-[#E11D48]'
                        }`}
                      >
                        {isFollowing ? '✓ Takipte' : '+ Takip Et 🔔'}
                      </Text>
                    </TouchableOpacity>
                  </View>

                  {/* ARTICLE CONTENT */}
                  <TouchableOpacity
                    activeOpacity={0.88}
                    onPress={() =>
                      navigation.navigate('NewsDetailScreen', {
                        newsId: article.id,
                      })
                    }
                  >
                    <View className="flex-row items-center justify-between mb-1">
                      <Text className="text-[#E11D48] text-[9px] font-black uppercase tracking-wider">
                        {article.category}
                      </Text>
                      <Text className="text-[#64748B] text-[9px]">
                        {article.published_at}
                      </Text>
                    </View>
                    <Text className="text-white font-bold text-sm leading-5 mb-1.5">
                      {article.title}
                    </Text>
                    <Text
                      className="text-[#94A3B8] text-xs leading-4 mb-3"
                      numberOfLines={2}
                    >
                      {article.summary}
                    </Text>
                  </TouchableOpacity>

                  {/* FOOTER METRICS & SHARE */}
                  <View className="flex-row items-center justify-between pt-2 border-t border-[#1C212D]">
                    <View className="flex-row items-center">
                      <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
                      <Text className="text-[#FFD700] text-xs font-bold mr-1">
                        {(article.view_count || 0).toLocaleString('tr-TR')}
                      </Text>
                      <Text className="text-[#64748B] text-[9px]">Okunma</Text>
                    </View>
                    <View className="flex-row items-center space-x-2">
                      <Text className="text-[#94A3B8] text-[10px]">
                        ⏱ {article.read_time}
                      </Text>
                      <TouchableOpacity
                        onPress={() => handleShareArticle(article)}
                        className="w-6 h-6 rounded-full bg-[#181C26] items-center justify-center border border-[#252C3A]"
                      >
                        <Text className="text-[#94A3B8] text-[10px]">↗</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                </View>
              );
            })
          )}
        </View>

        {/* 5. EDİTORYAL E-BÜLTEN KUTUSU (NEWSLETTER SUBSCRIPTION) */}
        <View className="mx-4 my-4 p-4 rounded-2xl bg-[#151924] border border-[#242C3D] relative overflow-hidden">
          <View className="flex-row items-center mb-1.5">
            <View className="w-2 h-2 rounded-full bg-[#E11D48] mr-2" />
            <Text className="text-white text-xs font-black tracking-wider uppercase">
              Spor24 Kulis Bülteni
            </Text>
          </View>
          <Text className="text-[#94A3B8] text-xs leading-4 mb-3">
            44 resmi federasyondan günlük kulis analizleri, perde arkası gelişmeler ve
            bağımsız köşe yazıları her sabah e-postanızda.
          </Text>
          <View className="flex-row items-center bg-[#0B0E14] rounded-xl p-1 border border-[#222836]">
            <TextInput
              placeholder="E-posta adresiniz..."
              placeholderTextColor="#64748B"
              value={newsletterEmail}
              onChangeText={setNewsletterEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              className="flex-1 text-white text-xs px-3 py-1.5 font-medium"
            />
            <TouchableOpacity
              activeOpacity={0.88}
              onPress={handleNewsletterSubmit}
              className="bg-[#E11D48] px-3.5 py-2 rounded-lg"
            >
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                KAYIT OL
              </Text>
            </TouchableOpacity>
          </View>
          <Text className="text-[#475569] text-[9px] mt-1.5 ml-1">
            * Spam gönderilmez. İstediğiniz an tek dokunuşla ayrılabilirsiniz.
          </Text>
        </View>

        {/* BOTTOM SAFE BUFFER */}
        <View className="h-16" />
      </ScrollView>
    </SafeAreaView>
  );
};

export default ColumnistsScreen;
