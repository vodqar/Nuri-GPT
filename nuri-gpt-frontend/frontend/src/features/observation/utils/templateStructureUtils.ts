export interface FlatItem {
  id: string;
  label: string;
  depth: number;
}

// 카드 UI용 트리 노드 타입
export interface TreeNode {
  id: string;
  label: string;
  children: TreeNode[];
}

export const MAX_DEPTH = 4;
export const MAX_DEPTH_CARD = 2; // 카드 UI: 대분류(0) → 소분류(1) → 항목(2)

/**
 * FlatItem 배열 → structure_json 트리 변환
 * depth 기반으로 부모-자식 관계를 복원한다.
 * leaf 노드(자식 없는 항목)의 value는 "".
 */
export function flatToTree(items: FlatItem[]): Record<string, unknown> {
  if (items.length === 0) return {};

  const root: Record<string, unknown> = {};
  // 각 depth별 현재 컨텍스트 노드를 추적
  const stack: Record<string, unknown>[] = [root];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const nextItem = items[i + 1];
    const hasChild = nextItem !== undefined && nextItem.depth > item.depth;

    // depth에 맞는 부모 노드 선택
    const parent = stack[item.depth];

    if (hasChild) {
      // 자식이 있으면 객체 노드
      const node: Record<string, unknown> = {};
      parent[item.label] = node;
      stack[item.depth + 1] = node;
    } else {
      // leaf 노드
      parent[item.label] = '';
    }
  }

  return root;
}

/**
 * structure_json 트리 → FlatItem 배열 변환
 * 재귀적으로 순회하며 depth와 label을 기록한다.
 */
export function treeToFlat(tree: Record<string, unknown>, depth = 0): FlatItem[] {
  const result: FlatItem[] = [];

  for (const [key, value] of Object.entries(tree)) {
    result.push({ id: crypto.randomUUID(), label: key, depth });
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      result.push(...treeToFlat(value as Record<string, unknown>, depth + 1));
    }
  }

  return result;
}

/**
 * 새 FlatItem 생성 헬퍼
 */
export function createFlatItem(label = '', depth = 0): FlatItem {
  return { id: crypto.randomUUID(), label, depth };
}

/**
 * 새 TreeNode 생성 헬퍼
 */
export function createTreeNode(label = ''): TreeNode {
  return { id: crypto.randomUUID(), label, children: [] };
}

/**
 * structure_json (API 응답) → TreeNode[] 변환
 * 최대 3단계 (대분류→소분류→항목) 까지만 지원
 */
export function structureToTreeNodes(structure: Record<string, unknown>): TreeNode[] {
  const nodes: TreeNode[] = [];

  for (const [key, value] of Object.entries(structure)) {
    const node = createTreeNode(key);

    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      // 소분류 레벨 (depth 1)
      for (const [subKey, subValue] of Object.entries(value as Record<string, unknown>)) {
        const subNode = createTreeNode(subKey);

        if (typeof subValue === 'object' && subValue !== null && !Array.isArray(subValue)) {
          // 항목 레벨 (depth 2) - 더 깊은 계층은 무시하고 leaf로 처리
          for (const [itemKey] of Object.entries(subValue as Record<string, unknown>)) {
            subNode.children.push(createTreeNode(itemKey));
          }
        }
        // subValue가 leaf면 subNode는 children 없이 항목 자체
        node.children.push(subNode);
      }
    }
    // value가 leaf면 node는 children 없이 항목 자체

    nodes.push(node);
  }

  return nodes;
}

/**
 * TreeNode[] → structure_json (API 요청용) 변환
 */
export function treeNodesToStructure(nodes: TreeNode[]): Record<string, unknown> {
  const structure: Record<string, unknown> = {};

  for (const node of nodes) {
    if (node.children.length === 0) {
      // leaf 항목
      structure[node.label] = '';
    } else {
      const subStructure: Record<string, unknown> = {};
      for (const child of node.children) {
        if (child.children.length === 0) {
          subStructure[child.label] = '';
        } else {
          const itemStructure: Record<string, unknown> = {};
          for (const grandChild of child.children) {
            itemStructure[grandChild.label] = '';
          }
          subStructure[child.label] = itemStructure;
        }
      }
      structure[node.label] = subStructure;
    }
  }

  return structure;
}
