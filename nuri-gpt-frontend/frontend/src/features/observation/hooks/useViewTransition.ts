import { useState, useCallback } from 'react';

// 하위 호환성을 위해 기본 제네릭 타입을 지정할 수 있으나, 명시적으로 제네릭 사용
export function useViewTransition<T extends string>(initialState: T) {
  const [viewState, setViewState] = useState<T>(initialState);
  const [exitingView, setExitingView] = useState<T | null>(null);

  const transitionTo = useCallback(
    (newView: T) => {
      if (viewState === newView) return;

      setExitingView(viewState);
      // Exit 애니메이션 완료 후 실제 전환
      setTimeout(() => {
        setViewState(newView);
        setExitingView(null);
      }, 200); // exit duration
    },
    [viewState]
  );

  return {
    viewState,
    exitingView,
    transitionTo,
  };
}
