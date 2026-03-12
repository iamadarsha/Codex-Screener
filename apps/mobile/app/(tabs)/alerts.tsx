import { StyleSheet, Text, View } from "react-native";

import { Screen } from "../../src/components/layout/screen";
import { colors } from "../../src/theme/colors";

export default function AlertsScreen() {
  return (
    <Screen>
      <View style={styles.card}>
        <Text style={styles.title}>Alerts</Text>
        <Text style={styles.copy}>
          Notification permissions, toggles, and timeline history are planned
          for the native alerts delivery phase.
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
