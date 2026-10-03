import React from 'react';
import { View, Text, Platform, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

// Ekran Bileşenleri İçe Aktarımı
import HomeScreen from './screens/HomeScreen';
import FederationsScreen from './screens/FederationsScreen';
import LiveTvScreen from './screens/LiveTvScreen';
import ColumnistsScreen from './screens/ColumnistsScreen';
import NewsDetailScreen from './screens/NewsDetailScreen';

// ==========================================
// 1. NAVIGATION TYPE DEFINITIONS
// ==========================================
export type RootTabParamList = {
  HomeTab: undefined;
  FederationsTab: undefined;
  LiveTvTab: undefined;
  ColumnistsTab: undefined;
};

export type RootStackParamList = {
  MainTabs: undefined;
  NewsDetailScreen: {
    newsId: string | number;
    title?: string;
  };
};

const Tab = createBottomTabNavigator<RootTabParamList>();
const Stack = createNativeStackNavigator<RootStackParamList>();

// ==========================================
// 2. ÖZEL ALT SEKME İKONU VE ROZETİ
// ==========================================
interface TabBarIconProps {
  focused: boolean;
  iconName: string;
  label: string;
  badgeCount?: number;
  isLive?: boolean;
}

const TabBarItem: React.FC<TabBarIconProps> = ({
  focused,
  iconName,
  label,
  badgeCount,
  isLive,
}) => {
  return (
    <View style={styles.tabItemContainer}>
      <View style={[styles.iconWrapper, focused && styles.iconWrapperActive]}>
        <Text style={[styles.tabIcon, focused && styles.tabIconActive]}>
          {iconName}
        </Text>

        {/* CANLI YAYIN ROZETİ (Web TV için) */}
        {isLive && (
          <View style={styles.liveIndicatorWrapper}>
            <View style={styles.liveIndicatorDot} />
          </View>
        )}

        {/* BİLDİRİM SAYACI (Federasyonlar veya Yazarlar için) */}
        {badgeCount && badgeCount > 0 ? (
          <View style={styles.badgeContainer}>
            <Text style={styles.badgeText}>{badgeCount}</Text>
          </View>
        ) : null}
      </View>

      <Text style={[styles.tabLabel, focused && styles.tabLabelActive]}>
        {label}
      </Text>

      {/* AKTİF SEKME ALT KIRMIZI ÇİZGİSİ */}
      {focused && <View style={styles.activeIndicator} />}
    </View>
  );
};

// ==========================================
// 3. BOTTOM TAB NAVIGATOR (4 ANA SEKME)
// ==========================================
const BottomTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      initialRouteName="HomeTab"
      screenOptions={{
        headerShown: false,
        tabBarShowLabel: false,
        tabBarStyle: styles.tabBar,
      }}
    >
      {/* 1. SEKME: ANA SAYFA */}
      <Tab.Screen
        name="HomeTab"
        component={HomeScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabBarItem focused={focused} iconName="⚡" label="Ana Sayfa" />
          ),
        }}
      />

      {/* 2. SEKME: 44 FEDERASYON & BRANŞ HAVUZU */}
      <Tab.Screen
        name="FederationsTab"
        component={FederationsScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabBarItem
              focused={focused}
              iconName="🛡"
              label="Federasyonlar"
              badgeCount={44}
            />
          ),
        }}
      />

      {/* 3. SEKME: SPOR24 WEB TV (CANLI YAYIN) */}
      <Tab.Screen
        name="LiveTvTab"
        component={LiveTvScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabBarItem
              focused={focused}
              iconName="📺"
              label="Canlı TV"
              isLive={true}
            />
          ),
        }}
      />

      {/* 4. SEKME: KÖŞE YAZARLARI & ANALİZ */}
      <Tab.Screen
        name="ColumnistsTab"
        component={ColumnistsScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <TabBarItem focused={focused} iconName="🖋" label="Yazarlar" />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

// ==========================================
// 4. ROOT STACK NAVIGATOR (DETAY GEÇİŞLERİ)
// ==========================================
export const AppNavigator: React.FC = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="MainTabs"
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
          animationDuration: 280,
          contentStyle: { backgroundColor: '#0B0E14' },
        }}
      >
        {/* Ana Alt Barlı Ekranlar */}
        <Stack.Screen name="MainTabs" component={BottomTabNavigator} />

        {/* Haber & SHA-256 Dijital Mühür Detay Ekranı */}
        <Stack.Screen
          name="NewsDetailScreen"
          component={NewsDetailScreen}
          options={{
            animation: 'slide_from_right',
            gestureEnabled: true,
            gestureDirection: 'horizontal',
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;

// ==========================================
// 5. STYLESHEET (ÖZEL BAR TASARIMI)
// ==========================================
const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#10131A',
    borderTopColor: '#1E232E',
    borderTopWidth: 1,
    height: Platform.OS === 'ios' ? 88 : 68,
    paddingTop: 8,
    paddingBottom: Platform.OS === 'ios' ? 28 : 10,
    elevation: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.45,
    shadowRadius: 10,
  },
  tabItemContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    height: '100%',
    position: 'relative',
  },
  iconWrapper: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    position: 'relative',
  },
  iconWrapperActive: {
    backgroundColor: 'rgba(225, 29, 72, 0.15)', // Crimson Red Soft Glow
  },
  tabIcon: {
    fontSize: 16,
    opacity: 0.65,
  },
  tabIconActive: {
    opacity: 1,
    transform: [{ scale: 1.1 }],
  },
  tabLabel: {
    color: '#94A3B8',
    fontSize: 10,
    fontWeight: '600',
    marginTop: 2,
    letterSpacing: 0.2,
  },
  tabLabelActive: {
    color: '#FFFFFF',
    fontWeight: '800',
  },
  activeIndicator: {
    position: 'absolute',
    bottom: -6,
    width: 16,
    height: 2.5,
    borderRadius: 2,
    backgroundColor: '#E11D48',
  },
  liveIndicatorWrapper: {
    position: 'absolute',
    top: 1,
    right: 1,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(225, 29, 72, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  liveIndicatorDot: {
    width: 5,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: '#E11D48',
  },
  badgeContainer: {
    position: 'absolute',
    top: -2,
    right: -6,
    backgroundColor: '#1E232E',
    borderColor: '#E11D48',
    borderWidth: 1,
    borderRadius: 7,
    paddingHorizontal: 4,
    height: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeText: {
    color: '#FFD700',
    fontSize: 8,
    fontWeight: '900',
  },
});
