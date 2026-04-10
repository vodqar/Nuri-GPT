import type { Template, GenerateLogResponse } from '../../types/api';

export const CHEAT_SAMPLE_RESULT: GenerateLogResponse = {
  status: 'success',
  message: '치트 모드: 샘플 데이터',
  updated_activities: [
    { target_id: '보육일지.놀이.활동.내용', updated_text: '종이의 질감을 탐색하고 접는 과정을 통해 소근육을 정교하게 조절하며, 다양한 형태를 구성해보는 조형 활동을 진행함.' },
    { target_id: '보육일지.놀이.실내놀이.놀이상황', updated_text: '다양한 크기의 블록을 활용하여 높이 쌓거나 구조물을 만드는 놀이에 몰입함. 블록의 균형을 맞추며 성취감을 느끼고 자신의 생각을 입체적으로 표현하는 모습이 관찰됨.' },
    { target_id: '보육일지.놀이.실내놀이.놀이지원', updated_text: '영유아가 블록 놀이에 충분히 몰입하고 창의적인 구조물을 구성할 수 있도록 놀이 공간을 확장하여 안전하고 여유로운 환경을 조성함.' },
    { target_id: '보육일지.놀이.바깥놀이(대체).놀이상황', updated_text: '자연물을 탐색하며 낙엽의 색깔과 모양 변화에 관심을 보임. 떨어진 낙엽을 주워 모으고 분류해보는 과정을 통해 계절의 변화를 감각적으로 경험함.' },
    { target_id: '보육일지.일상생활.간식', updated_text: '제철 과일을 제공하여 다양한 맛과 식감을 경험함. 스스로 포크를 사용하여 간식을 섭취하며 식사 예절과 자조 능력을 기르는 시간을 가짐.' },
    { target_id: '보육일지.일상생활.점심식사', updated_text: '자신의 식판에 적정량의 음식을 스스로 배식보며 자립심을 기르는 연습을 함. 배식 과정에서 질서를 지키고 차례를 기다리는 태도를 격려함.' },
    { target_id: '보육일지.일상생활.낮잠 및 휴식', updated_text: '심리적 안정감을 제공하기 위해 클래식 음악을 배경으로 휴식을 취함. 조용한 환경 속에서 신체적 긴장을 완화하고 에너지를 회복함.' },
    { target_id: '보육일지.통합보육.등원', updated_text: '등원하는 영유아를 밝게 맞이하며 개별적인 기분과 컨디션을 세심하게 살피고, 보호자와 긴밀하게 소통하며 안정적인 일과 시작을 도움.' },
    { target_id: '보육일지.통합보육.하원', updated_text: '소지품을 스스로 챙겨 하원할 수 있도록 격려하며, 안전하게 귀가할 수 있도록 보호자에게 당부 사항을 전달하고 긍정적인 상호작용으로 하루를 마무리함.' },
    { target_id: '보육일지.반 운영 특이사항', updated_text: '영유아가 사용하는 교구 및 비품을 주기적으로 소독하여 청결하고 안전한 보육 환경을 유지함.' },
    { target_id: '보육일지.놀이 평가 및 다음날 지원 계획', updated_text: '영유아가 현재 놀이에 지속적인 흥미를 보이고 있음. 놀이의 확장과 심화를 돕기 위해 관련 재료를 추가로 제공하여 창의적인 표현 활동이 더욱 풍성하게 이루어지도록 지원할 계획임.' },
  ] as Record<string, unknown>[],
};

export const CHEAT_SAMPLE_TEMPLATE: Template = {
  id: 'cheat-template-id',
  name: '치트 템플릿',
  user_id: 'cheat-user',
  template_type: 'daily_log',
  structure_json: {},
  is_default: false,
  sort_order: 0,
  is_active: true,
  created_at: new Date().toISOString(),
  semantic_json: {
    title: '보육일지',
    children: [
      {
        title: '놀이',
        children: [
          { title: '활동', children: [{ title: '내용', format: 'text' }] },
          { title: '실내놀이', children: [{ title: '놀이상황', format: 'text' }, { title: '놀이지원', format: 'text' }] },
          { title: '바깥놀이(대체)', children: [{ title: '놀이상황', format: 'text' }] },
        ],
      },
      {
        title: '일상생활',
        children: [
          { title: '간식', format: 'text' },
          { title: '점심식사', format: 'text' },
          { title: '낮잠 및 휴식', format: 'text' },
        ],
      },
      {
        title: '통합보육',
        children: [{ title: '등원', format: 'text' }, { title: '하원', format: 'text' }],
      },
      { title: '반 운영 특이사항', format: 'text' },
      { title: '놀이 평가 및 다음날 지원 계획', format: 'text' },
    ],
  },
};

export function isCheatMode(): boolean {
  const params = new URLSearchParams(window.location.search);
  return params.get('cheat') === 'regenerate';
}
