import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";

import { colors } from "../src/theme/colors";

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: colors.bgPage }}>
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.bgSidebar },
          headerTintColor: colors.textPrimary,
          contentStyle: { backgroundColor: colors.bgPage },
        }}
      />
    </GestureHandlerRootView>
  );
}
