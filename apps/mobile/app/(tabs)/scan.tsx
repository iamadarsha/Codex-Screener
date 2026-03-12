import { StyleSheet, Text, View } from "react-native";

import { Screen } from "../../src/components/layout/screen";
import { colors } from "../../src/theme/colors";

export default function ScanScreen() {
  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.title}>Scan</Text>
        <Text style={styles.copy}>
          Prebuilt scan categories and animated result screens will arrive in
          the mobile feature phase.
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
