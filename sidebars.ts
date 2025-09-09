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
    // Overview Section
    {
      type: 'doc',
      id: 'overview/index',
      label: '📋 Overview',
      className: 'sidebar-overview-section',
    },
    
    // Spacer for visual separation
    {
      type: 'html',
      value: '<div class="sidebar-divider"></div>',
    },
    
    // Control Layer Section
    {
      type: 'category',
      label: '🛡️ Control Layer',
      className: 'sidebar-section-header control-layer-section',
      link: {
        type: 'doc',
        id: 'control-layer/index',
      },
      collapsible: true,
      collapsed: true,
      items: [
        {
          type: 'category',
          label: 'Deployment',
          collapsible: true,
          collapsed: false,
          items: [
            'control-layer/deployment/index',
            'control-layer/deployment/docker-compose',
            'control-layer/deployment/kubernetes',
          ],
        },
        {
          type: 'category', 
          label: 'Usage',
          collapsible: true,
          collapsed: false,
          items: [
            'control-layer/usage/index',
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
          collapsible: true,
          collapsed: true,
          items: [
            'control-layer/reference/index',
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
      label: '⚡ Inference Stack',
      className: 'sidebar-section-header inference-stack-section',
      link: {
        type: 'doc',
        id: 'inference-stack/index',
      },
      collapsible: true,
      collapsed: true,
      items: [
        {
          type: 'category',
          label: 'Deployment',
          collapsible: true,
          collapsed: false,
          items: [
            'inference-stack/deployment/index',
            'inference-stack/deployment/docker-compose',
            'inference-stack/deployment/kubernetes',
          ],
        },
        {
          type: 'category',
          label: 'Usage', 
          collapsible: true,
          collapsed: false,
          items: [
            'inference-stack/usage/index',
          ],
        },
        {
          type: 'category',
          label: 'Reference',
          collapsible: true,
          collapsed: true,
          items: [
            'inference-stack/reference/index',
            'inference-stack/reference/configuration',
          ],
        },
      ],
    },
  ],
};

export default sidebars;
