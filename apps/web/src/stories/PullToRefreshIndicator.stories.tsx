import type { Meta, StoryObj } from "@storybook/react";
import { PullToRefreshIndicator } from "@/components/ui/pull-to-refresh-indicator";

const meta: Meta<typeof PullToRefreshIndicator> = {
  title: "UI/PullToRefreshIndicator",
  component: PullToRefreshIndicator,
  tags: ["autodocs"],
  argTypes: {
    pullDistance: { control: { type: "range", min: 0, max: 120 } },
    refreshing: { control: "boolean" },
    threshold: { control: { type: "number", min: 40, max: 120 } },
  },
};

export default meta;
type Story = StoryObj<typeof PullToRefreshIndicator>;

export const Idle: Story = {
  args: { pullDistance: 0, refreshing: false },
};

export const Pulling: Story = {
  args: { pullDistance: 40, refreshing: false, threshold: 80 },
};

export const ReadyToRelease: Story = {
  args: { pullDistance: 85, refreshing: false, threshold: 80 },
};

export const Refreshing: Story = {
  args: { pullDistance: 0, refreshing: true, threshold: 80 },
};
