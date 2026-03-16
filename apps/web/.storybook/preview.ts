import type { Preview } from "@storybook/react";
import "../src/app/globals.css";

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    backgrounds: {
      default: "dark",
      values: [
        { name: "dark", value: "#0a0e1a" },
        { name: "light", value: "#f0f2f8" },
      ],
    },
  },
  decorators: [
    (Story) => (
      <div data-theme="dark" style={{ padding: "2rem", minHeight: "100vh", background: "var(--bg-page)", color: "var(--text-primary)" }}>
        <Story />
      </div>
    ),
  ],
};

export default preview;
