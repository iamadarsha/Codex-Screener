import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { Screen } from "../../src/components/layout/screen";
import { colors } from "../../src/theme/colors";

export default function ScanDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.label}>Scan Details</Text>
        <Text style={styles.title}>{id ?? "scan"}</Text>
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
});
