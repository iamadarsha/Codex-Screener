import { StyleSheet, Text, View } from "react-native";

import { Screen } from "../../src/components/layout/screen";
import { colors } from "../../src/theme/colors";

export default function HomeScreen() {
  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.label}>Home</Text>
        <Text style={styles.title}>Market dashboard scaffold</Text>
        <Text style={styles.copy}>
          The Phase 1 mobile app establishes navigation, theming, and the dark
          trading-terminal palette for later feature work.
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
  label: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
    textTransform: "uppercase",
  },
  title: {
    marginTop: 12,
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
