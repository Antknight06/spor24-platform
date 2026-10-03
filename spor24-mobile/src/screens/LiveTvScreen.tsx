import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Share,
  RefreshControl,
  Dimensions,
  StatusBar,
  SafeAreaView,
  Linking,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const { width } = Dimensions.get('window');

// ==========================================
// 1. TYPESCRIPT DATA INTERFACES
// ==========================================
export interface BroadcastProgram {
  id: string;
  time_range: string;
  title: string;
  federation: string;
  status: 'completed' | 'on_air' | 'upcoming';
  description?: string;
}

export interface VodVideoItem {
  id: string;
  title: string;
  federation: string;
  duration: string;
  view_count: number;
  thumbnail_url: string;
  published_at: string;
  video_url: string;
}

export interface LiveStreamMetadata {
  title: string;
  description: string;
  current_viewers: number;
  quality: string;
  fps: number;
  stream_url: string;
  poster_url: string;
  is_live: boolean;
}

// ==========================================
// 2. FALLBACK / OFFLINE MOCK DATA
// ==========================================
const FALLBACK_LIVE_METADATA: LiveStreamMetadata = {
  title: 'Özel Maç & Federasyon Arşiv Kuşağı',
  description:
    'Türkiye Boks ve Güreş Federasyonu tarihi altın madalya finalleri, milli sporcularımızın taktik analizleri ve kulis değerlendirmeleriyle canlı yayında.',
  current_viewers: 1842,
  quality: '1080p',
  fps: 60,
  stream_url: 'https://spor24.net/live/hls/stream.m3u8',
  poster_url:
    'https://images.unsplash.com/photo-1549719386-74dfcbf7dbed?auto=format&fit=crop&w=1200&q=80',
  is_live: true,
};

const FALLBACK_TIMELINE: BroadcastProgram[] = [
  {
    id: 'prog-1',
    time_range: '14:00 - 15:30',
    title: 'Türkiye Boks Şampiyonası Ağır Sıklet Finalleri',
    federation: 'TÜRKİYE BOKS FEDERASYONU',
    status: 'completed',
  },
  {
    id: 'prog-2',
    time_range: '15:30 - 17:00',
    title: 'Veledrom Genç Pedal Kupası & Zamana Karşı Yarışlar',
    federation: 'TÜRKİYE BİSİKLET FEDERASYONU',
    status: 'completed',
  },
  {
    id: 'prog-3',
    time_range: '17:00 - 18:30',
    title: 'Özel Maç & Federasyon Arşiv Kuşağı: Tarihi Şampiyonluklar',
    federation: 'SPOR24 CANLI MASASI',
    status: 'on_air',
    description:
      'Boks ve Güreş altın madalya tahlili & Kenan Demirel ile canlı analiz.',
  },
  {
    id: 'prog-4',
    time_range: '18:30 - 20:00',
    title: 'Karate Federasyonu Paris Etabı Özel Röportajları',
    federation: 'TÜRKİYE KARATE FEDERASYONU',
    status: 'upcoming',
  },
  {
    id: 'prog-5',
    time_range: '20:00 - 22:00',
    title: 'Dövüş Sporları En İyi 10 Nakavt Kuşağı (Muay Thai & Wushu)',
    federation: 'TÜRKİYE MUAY THAI FEDERASYONU',
    status: 'upcoming',
  },
];

