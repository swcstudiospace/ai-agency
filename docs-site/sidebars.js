/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: "category",
      label: "Getting started",
      collapsed: false,
      items: [
        "getting-started/intro",
        "getting-started/quickstart",
        "getting-started/shopify-setup",
      ],
    },
    {
      type: "category",
      label: "Architecture",
      items: [
        "architecture/overview",
        "architecture/control-planes",
        "architecture/agents-teams-workflows",
        "architecture/hermes-bridge",
        "architecture/memory-kip",
      ],
    },
    {
      type: "category",
      label: "Guides",
      collapsed: false,
      items: [
        "guides/product-discovery",
        "guides/product-locate",
        "guides/dropshipping-lifecycle",
        "guides/ugc-promptwise",
        "guides/hitl-spend",
        "guides/e2e-testing",
      ],
    },
    {
      type: "category",
      label: "Operations",
      items: [
        "operations/autonomy-and-keys",
        "operations/ci-cd",
        "operations/linear-github",
        "operations/cockpit-ui",
      ],
    },
    {
      type: "category",
      label: "Reference",
      items: [
        "reference/scripts",
        "reference/env",
        "reference/ports",
      ],
    },
  ],
};

module.exports = sidebars;
