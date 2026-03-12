import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";

export default function AlertsPage() {
  return (
    <AppShell>
      <Card>
        <div className="text-xs uppercase tracking-[0.22em] text-[#5C5D6E]">
          Alerts
        </div>
        <h1 className="mt-2 text-3xl font-bold text-white">Signal triggers</h1>
        <p className="mt-3 text-sm text-[#9899A8]">
          Alert forms, active toggles, and trigger history will connect to the
          backend alert system later in the delivery sequence.
        </p>
      </Card>
    </AppShell>
  );
}

