import { useState, useEffect, useCallback } from 'react';
import { ArrowUp } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ScrollToTopProps {
  threshold?: number;
  targetSelector?: string;
}

export function ScrollToTop({ threshold = 200, targetSelector }: ScrollToTopProps) {
  const [isVisible, setIsVisible] = useState(false);

  const checkScroll = useCallback(() => {
    if (targetSelector) {
      const target = document.querySelector(targetSelector);
      if (target) {
        setIsVisible(target.scrollTop > threshold);
      }
    } else {
      setIsVisible(window.scrollY > threshold);
    }
  }, [threshold, targetSelector]);

  useEffect(() => {
    const scrollTarget = targetSelector
      ? document.querySelector(targetSelector)
      : window;

    if (scrollTarget) {
      scrollTarget.addEventListener('scroll', checkScroll, { passive: true });
      // eslint-disable-next-line react-hooks/set-state-in-effect
      checkScroll(); // 초기 체크
    }

    return () => {
      if (scrollTarget) {
        scrollTarget.removeEventListener('scroll', checkScroll);
      }
    };
  }, [checkScroll, targetSelector]);

  const scrollToTop = () => {
    if (targetSelector) {
      const target = document.querySelector(targetSelector);
      if (target) {
        target.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  return (
    <button
      onClick={scrollToTop}
      className={cn('scroll-top-btn', isVisible && 'visible')}
      aria-label="맨 위로 스크롤"
      title="맨 위로"
    >
      <ArrowUp className="w-5 h-5" />
    </button>
  );
}