const FALLBACK_VOD_LIST: VodVideoItem[] = [
  {
    id: 'vod-1',
    title: 'Dünya Gençler Muay Thai Şampiyonası Final Maçı',
    federation: 'MUAY THAI',
    duration: '04:15',
    view_count: 3820,
    thumbnail_url:
      'https://images.unsplash.com/photo-1517438322307-e67111335449?auto=format&fit=crop&w=600&q=80',
    published_at: '2 saat önce',
    video_url: 'https://spor24.net/videos/muaythai-final.mp4',
  },
  {
    id: 'vod-2',
    title: '59. Cumhurbaşkanlığı Bisiklet Turu Kemer Etabı Özeti',
    federation: 'BİSİKLET',
    duration: '06:40',
    view_count: 5120,
    thumbnail_url:
      'https://images.unsplash.com/photo-1544161515-4ab6ce6db874?auto=format&fit=crop&w=600&q=80',
    published_at: '4 saat önce',
    video_url: 'https://spor24.net/videos/tur-kemer-ozet.mp4',
  },
  {
    id: 'vod-3',
    title: 'Grekoromen Güreş Ağır Sıklet Taktik Analizi',
    federation: 'GÜREŞ',
    duration: '08:20',
    view_count: 2940,
    thumbnail_url:
      'https://images.unsplash.com/photo-1517838277536-f5f99be501cd?auto=format&fit=crop&w=600&q=80',
    published_at: 'Dün',
    video_url: 'https://spor24.net/videos/gures-analiz.mp4',
  },
  {
    id: 'vod-4',
    title: 'Balkan Wushu Şampiyonası Altın Madalya Serisi',
    federation: 'WUSHU',
    duration: '05:30',
    view_count: 1750,
    thumbnail_url:
      'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=600&q=80',
    published_at: '2 gün önce',
    video_url: 'https://spor24.net/videos/wushu-balkan.mp4',
  },
];

