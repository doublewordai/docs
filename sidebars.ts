import type { SidebarsConfig } from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    // Home Section
    {
      type: 'doc',
      id: 'home/index',
      label: 'Home',
    },
    {
      type: 'doc',
      id: 'home/home-static',
      label: 'Home (Static)',
    },
    
    // Control Layer Section
    {
      type: 'category',
      label: 'Control Layer',
      className: 'sidebar-section-header control-layer-section control-layer-with-icon',
      link: {
        type: 'doc',
        id: 'control-layer/index',
      },
      collapsible: false,
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Deployment',
          link: {
            type: 'doc',
            id: 'control-layer/deployment/index',
          },
          collapsible: true,
          collapsed: false,
          items: [
            'control-layer/deployment/docker-compose',
            'control-layer/deployment/kubernetes',
          ],
        },
        {
          type: 'category', 
          label: 'Usage',
          link: {
            type: 'doc',
            id: 'control-layer/usage/index',
          },
          collapsible: true,
          collapsed: false,
          items: [
            'control-layer/usage/models-and-access',
            'control-layer/usage/playground',
            'control-layer/usage/api-integration',
            {
              type: 'category',
              label: 'Admin',
              items: [
                'control-layer/usage/admin/model-sources',
                'control-layer/usage/admin/users-and-groups',
              ],
            },
          ],
        },
        {
          type: 'category',
          label: 'Reference',
          link: {
            type: 'doc',
            id: 'control-layer/reference/index',
          },
          collapsible: true,
          collapsed: false,
          items: [
            'control-layer/reference/configuration',
          ],
        },
      ],
    },
    
    // Spacer for visual separation
    {
      type: 'html',
      value: '<div class="sidebar-divider"></div>',
    },
    
    // Inference Stack Section
    {
      type: 'category',
      label: 'Inference Stack',
      className: 'sidebar-section-header inference-stack-section inference-stack-with-icon',
      link: {
        type: 'doc',
        id: 'inference-stack/index',
      },
      collapsible: false,
      collapsed: false,
      items: [
        {
          type: 'category',
          label: 'Deployment',
          link: {
            type: 'doc',
            id: 'inference-stack/deployment/index',
          },
          collapsible: true,
          collapsed: false,
          items: [
            'inference-stack/deployment/first',
          ],
        },
        {
          type: 'category',
          label: 'Usage', 
          link: {
            type: 'doc',
            id: 'inference-stack/usage/index',
          },
          collapsible: true,
          collapsed: false,
          items: [],
        },
        {
          type: 'category',
          label: 'Reference',
          link: {
            type: 'doc',
            id: 'inference-stack/reference/index',
          },
          collapsible: true,
          collapsed: false,
          items: [
            'inference-stack/reference/configuration',
          ],
        },
      ],
    },
  ],
};

export default sidebars;
