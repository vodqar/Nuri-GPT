/**
 * Flattened Key (e.g., "놀이.실내놀이.놀이상황")를 중첩된 JSON 객체로 변환합니다.
 * @param flatObject - 평탄화된 객체 (키는 점(.)으로 구분된 경로)
 * @returns 중첩된 JSON 객체
 */
export function unflattenObject(flatObject: Record<string, string>): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  for (const [flatKey, value] of Object.entries(flatObject)) {
    const keys = flatKey.split('.');
    let current = result;

    for (let i = 0; i < keys.length; i++) {
      const key = keys[i];
      
      if (i === keys.length - 1) {
        // 마지막 키 - 값 설정
        current[key] = value;
      } else {
        // 중간 키 - 객체 생성
        if (!(key in current)) {
          current[key] = {};
        }
        current = current[key] as Record<string, unknown>;
      }
    }
  }

  return result;
}

/**
 * 객체가 비어있는지 확인합니다.
 * @param obj - 검사할 객체
 * @returns 비어있으면 true, 아니면 false
 */
export function isEmptyObject(obj: Record<string, unknown>): boolean {
  return Object.keys(obj).length === 0;
}

export interface FlatField {
  path: string[];
  value: string;
  flatKey: string;
}

export const getFlatFields = (data: Record<string, unknown>, currentPath: string[] = []): FlatField[] => {
  let fields: FlatField[] = [];
  if (typeof data === 'object' && data !== null && !Array.isArray(data)) {
    for (const [key, value] of Object.entries(data)) {
      const newPath = [...currentPath, key];
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        fields = [...fields, ...getFlatFields(value as Record<string, unknown>, newPath)];
      } else {
        fields.push({
          path: newPath,
          value: Array.isArray(value) ? value.join(', ') : String(value),
          flatKey: newPath.join('.'),
        });
      }
    }
  }
  return fields;
};

// 요일 필드 관련 상수 및 타입
export const DAYS = ['월요일', '화요일', '수요일', '목요일', '금요일'] as const;
export type Day = typeof DAYS[number];

// 요일 그룹핑 결과 타입
export interface CategoryGroup {
  path: string[]; // 중분류까지의 경로
  days: Map<Day, FlatField[]>; // 요일별 필드
}

export interface DayGroupedResult {
  regularFields: FlatField[]; // 요일이 아닌 일반 필드
  categoryGroups: Map<string, CategoryGroup>; // 중분류 경로 -> 그룹
}

/**
 * 플랫 필드를 중분류 기준 요일별로 그룹핑합니다.
 * @param fields - getFlatFields 결과
 * @returns 요일별 그룹핑 결과
 */
export function groupFieldsByCategoryAndDay(fields: FlatField[]): DayGroupedResult {
  const regularFields: FlatField[] = [];
  const categoryGroups = new Map<string, CategoryGroup>();

  for (const field of fields) {
    const lastSegment = field.path[field.path.length - 1];

    // 요일 필드인지 확인
    if (DAYS.includes(lastSegment as Day)) {
      // 중분류 경로 = 마지막-1까지 (예: ["계획 및 실행", "일상생활", "간식"])
      const categoryPath = field.path.slice(0, -1);
      const categoryKey = categoryPath.join('.');
      const day = lastSegment as Day;

      // 중분류 그룹 가져오거나 생성
      let group = categoryGroups.get(categoryKey);
      if (!group) {
        group = {
          path: categoryPath,
          days: new Map<Day, FlatField[]>(),
        };
        categoryGroups.set(categoryKey, group);
      }

      // 요일별 필드 추가
      const dayFields = group.days.get(day) || [];
      dayFields.push(field);
      group.days.set(day, dayFields);
    } else {
      // 일반 필드
      regularFields.push(field);
    }
  }

  return { regularFields, categoryGroups };
}
