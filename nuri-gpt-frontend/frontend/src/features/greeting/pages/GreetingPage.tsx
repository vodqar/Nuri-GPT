import { useState, useEffect } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { GreetingService } from '../services/greetingService';
import { useGreeting } from '../hooks/useGreeting';
import { LoadingSpinner } from '../../../components/global/LoadingSpinner';
import { Search, Calendar, Copy, RefreshCw, Check, MapPin, Info, MessageSquarePlus, User, Smile } from 'lucide-react';
import { cn } from '../../../utils/cn';

export default function GreetingPage() {
  const { accessToken, user } = useAuthStore();
  const { isGenerating, result, error, generateGreeting } = useGreeting();
  
  const [regions, setRegions] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isRegionListOpen, setIsRegionListOpen] = useState(false);
  
  const [selectedRegion, setSelectedRegion] = useState(user?.preferred_region || '');
  const [targetDate, setTargetDate] = useState(new Date().toISOString().split('T')[0]);
  const [enabledContexts, setEnabledContexts] = useState<string[]>(['weather', 'seasonal', 'holiday', 'week']);
  const [userInput, setUserInput] = useState('');
  const [nameInput, setNameInput] = useState(false);
  const [useEmoji, setUseEmoji] = useState(true);
  const [copySuccess, setCopySuccess] = useState(false);

  // Fetch regions on mount
  useEffect(() => {
    const fetchRegions = async () => {
      if (!accessToken) return;
      try {
        const data = await GreetingService.getRegions(accessToken);
        setRegions(data);
      } catch (err) {
        console.error('Failed to fetch regions:', err);
      }
    };
    fetchRegions();
  }, [accessToken]);

  // Sync selectedRegion with user preferred region if it changes
  useEffect(() => {
    if (user?.preferred_region && !selectedRegion) {
      setSelectedRegion(user.preferred_region);
    }
  }, [user?.preferred_region, selectedRegion]);

  const filteredRegions = regions.filter(r => 
    r.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + 10);
  const maxDateStr = maxDate.toISOString().split('T')[0];
  const minDateStr = new Date().toISOString().split('T')[0];

  const handleContextToggle = (context: string) => {
    setEnabledContexts(prev => 
      prev.includes(context) 
        ? prev.filter(c => c !== context)
        : [...prev, context]
    );
  };

  const handleGenerate = () => {
    if (!selectedRegion) return;
    generateGreeting({
      region: selectedRegion,
      target_date: targetDate,
      user_input: userInput,
      enabled_contexts: enabledContexts,
      name_input: nameInput,
      use_emoji: useEmoji,
    });
  };

  const handleCopy = async () => {
    if (result) {
      try {
        await navigator.clipboard.writeText(result);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      } catch (err) {
        console.error('Failed to copy text:', err);
        // Fallback: try using document.execCommand
        const textArea = document.createElement('textarea');
        textArea.value = result;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
          document.execCommand('copy');
          setCopySuccess(true);
          setTimeout(() => setCopySuccess(false), 2000);
        } catch (fallbackErr) {
          console.error('Fallback copy also failed:', fallbackErr);
          alert('복사에 실패했습니다. 수동으로 복사해주세요.');
        }
        document.body.removeChild(textArea);
      }
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8 animate-view-enter">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-100">알림장 인삿말 생성</h1>
        <p className="text-zinc-500 dark:text-zinc-400 mt-1">지역 날씨와 날짜 맥락을 담은 따뜻한 인삿말을 만들어보세요.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Input Section */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-zinc-100 dark:border-zinc-800 space-y-6">
          {/* Region Selection */}
          <div className="space-y-2 relative">
            <label className="text-sm font-bold flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
              <MapPin className="w-4 h-4 text-[var(--color-primary)]" />
              1. 지역 선택
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                <Search className="w-4 h-4 text-zinc-400" />
              </div>
              <input
                type="text"
                placeholder="시군구 검색 (예: 강남구)"
                className="w-full pl-10 pr-4 py-3 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-100 dark:border-zinc-800 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] transition-all"
                value={isRegionListOpen ? searchQuery : selectedRegion}
                onFocus={() => {
                  setIsRegionListOpen(true);
                  setSearchQuery('');
                }}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {isRegionListOpen && (
                <div className="absolute z-50 w-full mt-2 bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 rounded-2xl shadow-xl max-h-60 overflow-y-auto overflow-x-hidden animate-in fade-in zoom-in duration-200">
                  {filteredRegions.length > 0 ? (
                    filteredRegions.map((r) => (
                      <button
                        key={r}
                        className="w-full text-left px-4 py-3 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors flex items-center justify-between group"
                        onClick={() => {
                          setSelectedRegion(r);
                          setIsRegionListOpen(false);
                          setSearchQuery('');
                        }}
                      >
                        <span className="text-sm font-medium text-zinc-700 dark:text-zinc-300 group-hover:text-[var(--color-primary)]">{r}</span>
                        {selectedRegion === r && <Check className="w-4 h-4 text-[var(--color-primary)]" />}
                      </button>
                    ))
                  ) : (
                    <div className="px-4 py-8 text-center text-zinc-500 text-sm">검색 결과가 없습니다.</div>
                  )}
                </div>
              )}
            </div>
            {isRegionListOpen && (
              <div 
                className="fixed inset-0 z-40" 
                onClick={() => setIsRegionListOpen(false)} 
              />
            )}
            {user?.preferred_region && (
              <p className="text-[11px] text-zinc-400 flex items-center gap-1 pl-1">
                <Info className="w-3 h-3" />
                최근 선택: {user.preferred_region}
              </p>
            )}
          </div>

          {/* Date Selection */}
          <div className="space-y-2">
            <label className="text-sm font-bold flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
              <Calendar className="w-4 h-4 text-[var(--color-primary)]" />
              2. 날짜 선택
            </label>
            <div className="relative">
              <input
                type="date"
                min={minDateStr}
                max={maxDateStr}
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-100 dark:border-zinc-800 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] transition-all"
              />
            </div>
            <p className="text-[11px] text-zinc-400 flex items-center gap-1 pl-1">
              <Info className="w-3 h-3" />
              오늘부터 최대 10일 후까지만 선택 가능합니다.
            </p>
          </div>

          {/* Context Options */}
          <div className="space-y-3">
            <label className="text-sm font-bold flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
              <Check className="w-4 h-4 text-[var(--color-primary)]" />
              3. 포함할 내용 (맥락)
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'weather', label: '날씨 정보' },
                { id: 'seasonal', label: '절기 정보' },
                { id: 'holiday', label: '공휴일/기념일' },
                { id: 'week', label: '주차 정보' },
              ].map((ctx) => (
                <button
                  key={ctx.id}
                  onClick={() => handleContextToggle(ctx.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 rounded-2xl border transition-all text-sm font-medium",
                    enabledContexts.includes(ctx.id)
                      ? "bg-[var(--color-primary-container)] border-[var(--color-primary)] text-[var(--color-on-primary-container)]"
                      : "bg-white dark:bg-zinc-900 border-zinc-100 dark:border-zinc-800 text-zinc-500 hover:border-zinc-300"
                  )}
                >
                  <div className={cn(
                    "w-4 h-4 rounded-md flex items-center justify-center border",
                    enabledContexts.includes(ctx.id) ? "bg-[var(--color-primary)] border-[var(--color-primary)]" : "border-zinc-300"
                  )}>
                    {enabledContexts.includes(ctx.id) && <Check className="w-3 h-3 text-white" />}
                  </div>
                  {ctx.label}
                </button>
              ))}
            </div>
          </div>

          {/* Greeting Options */}
          <div className="space-y-3">
            <label className="text-sm font-bold flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
              <Smile className="w-4 h-4 text-[var(--color-primary)]" />
              4. 인삿말 옵션
            </label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'nameInput' as const, label: '이름 삽입', desc: '개별 아동용', icon: User, state: nameInput, setter: setNameInput },
                { id: 'useEmoji' as const, label: '이모지 사용', desc: '차분한 톤', icon: Smile, state: useEmoji, setter: setUseEmoji },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => opt.setter(!opt.state)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 rounded-2xl border transition-all text-sm font-medium",
                    opt.state
                      ? "bg-[var(--color-primary-container)] border-[var(--color-primary)] text-[var(--color-on-primary-container)]"
                      : "bg-white dark:bg-zinc-900 border-zinc-100 dark:border-zinc-800 text-zinc-500 hover:border-zinc-300"
                  )}
                >
                  <div className={cn(
                    "w-4 h-4 rounded-md flex items-center justify-center border",
                    opt.state ? "bg-[var(--color-primary)] border-[var(--color-primary)]" : "border-zinc-300"
                  )}>
                    {opt.state && <Check className="w-3 h-3 text-white" />}
                  </div>
                  <div className="flex flex-col items-start">
                    <span>{opt.label}</span>
                    <span className="text-[10px] text-zinc-400 font-normal">{opt.state ? (opt.id === 'nameInput' ? '예: 우리 [이름]이가' : '이모지 포함') : (opt.id === 'nameInput' ? '반 전체 지칭' : opt.desc)}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* User Input */}
          <div className="space-y-2">
            <label className="text-sm font-bold flex items-center gap-2 text-zinc-700 dark:text-zinc-300">
              <MessageSquarePlus className="w-4 h-4 text-[var(--color-primary)]" />
              5. 추가 요구사항 (선택)
            </label>
            <textarea
              placeholder="예: 아이들이 소풍을 가는 날임을 언급해줘, 비타민 같은 하루 보내라는 말 넣어줘 등"
              className="w-full px-4 py-3 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-100 dark:border-zinc-800 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] transition-all min-h-[100px] resize-none text-sm"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
            />
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !selectedRegion}
            className={cn(
              "w-full py-4 rounded-2xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg",
              isGenerating || !selectedRegion
                ? "bg-zinc-100 text-zinc-400 cursor-not-allowed shadow-none"
                : "bg-[var(--color-primary)] text-white hover:scale-[1.02] active:scale-[0.98]"
            )}
          >
            {isGenerating ? (
              <>
                <LoadingSpinner size="sm" color="white" />
                인삿말 생성 중...
              </>
            ) : (
              <>
                <RefreshCw className="w-5 h-5" />
                인삿말 생성하기
              </>
            )}
          </button>
        </div>

        {/* Result Section */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-zinc-100 dark:border-zinc-800 flex flex-col min-h-[560px]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-[var(--color-primary)]" />
              생성 결과
            </h3>
            {result && (
              <div className="flex gap-2">
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-xl text-xs font-bold hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all"
                >
                  {copySuccess ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-green-600" />
                      복사됨!
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      복사하기
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          <div className="flex-1 bg-zinc-50 dark:bg-zinc-950 rounded-2xl border border-dashed border-zinc-200 dark:border-zinc-800 p-6 relative">
            {isGenerating ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center space-y-4">
                <LoadingSpinner size="xl" />
                <p className="text-zinc-500 font-medium animate-pulse">날씨와 맥락을 분석하여 작성 중입니다...</p>
              </div>
            ) : result ? (
              <div className="prose dark:prose-invert max-w-none">
                <p className="text-zinc-800 dark:text-zinc-200 leading-relaxed whitespace-pre-wrap">
                  {result}
                </p>
              </div>
            ) : error ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <span className="text-red-600 font-bold text-xl">!</span>
                </div>
                <p className="text-red-600 font-bold">{error}</p>
                <button 
                  onClick={handleGenerate}
                  className="text-sm font-bold text-zinc-500 underline underline-offset-4 hover:text-zinc-900"
                >
                  다시 시도하기
                </button>
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center space-y-4 opacity-50">
                <div className="w-16 h-16 rounded-full bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center">
                  <MessageSquarePlus className="w-8 h-8 text-zinc-300" />
                </div>
                <p className="text-zinc-500 font-medium leading-relaxed">
                  지역과 날짜를 선택한 후<br />'인삿말 생성하기' 버튼을 눌러주세요.
                </p>
              </div>
            )}
          </div>

          {result && (
            <div className="mt-6 p-4 rounded-2xl bg-[var(--color-primary-container)]/20 border border-[var(--color-primary)]/10">
              <p className="text-xs text-[var(--color-primary)] leading-relaxed font-medium">
                Tip: 생성된 인삿말이 마음에 들지 않는다면 '추가 요구사항'을 적고 다시 생성해보세요!
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
