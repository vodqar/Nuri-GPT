import React from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-gray-50 text-gray-900">
          <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 max-w-md w-full text-center space-y-4">
            <h2 className="text-xl font-bold text-red-600">문제가 발생했습니다</h2>
            <p className="text-sm text-gray-600">
              일시적인 오류가 발생했습니다. 다시 시도해주세요.
            </p>
            {import.meta.env.DEV && this.state.error && (
              <pre className="text-xs text-left bg-gray-100 p-3 rounded-lg overflow-auto mt-4 max-h-40">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              className="mt-6 w-full py-3 px-4 text-white font-bold rounded-xl transition-colors"
              style={{ backgroundColor: 'var(--color-primary)' }}
            >
              다시 시도
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
