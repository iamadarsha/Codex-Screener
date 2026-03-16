import type { Meta, StoryObj } from "@storybook/react";
import { Badge } from "@/components/ui/badge";

const meta: Meta<typeof Badge> = {
  title: "UI/Badge",
  component: Badge,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["neutral", "accent", "bullish", "bearish", "warning"],
    },
  },
};

export default meta;
type Story = StoryObj<typeof Badge>;

export const Default: Story = {
  args: { children: "Default", variant: "neutral" },
};

export const Accent: Story = {
  args: { children: "12 signals", variant: "accent" },
};

export const Bullish: Story = {
  args: { children: "+3.2%", variant: "bullish" },
};

export const Bearish: Story = {
  args: { children: "-1.8%", variant: "bearish" },
};

export const Warning: Story = {
  args: { children: "Volatile", variant: "warning" },
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
      <Badge variant="neutral">Default</Badge>
      <Badge variant="accent">Accent</Badge>
      <Badge variant="bullish">Bullish</Badge>
      <Badge variant="bearish">Bearish</Badge>
      <Badge variant="warning">Warning</Badge>
    </div>
  ),
};
