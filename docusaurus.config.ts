import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Documentation',
  tagline: 'Doubleword Technical Documentation',
  favicon: 'img/favicon.ico',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: process.env.DOCUSAURUS_URL || 'https://doubleword-docs.pages.dev',
  // Set the /<baseUrl>/ pathname under which your site is served
  baseUrl: process.env.DOCUSAURUS_BASE_URL || '/',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarCollapsed: false,
          sidebarPath: './sidebars.ts',
          routeBasePath: '/', // Serve the docs at the site's root
          showLastUpdateTime: false,
          includeCurrentVersion: true,
        },
        blog: {
          showReadingTime: true,
          routeBasePath: 'conceptual',
          path: 'conceptual',
          blogTitle: 'Conceptual Guides',
          blogDescription: 'Conceptual guides and deep dives into AI infrastructure',
          blogSidebarCount: 'ALL',
          blogSidebarTitle: 'All Guides',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    [
      "posthog-docusaurus",
      {
        apiKey: "phc_Gsc7iKs7KCkxySkNRu8pmJb3dYr4RcrOgYPvnBmvviH",
        appUrl: "https://eu.i.posthog.com", // optional, defaults to "https://us.i.posthog.com"
        enableInDevelopment: false, // optional
      },
    ],
  ],

  themeConfig: {
    // Replace with your project's social card
    image: 'img/docusaurus-social-card.jpg',
    colorMode: {
      defaultMode: 'light',
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      logo: {
        alt: 'Doubleword Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Documentation',
        },
        { to: "/conceptual", label: "Conceptual Guides", position: "left" },
        { to: "/support", label: "Support", position: "left" },
        {
          href: 'https://github.com/doublewordai/control-layer',
          position: 'right',
          className: 'header-github-link control-layer-github',
          label: 'Control Layer',
        },
        {
          href: 'https://github.com/doublewordai/inference-stack',
          position: 'right',
          className: 'header-github-link inference-stack-github',
          label: 'Inference Stack',
        },
      ],
    },
    footer: {
      style: 'dark',
      copyright: `Copyright © ${new Date().getFullYear()} Doubleword AI.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
