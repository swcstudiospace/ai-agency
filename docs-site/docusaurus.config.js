// @ts-check
/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "AI Dropshipping Agency",
  tagline: "Hermes × Agno · 30 agents · Parallel · SuperGrok · Shopify",
  favicon: "img/favicon.svg",
  url: "https://swcstudiospace.github.io",
  baseUrl: "/ai-agency/",
  organizationName: "swcstudiospace",
  projectName: "ai-agency",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  i18n: { defaultLocale: "en", locales: ["en"] },
  presets: [
    [
      "classic",
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: "./sidebars.js",
          editUrl: "https://github.com/swcstudiospace/ai-agency/tree/main/docs-site/",
          showLastUpdateTime: false,
        },
        blog: {
          showReadingTime: true,
          blogTitle: "Agency field notes",
        },
        theme: { customCss: "./src/css/custom.css" },
      }),
    ],
  ],
  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: "img/social-card.svg",
      colorMode: {
        defaultMode: "dark",
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: "AI Agency",
        logo: { alt: "Agency", src: "img/logo.svg" },
        items: [
          { type: "docSidebar", sidebarId: "docs", position: "left", label: "Docs" },
          { to: "/blog", label: "Field notes", position: "left" },
          {
            href: "https://github.com/swcstudiospace/ai-agency",
            label: "GitHub",
            position: "right",
          },
        ],
      },
      footer: {
        style: "dark",
        links: [
          {
            title: "Docs",
            items: [
              { label: "Quick start", to: "/docs/getting-started/quickstart" },
              { label: "Product locate", to: "/docs/guides/product-locate" },
              { label: "Autonomy & keys", to: "/docs/operations/autonomy-and-keys" },
            ],
          },
          {
            title: "Control planes",
            items: [
              { label: "AgentOS :7777", to: "/docs/architecture/control-planes" },
              { label: "Drop gateway", to: "/docs/architecture/control-planes" },
              { label: "Hermes bridge", to: "/docs/architecture/hermes-bridge" },
            ],
          },
          {
            title: "More",
            items: [
              { label: "GitHub", href: "https://github.com/swcstudiospace/ai-agency" },
              { label: "Linear project", href: "https://linear.app/spectrumwebco/project/ai-dropshipping-agency-e61fc9b53cae" },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Spectrum Web Co · AI Dropshipping Agency`,
      },
      prism: {
        theme: require("prism-react-renderer").themes.github,
        darkTheme: require("prism-react-renderer").themes.dracula,
        additionalLanguages: ["bash", "json", "python", "yaml"],
      },
    }),
};

module.exports = config;