// ==========================================
// 3. MAIN COMPONENT: LiveTvScreen
// ==========================================
export const LiveTvScreen: React.FC = () => {
  const navigation = useNavigation<any>();

  // State Management
  const [liveData, setLiveData] = useState<LiveStreamMetadata>(FALLBACK_LIVE_METADATA);
  const [timeline, setTimeline] = useState<BroadcastProgram[]>(FALLBACK_TIMELINE);
  const [vodList, setVodList] = useState<VodVideoItem[]>(FALLBACK_VOD_LIST);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [isNotified, setIsNotified] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Dynamic Backend Fetch: https://spor24.net/api/videos/
  const fetchVideoData = async () => {
    try {
      setLoading(true);
      const res = await fetch('https://spor24.net/api/videos/');
      if (res.ok) {
        const data = await res.json();
        if (data.live) setLiveData(data.live);
        if (data.timeline) setTimeline(data.timeline);
        if (data.vods) setVodList(data.vods);
      }
    } catch (error) {
      console.warn(
        'Video API bağlantısı kurulamadı, çevrimdışı canlı akış devrede:',
        error
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchVideoData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchVideoData();
  };

  // Actions
  const handleShareStream = async () => {
    try {
      await Share.share({
        message: `🔴 CANLI YAYIN: ${liveData.title} - Spor24 Web TV 1080p kesintisiz yayınında izleyin! https://spor24.net/canli-tv`,
        title: 'Spor24 Web TV Canlı Yayın',
      });
    } catch (e) {
      console.error(e);
    }
  };

  const toggleNotification = () => {
    setIsNotified(!isNotified);
  };

  return (
    <SafeAreaView className="flex-1 bg-[#0B0E14]">
      <StatusBar barStyle="light-content" backgroundColor="#0B0E14" />

      {/* 1. ÜST APP BAR & CANLI YAYIN BİLGİ BANDI */}
      <View className="bg-[#10131A] border-b border-[#1E232E] px-4 py-3">
        <View className="flex-row items-center justify-between">
          <View className="flex-row items-center">
            <TouchableOpacity
              onPress={() => navigation.goBack()}
              className="w-8 h-8 rounded-full bg-[#181C24] items-center justify-center mr-2.5 border border-[#262B36]"
            >
              <Text className="text-white text-xs font-bold">←</Text>
            </TouchableOpacity>
            <View>
              <View className="flex-row items-center">
                <Text className="text-white font-black text-base tracking-wide">
                  SPOR24
                </Text>
                <Text className="text-[#E11D48] font-black text-base ml-1">WEB TV</Text>
              </View>
              <View className="flex-row items-center mt-0.5">
                <View className="w-1.5 h-1.5 rounded-full bg-[#E11D48] mr-1.5 animate-ping" />
                <Text className="text-[#E11D48] text-[9px] font-black tracking-wider uppercase">
                  1080p KESİNTİSİZ YAYIN
                </Text>
              </View>
            </View>
          </View>

          {/* CANLI İZLEYİCİ SAYACI */}
          <View className="bg-[#181C24] px-3 py-1.5 rounded-full border border-[#262B36] flex-row items-center shadow-lg">
            <Text className="text-[#FFD700] text-xs mr-1">👁</Text>
            <Text className="text-[#FFD700] text-xs font-bold mr-1">
              {(liveData.current_viewers || 0).toLocaleString('tr-TR')}
            </Text>
            <Text className="text-[#94A3B8] text-[9px] font-medium">İzleyici</Text>
          </View>
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
        {/* 2. DEV CANLI VİDEO OYNATICI ALANI (HERO LIVE PLAYER) */}
        <View className="relative bg-black border-b border-[#1E232E]">
          <View style={{ width: width, height: (width * 9) / 16 }} className="relative bg-black">
            <Image
              source={{ uri: liveData.poster_url }}
              className="w-full h-full opacity-80"
              resizeMode="cover"
            />
            <View className="absolute inset-0 bg-black/30" />

            {/* OYNATICI İÇİ ÜST HUD ROZETLERİ */}
            <View className="absolute top-3 left-3 flex-row items-center space-x-2">
              <View className="bg-[#E11D48] px-2.5 py-1 rounded flex-row items-center shadow-md shadow-[#E11D48]/40">
                <View className="w-1.5 h-1.5 rounded-full bg-white mr-1.5 animate-pulse" />
                <Text className="text-white text-[9px] font-black tracking-widest uppercase">
                  CANLI • SPOR24 HD
                </Text>
              </View>
            </View>

            <View className="absolute top-3 right-3 flex-row items-center space-x-2">
              <View className="bg-black/75 px-2 py-0.5 rounded border border-white/10">
                <Text className="text-[#38BDF8] text-[9px] font-mono font-bold">
                  {liveData.quality} {liveData.fps}FPS
                </Text>
              </View>
              <TouchableOpacity className="w-7 h-7 rounded bg-black/75 items-center justify-center border border-white/10">
                <Text className="text-white text-[10px]">⛶</Text>
              </TouchableOpacity>
            </View>

            {/* MERKEZİ OYNAT / DURAKLAT ETKİLEŞİMİ */}
            <TouchableOpacity
              activeOpacity={0.85}
              onPress={() => setIsPlaying(!isPlaying)}
              className="absolute inset-0 items-center justify-center"
            >
              <View className="w-14 h-14 rounded-full bg-[#E11D48]/90 items-center justify-center shadow-2xl shadow-[#E11D48]/50 border-2 border-white/20">
                <Text className="text-white text-xl font-bold ml-1">
                  {isPlaying ? '❚❚' : '▶'}
                </Text>
              </View>
            </TouchableOpacity>

            {/* OYNATICI ALTI SES & CANLI GÖSTERGESİ */}
            <View className="absolute bottom-2.5 left-3 right-3 flex-row items-center justify-between">
              <View className="flex-row items-center">
                <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
                <Text className="text-white text-[10px] font-bold">
                  Kesintisiz Canlı Yayın Akışı
                </Text>
              </View>
              <View className="flex-row items-center space-x-2">
                <Text className="text-white text-xs">🔊</Text>
              </View>
            </View>
          </View>

          {/* CANLI PROGRAM BAŞLIĞI & AKSİYON BUTONLARI */}
          <View className="p-4 bg-[#10131A]">
            <View className="flex-row items-center mb-1">
              <View className="bg-[#181C24] px-2 py-0.5 rounded border border-[#262B36] mr-2">
                <Text className="text-[#E11D48] text-[9px] font-black tracking-wider uppercase">
                  ŞU AN YAYINDA
                </Text>
              </View>
              <Text className="text-[#64748B] text-[10px] font-mono">17:00 - 18:30 Kuşağı</Text>
            </View>
            <Text className="text-white font-black text-base leading-6 mb-1.5">
              {liveData.title}
            </Text>
            <Text className="text-[#94A3B8] text-xs leading-4 mb-4">
              {liveData.description}
            </Text>

            {/* HIZLI AKSİYON BUTONLARI */}
            <View className="flex-row items-center space-x-3">
              <TouchableOpacity
                activeOpacity={0.88}
                onPress={handleShareStream}
                className="flex-1 py-2.5 px-3 rounded-xl bg-[#161B26] border border-[#2E3646] flex-row items-center justify-center"
              >
                <Text className="text-white text-xs font-bold mr-1.5">Yayını Paylaş</Text>
                <Text className="text-[#38BDF8] text-xs">↗</Text>
              </TouchableOpacity>
              <TouchableOpacity
                activeOpacity={0.88}
                onPress={toggleNotification}
                className={`flex-1 py-2.5 px-3 rounded-xl border flex-row items-center justify-center ${
                  isNotified
                    ? 'bg-[#E11D48] border-[#E11D48]'
                    : 'bg-[#181C24] border-[#262B36]'
                }`}
              >
                <Text className="mr-1.5 text-xs">{isNotified ? '✓' : '🔔'}</Text>
                <Text className="text-white text-xs font-bold">
                  {isNotified ? 'Bildirim Açık' : 'Yayın Bildirimi'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* 3. GÜNÜN TV YAYIN AKIŞI ÇİZELGESİ (BROADCAST TIMELINE) */}
        <View className="mt-4 px-4">
          <View className="flex-row items-center justify-between mb-3">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                Günün TV Yayın Akışı
              </Text>
            </View>
            <Text className="text-[#64748B] text-[10px] font-mono">
              18 Nisan 2025 • Canlı Akış
            </Text>
          </View>

          <View className="p-3.5 rounded-2xl bg-[#121620] border border-[#1E2432]">
            {timeline.map((prog, index) => {
              const isOnAir = prog.status === 'on_air';
              const isCompleted = prog.status === 'completed';

              return (
                <View key={prog.id} className="relative flex-row pb-4 last:pb-0">
                  {/* VERTICAL LINE */}
                  {index !== timeline.length - 1 && (
                    <View className="absolute left-[7px] top-4 bottom-0 w-[2px] bg-[#1E2432]" />
                  )}

                  {/* TIMELINE NODE DOT */}
                  <View className="mr-3 pt-0.5">
                    {isOnAir ? (
                      <View className="w-4 h-4 rounded-full bg-[#E11D48]/20 border-2 border-[#E11D48] items-center justify-center">
                        <View className="w-1.5 h-1.5 rounded-full bg-[#E11D48] animate-ping" />
                      </View>
                    ) : isCompleted ? (
                      <View className="w-4 h-4 rounded-full bg-[#1A1F2B] border border-[#2B3545] items-center justify-center">
                        <Text className="text-[#64748B] text-[8px] font-bold">✓</Text>
                      </View>
                    ) : (
                      <View className="w-4 h-4 rounded-full bg-[#181C24] border border-[#262B36]" />
                    )}
                  </View>

                  {/* PROGRAM CARD CONTENT */}
                  <View
                    className={`flex-1 p-2.5 rounded-xl border ${
                      isOnAir
                        ? 'bg-[#181D29] border-[#E11D48]/40 shadow-lg'
                        : 'bg-[#0E1118] border-[#181D28]'
                    }`}
                  >
                    <View className="flex-row items-center justify-between mb-1">
                      <Text
                        className={`text-[10px] font-mono font-bold ${
                          isOnAir ? 'text-[#E11D48]' : 'text-[#64748B]'
                        }`}
                      >
                        {prog.time_range}
                      </Text>
                      {isOnAir ? (
                        <View className="bg-[#E11D48] px-1.5 py-0.5 rounded">
                          <Text className="text-white text-[8px] font-black uppercase">
                            ŞU AN YAYINDA
                          </Text>
                        </View>
                      ) : isCompleted ? (
                        <Text className="text-[#64748B] text-[9px]">Tamamlandı</Text>
                      ) : (
                        <Text className="text-[#38BDF8] text-[9px] font-bold">Sıradaki</Text>
                      )}
                    </View>
                    <Text
                      className={`text-xs font-bold leading-4 mb-0.5 ${
                        isOnAir ? 'text-white' : 'text-[#CBD5E1]'
                      }`}
                    >
                      {prog.title}
                    </Text>
                    <Text className="text-[#64748B] text-[9px] font-medium uppercase tracking-wider">
                      {prog.federation}
                    </Text>
                    {prog.description ? (
                      <Text className="text-[#94A3B8] text-[10px] mt-1.5 pt-1.5 border-t border-[#262D3D]">
                        {prog.description}
                      </Text>
                    ) : null}
                  </View>
                </View>
              );
            })}
          </View>
        </View>

        {/* 4. FEDERASYON VOD VİDEO GALERİSİ (2 SÜTUNLU GRID) */}
        <View className="mt-5 px-4 pb-20">
          <View className="flex-row items-center justify-between mb-3">
            <View className="flex-row items-center">
              <View className="w-1 h-3.5 bg-[#E11D48] rounded mr-1.5" />
              <Text className="text-white text-xs font-black tracking-wider uppercase">
                Federasyon Video Havuzu (VOD)
              </Text>
            </View>
            <TouchableOpacity
              onPress={() => Linking.openURL('https://spor24.net/videolar')}
            >
              <Text className="text-[#94A3B8] text-xs">Tüm Arşiv (124) ➔</Text>
            </TouchableOpacity>
          </View>

          {/* 2-COLUMN GRID */}
          <View className="flex-row flex-wrap justify-between">
            {vodList.map((vod) => (
              <TouchableOpacity
                key={vod.id}
                activeOpacity={0.88}
                onPress={() => Linking.openURL(vod.video_url)}
                style={{ width: (width - 44) / 2 }}
                className="mb-3.5 rounded-xl overflow-hidden bg-[#121620] border border-[#1E2432]"
              >
                {/* THUMBNAIL WITH DURATION & PLAY BADGE */}
                <View className="relative h-28 w-full bg-[#181C24]">
                  <Image
                    source={{ uri: vod.thumbnail_url }}
                    className="w-full h-full"
                    resizeMode="cover"
                  />
                  <View className="absolute inset-0 bg-black/35" />

                  {/* PLAY ICON */}
                  <View className="absolute inset-0 items-center justify-center">
                    <View className="w-8 h-8 rounded-full bg-black/60 items-center justify-center border border-white/20">
                      <Text className="text-white text-xs font-bold ml-0.5">▶</Text>
                    </View>
                  </View>

                  {/* FEDERATION BADGE */}
                  <View className="absolute top-1.5 left-1.5 bg-[#0B0E14]/85 px-1.5 py-0.5 rounded border border-white/10">
                    <Text className="text-[#E11D48] text-[8px] font-black uppercase">
                      {vod.federation}
                    </Text>
                  </View>

                  {/* DURATION BADGE */}
                  <View className="absolute bottom-1.5 right-1.5 bg-black/80 px-1.5 py-0.5 rounded">
                    <Text className="text-white text-[8px] font-mono font-bold">
                      {vod.duration}
                    </Text>
                  </View>
                </View>

                {/* VOD DETAILS */}
                <View className="p-2.5 justify-between">
                  <Text
                    className="text-white font-bold text-xs leading-4 mb-2"
                    numberOfLines={2}
                  >
                    {vod.title}
                  </Text>
                  <View className="flex-row items-center justify-between pt-1 border-t border-[#1C212D]">
                    <Text className="text-[#64748B] text-[9px]">{vod.published_at}</Text>
                    <View className="flex-row items-center">
                      <Text className="text-[#FFD700] text-[10px] mr-0.5">👁</Text>
                      <Text className="text-[#FFD700] text-[10px] font-bold">
                        {(vod.view_count || 0).toLocaleString('tr-TR')}
                      </Text>
                    </View>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

export default LiveTvScreen;
