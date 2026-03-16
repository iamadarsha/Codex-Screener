import type { Meta, StoryObj } from "@storybook/react";
import { Button } from "@/components/ui/button";

const meta: Meta<typeof Button> = {
  title: "UI/Button",
  component: Button,
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["primary", "secondary", "ghost"],
    },
    size: {
      control: "select",
      options: ["sm", "md", "lg"],
    },
    disabled: { control: "boolean" },
  },
};

export default meta;
type Story = StoryObj<typeof Button>;

export const Primary: Story = {
  args: { children: "Get Started", variant: "primary", size: "md" },
};

export const Secondary: Story = {
  args: { children: "Learn More", variant: "secondary", size: "md" },
};

export const Ghost: Story = {
  args: { children: "Cancel", variant: "ghost", size: "md" },
};

export const Small: Story = {
  args: { children: "Small", variant: "primary", size: "sm" },
};

export const Large: Story = {
  args: { children: "Large Action", variant: "primary", size: "lg" },
};

export const Disabled: Story = {
  args: { children: "Disabled", variant: "primary", disabled: true },
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="primary" disabled>Disabled</Button>
    </div>
  ),
};
