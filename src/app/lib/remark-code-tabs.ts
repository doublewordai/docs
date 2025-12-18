import { visit } from 'unist-util-visit';
import type { Plugin } from 'unified';
import type { Root, Code, Parent, HTML } from 'mdast';

interface CodeNode extends Code {
  meta?: string | null;
}

interface TabBlock {
  name: string;
  lang: string;
  value: string;
  node: CodeNode;
  parent: Parent;
  index: number;
  sync?: string;
}

const remarkCodeTabs: Plugin<[], Root> = () => {
  return (tree) => {
    // Collect all code blocks with tabs metadata
    const tabGroups = new Map<string, TabBlock[]>();

    visit(tree, 'code', (node: CodeNode, index, parent) => {
      if (!node.meta || index === undefined || !parent) return;

      const tabsMatch = node.meta.match(/tabs=(\S+)/);
      const nameMatch = node.meta.match(/name=(\S+)/);
      const syncMatch = node.meta.match(/sync=(\S+)/);

      if (tabsMatch && nameMatch) {
        const tabs = tabsMatch[1];
        const name = nameMatch[1];
        const sync = syncMatch ? syncMatch[1] : undefined;

        if (!tabGroups.has(tabs)) {
          tabGroups.set(tabs, []);
        }

        tabGroups.get(tabs)!.push({
          name,
          lang: node.lang || 'text',
          value: node.value,
          node,
          parent: parent as Parent,
          index,
          sync,
        });
      }
    });

    // Process each tab group
    tabGroups.forEach((blocks, tabsId) => {
      if (blocks.length === 0) return;

      // Find the first block
      const firstBlock = blocks[0];
      const syncAttr = firstBlock.sync ? ` data-sync="${firstBlock.sync}"` : '';

      // Create select dropdown HTML
      const selectOptions = blocks
        .map(
          (block, i) =>
            `<option value="${i}">${block.name}</option>`
        )
        .join('');

      // Create new nodes
      const newNodes: Array<HTML | CodeNode> = [];

      // Container with select dropdown (first option selected by default)
      newNodes.push({
        type: 'html',
        value: `<div class="code-tabs-container"><select class="code-tabs-select" data-code-tabs-select${syncAttr}>${selectOptions}</select>`,
      });

      // Add each tab panel with its code block
      blocks.forEach((block, i) => {
        newNodes.push({
          type: 'html',
          value: `<div class="code-tab-panel${i === 0 ? ' active' : ''}" data-panel="${i}">`,
        });

        newNodes.push({
          type: 'code',
          lang: block.lang,
          value: block.value,
          meta: null,
        });

        newNodes.push({
          type: 'html',
          value: '</div>',
        });
      });

      // Close container
      newNodes.push({
        type: 'html',
        value: '</div>',
      });

      // Replace the first block with the entire tab structure
      const firstParent = firstBlock.parent;
      const firstIndex = firstParent.children.indexOf(firstBlock.node);
      if (firstIndex !== -1) {
        firstParent.children.splice(firstIndex, 1, ...newNodes);
      }

      // Remove all other blocks in this group
      blocks.slice(1).forEach((block) => {
        const parentNode = block.parent;
        const nodeIndex = parentNode.children.indexOf(block.node);
        if (nodeIndex !== -1) {
          parentNode.children.splice(nodeIndex, 1);
        }
      });
    });
  };
};

export default remarkCodeTabs;
