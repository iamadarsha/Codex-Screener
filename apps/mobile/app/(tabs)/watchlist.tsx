import { StyleSheet, Text, View } from "react-native";

import { Screen } from "../../src/components/layout/screen";
import { colors } from "../../src/theme/colors";

export default function WatchlistScreen() {
  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.title}>Watchlist</Text>
        <Text style={styles.copy}>
          Draggable watchlists, swipe actions, and the add-symbol sheet come
          after the live data and alerts layers are in place.
        </Text>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgCard,
    padding: 20,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 26,
    fontWeight: "700",
  },
  copy: {
    marginTop: 12,
    color: colors.textSecondary,
    fontSize: 15,
    lineHeight: 22,
  },
});
