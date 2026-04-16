import { useEffect, useState } from 'react';
import { useAuthStore } from '../../../store/authStore';
import { LoadingSpinner } from '../../../components/global/LoadingSpinner';
import { cn } from '../../../utils/cn';
import { getUserUsage } from '../../../services/api';

interface UsageDetail {
  used_today: number;
  limit_today: number;
  next_reset_kst: string;
}

interface UserUsageResponse {
  plan: string;
  features: {
    [key: string]: UsageDetail;
  };
}

export function AccountPage() {
  const { user } = useAuthStore();
  const [usage, setUsage] = useState<UserUsageResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const data = await getUserUsage<UserUsageResponse>();
        setUsage(data);
      } catch (error) {
        console.error('Failed to fetch usage:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchUsage();
  }, []);

  // Map backend features to UI labels
  const featureLabels: Record<string, string> = {
    text_generate: '관찰일지 생성',
    vision_analyze: '이미지/템플릿 분석',
  };

  const subscriptionData = {
    plan: usage?.plan ? usage.plan.charAt(0).toUpperCase() + usage.plan.slice(1) : 'Basic',
    renewalDate: '매월 1일', // Placeholder for actual subscription logic
    paymentMethod: {
      type: 'MasterCard',
      last4: '4892',
      expiry: '11/26'
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8 animate-view-enter">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-100">계정 설정</h1>
          <p className="text-zinc-500 dark:text-zinc-400 mt-1">계정 정보 및 서비스 이용 현황을 관리합니다.</p>
        </div>
      </div>

      {/* Profile Section */}
      <div className="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-zinc-100 dark:border-zinc-800 flex flex-col md:flex-row items-center gap-6">
        <div className="relative group">
          <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-[var(--color-primary-container)] shadow-inner">
            <img
              src={user?.email === 'user@example.com' ? "https://lh3.googleusercontent.com/aida-public/AB6AXuAUu-UvnXOZ2h4Yn67oztWuXr0wM-xtW9BUx39JfM970ZsFMNysq6KoE2tF1NgDJ8zioB43aS8Sz_1fwSHp_Qz41iWzlKM-n4IeHG9ULU8URNndx8Ed55zggbUa3MmlHofumoAl5w_1Jh2RfLou8-iSnvN0F7eXFMaEsGS8kfbn1kYTLYLOFcRmX8350DR32H_XoJHjolWsr_SQYlPqGzM9R0wfc3rPO3pNsiAzmEjfcrklksdDnZXc5RwkIlT2rIIJVKKAT1yoFw" : "https://lh3.googleusercontent.com/aida-public/AB6AXuDS50v-bDzSBnsD_Gk03h8AdlKkIL5blfFkaQM8sTQCpjtFG76R05j5PyBbAdpO5BerkfxKQc8-nWR_HwCzx4oij98fFmya331jHY7uLDrzSfEn1n8Pw8sJmgKH_MkWawcEoRbmPfoZeQKp-IrIC3oZWkh42jM9laLcYDK47FbYtDjZUWUYcEm6kd6K-eNNRQNbZtryPFZ7iWQbxHkA5oh7_OkYPRVg1M6r5SlCU4-MfZAR-m-9dDRL25T8_NbSI14zm8iJ9ru2Pw"}
              alt="Profile"
              className="w-full h-full object-cover transition-transform group-hover:scale-110"
            />
          </div>
          <button className="absolute bottom-0 right-0 bg-[var(--color-primary)] text-white p-1.5 rounded-full shadow-lg border-2 border-white dark:border-zinc-900 group-hover:scale-110 transition-transform">
            <span className="material-symbols-outlined text-sm">edit</span>
          </button>
        </div>
        
        <div className="flex-1 text-center md:text-left space-y-1">
          <h2 className="text-xl font-bold text-zinc-900 dark:text-zinc-100">{user?.name || user?.email?.split('@')[0]}님</h2>
          <p className="text-zinc-500 text-sm">{user?.email}</p>
          <div className="flex items-center justify-center md:justify-start gap-2 mt-2">
            <span className="px-3 py-1 bg-[var(--color-primary-container)] text-[var(--color-on-primary-container)] text-[10px] font-bold uppercase tracking-wider rounded-full">
              {user?.role || 'Educator'}
            </span>
          </div>
        </div>

        <div className="flex gap-2">
          <button className="px-4 py-2 text-sm font-semibold rounded-xl border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">
            프로필 수정
          </button>
          <button className="px-4 py-2 text-sm font-semibold text-white bg-[var(--color-primary)] rounded-xl hover:bg-[var(--color-primary-dim)] transition-colors shadow-md shadow-green-900/10">
            비밀번호 변경
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Subscription & Billing */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-zinc-100 dark:border-zinc-800 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <span className="material-symbols-outlined text-[var(--color-primary)]">card_membership</span>
              구독 및 결제
            </h3>
            <span className="text-xs font-semibold text-[var(--color-primary)] bg-[var(--color-primary-container)]/30 px-2 py-1 rounded-md">사용 중</span>
          </div>

          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-100 dark:border-zinc-800">
              <p className="text-xs text-zinc-500 uppercase tracking-wider mb-1">현재 플랜</p>
              <div className="flex items-center justify-between">
                <span className="text-lg font-bold text-[var(--color-primary)]">{subscriptionData.plan}</span>
                <span className="text-xs text-zinc-500">갱신일: {subscriptionData.renewalDate}</span>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-xs text-zinc-500 uppercase tracking-wider">결제 수단</p>
                <button className="text-xs font-bold text-[var(--color-primary)] hover:underline">상세 보기</button>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-8 bg-zinc-100 dark:bg-zinc-800 rounded flex items-center justify-center font-bold text-[10px] text-zinc-400">
                  {subscriptionData.paymentMethod.type}
                </div>
                <div>
                  <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">•••• •••• •••• {subscriptionData.paymentMethod.last4}</p>
                  <p className="text-[10px] text-zinc-500">만료일: {subscriptionData.paymentMethod.expiry}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button className="flex-1 px-4 py-3 text-sm font-semibold rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:scale-[1.02] transition-transform">
              플랜 관리
            </button>
            <button className="flex-1 px-4 py-3 text-sm font-semibold rounded-xl border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors">
              결제 수단 변경
            </button>
          </div>
        </div>

        {/* Usage & Quotas */}
        <div className="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-zinc-100 dark:border-zinc-800 md:p-8 relative overflow-hidden">
          <div className={cn("space-y-6 transition-all duration-300", !usage && loading && "blur-[2px] opacity-60 pointer-events-none")}>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold flex items-center gap-2">
                <span className="material-symbols-outlined text-[var(--color-primary)]">analytics</span>
                사용 현황 및 할당량
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Main AI Quota Circle (text_generate) */}
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="relative w-32 h-32">
                <svg className="w-full h-full -rotate-90 transform" viewBox="0 0 100 100">
                  <circle
                    className="text-zinc-100 dark:text-zinc-800"
                    strokeWidth="8"
                    stroke="currentColor"
                    fill="transparent"
                    r="40"
                    cx="50"
                    cy="50"
                  />
                  {usage?.features?.text_generate && (
                    <circle
                      className="text-[var(--color-primary)]"
                      strokeWidth="8"
                      strokeDasharray={2 * Math.PI * 40}
                      strokeDashoffset={2 * Math.PI * 40 * (1 - usage.features.text_generate.used_today / usage.features.text_generate.limit_today)}
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="transparent"
                      r="40"
                      cx="50"
                      cy="50"
                    />
                  )}
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                    {usage?.features?.text_generate ? `${usage.features.text_generate.used_today}/${usage.features.text_generate.limit_today}` : '--/--'}
                  </span>
                  <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-widest">오늘</span>
                </div>
              </div>
              <p className="text-sm font-bold text-zinc-700 dark:text-zinc-300">{featureLabels.text_generate}</p>
            </div>

            {/* Other AI features progress bars (vision_analyze etc) */}
            <div className="space-y-6 self-center">
              {Object.entries(usage?.features || {}).filter(([key]) => key !== 'text_generate').map(([key, feature]) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-zinc-500 uppercase tracking-tight">{featureLabels[key] || key}</span>
                    <span className="text-zinc-900 dark:text-zinc-100">{feature.used_today} / {feature.limit_today}</span>
                  </div>
                  <div className="h-3 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-1000"
                      style={{ width: `${(feature.used_today / feature.limit_today) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
            </div>
            
            <div className="p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-100 dark:border-zinc-800">
               <div className="flex items-start gap-3">
                 <span className="material-symbols-outlined text-zinc-400 text-sm mt-0.5">info</span>
                 <p className="text-[11px] text-zinc-500 leading-relaxed">
                   할당량은 매일 자정(KST)을 기준으로 초기화됩니다. 할당량이 부족할 경우 플랜을 업그레이드하여 한도를 늘릴 수 있습니다.
                 </p>
               </div>
            </div>
          </div>

          {/* Blur Overlay & Spinner */}
          {!usage && loading && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/40 dark:bg-zinc-900/40 backdrop-blur-[2px]">
              <div className="flex flex-col items-center gap-4">
                <LoadingSpinner size="xl" />
                <span className="text-sm font-bold text-zinc-600 dark:text-zinc-300 animate-pulse tracking-tight">정보를 불러오는 중...</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Danger Zone */}
      <div className="border border-red-100 dark:border-red-900/30 rounded-3xl p-6 bg-red-50/30 dark:bg-red-950/10">
        <h3 className="text-lg font-bold text-red-700 dark:text-red-400 mb-4">계정 삭제</h3>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mb-6 font-medium">
          계정을 삭제하면 모든 관찰 기록 및 관련 데이터가 영구적으로 제거됩니다. 이 작업은 되돌릴 수 없습니다.
        </p>
        <button className="px-6 py-2 text-sm font-bold text-red-600 border border-red-200 bg-white hover:bg-red-50 rounded-xl transition-all shadow-sm">
          서비스 탈퇴
        </button>
      </div>
    </div>
  );
}
