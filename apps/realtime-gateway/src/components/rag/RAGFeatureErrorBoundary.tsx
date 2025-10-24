/**
 * RAG Feature Error Boundary Component
 * Catches and displays user-friendly errors for RAG feature operations
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  AlertCircle, 
  RefreshCw, 
  Home, 
  Settings, 
  Bug,
  Copy,
  CheckCircle
} from 'lucide-react';

// ==================== TYPES ====================

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  className?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string;
  copied: boolean;
}

// ==================== COMPONENT IMPLEMENTATION ====================

export class RAGFeatureErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      copied: false
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate unique error ID for tracking
    const errorId = `rag-error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    return {
      hasError: true,
      error,
      errorId
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details
    console.error('RAG Feature Error Boundary caught an error:', error, errorInfo);
    
    // Update state with error info
    this.setState({
      error,
      errorInfo
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to send this to an error reporting service
    this.reportError(error, errorInfo);
  }

  private reportError = (error: Error, errorInfo: ErrorInfo) => {
    // This would typically send to an error reporting service like Sentry
    const errorReport = {
      errorId: this.state.errorId,
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // For now, just log to console
    console.error('Error Report:', errorReport);
  };

  private handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: '',
      copied: false
    });
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private handleGoToSettings = () => {
    window.location.href = '/admin/rag-features';
  };

  private handleCopyError = async () => {
    const errorDetails = this.getErrorDetails();
    try {
      await navigator.clipboard.writeText(errorDetails);
      this.setState({ copied: true });
      setTimeout(() => this.setState({ copied: false }), 2000);
    } catch (err) {
      console.error('Failed to copy error details:', err);
    }
  };

  private getErrorDetails = (): string => {
    const { error, errorInfo, errorId } = this.state;
    return `
RAG Feature Error Report
Error ID: ${errorId}
Timestamp: ${new Date().toISOString()}
URL: ${window.location.href}

Error Message:
${error?.message || 'Unknown error'}

Error Stack:
${error?.stack || 'No stack trace available'}

Component Stack:
${errorInfo?.componentStack || 'No component stack available'}

User Agent:
${navigator.userAgent}
    `.trim();
  };

  private getErrorType = (error: Error): string => {
    const message = error.message.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch')) {
      return 'Network Error';
    }
    if (message.includes('permission') || message.includes('forbidden')) {
      return 'Permission Error';
    }
    if (message.includes('validation') || message.includes('invalid')) {
      return 'Validation Error';
    }
    if (message.includes('feature') && message.includes('not enabled')) {
      return 'Feature Not Enabled';
    }
    if (message.includes('organization') && message.includes('not found')) {
      return 'Organization Error';
    }
    if (message.includes('inheritance') || message.includes('parent')) {
      return 'Inheritance Error';
    }
    
    return 'Unknown Error';
  };

  private getErrorSuggestions = (error: Error): string[] => {
    const message = error.message.toLowerCase();
    const suggestions: string[] = [];

    if (message.includes('network') || message.includes('fetch')) {
      suggestions.push('Check your internet connection');
      suggestions.push('Try refreshing the page');
      suggestions.push('Contact support if the problem persists');
    } else if (message.includes('permission') || message.includes('forbidden')) {
      suggestions.push('Check if you have the required permissions');
      suggestions.push('Contact your organization administrator');
      suggestions.push('Verify your user role and access level');
    } else if (message.includes('validation') || message.includes('invalid')) {
      suggestions.push('Check your input data for errors');
      suggestions.push('Ensure all required fields are filled');
      suggestions.push('Verify the format of your data');
    } else if (message.includes('feature') && message.includes('not enabled')) {
      suggestions.push('Contact your organization administrator to enable this feature');
      suggestions.push('Check if the feature is available for your organization');
      suggestions.push('Verify your organization\'s RAG feature settings');
    } else if (message.includes('organization') && message.includes('not found')) {
      suggestions.push('Verify your organization ID');
      suggestions.push('Contact support to check your organization status');
      suggestions.push('Ensure you\'re logged in with the correct account');
    } else if (message.includes('inheritance') || message.includes('parent')) {
      suggestions.push('Check your organization hierarchy settings');
      suggestions.push('Contact your parent organization administrator');
      suggestions.push('Verify inheritance rules and permissions');
    } else {
      suggestions.push('Try refreshing the page');
      suggestions.push('Check your internet connection');
      suggestions.push('Contact support if the problem persists');
    }

    return suggestions;
  };

  render() {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const { error, errorId } = this.state;
      const errorType = error ? this.getErrorType(error) : 'Unknown Error';
      const suggestions = error ? this.getErrorSuggestions(error) : [];

      return (
        <div className={`min-h-screen bg-gray-100 flex items-center justify-center p-4 ${this.props.className || ''}`}>
          <Card className="max-w-2xl w-full p-6">
            <div className="text-center">
              {/* Error Icon */}
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <AlertCircle className="h-6 w-6 text-red-600" />
              </div>

              {/* Error Title */}
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                RAG Feature Error
              </h1>
              
              <p className="text-lg text-gray-600 mb-4">
                {errorType}
              </p>

              {/* Error Message */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                  <p className="text-red-800 font-medium mb-2">Error Details:</p>
                  <p className="text-red-700 text-sm">
                    {error.message}
                  </p>
                </div>
              )}

              {/* Error ID */}
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-6">
                <p className="text-sm text-gray-600 mb-1">Error ID:</p>
                <p className="font-mono text-sm text-gray-800 break-all">
                  {errorId}
                </p>
              </div>

              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div className="text-left mb-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">What you can try:</h3>
                  <ul className="space-y-2">
                    {suggestions.map((suggestion, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-gray-700">{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button
                  onClick={this.handleRetry}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>

                <Button
                  variant="outline"
                  onClick={this.handleGoToSettings}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  RAG Settings
                </Button>

                <Button
                  variant="outline"
                  onClick={this.handleGoHome}
                >
                  <Home className="h-4 w-4 mr-2" />
                  Go Home
                </Button>
              </div>

              {/* Technical Details */}
              {this.props.showDetails && error && (
                <div className="mt-8 text-left">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-medium text-gray-900">Technical Details</h3>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={this.handleCopyError}
                      className="text-xs"
                    >
                      {this.state.copied ? (
                        <>
                          <CheckCircle className="h-3 w-3 mr-1" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3 mr-1" />
                          Copy Details
                        </>
                      )}
                    </Button>
                  </div>
                  
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs overflow-auto max-h-64">
                    <pre>{this.getErrorDetails()}</pre>
                  </div>
                </div>
              )}

              {/* Support Information */}
              <div className="mt-8 pt-6 border-t border-gray-200">
                <p className="text-sm text-gray-500">
                  If this problem continues, please contact support with the Error ID above.
                </p>
                <div className="flex items-center justify-center space-x-4 mt-2 text-xs text-gray-400">
                  <span>Error ID: {errorId}</span>
                  <span>•</span>
                  <span>{new Date().toLocaleString()}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// ==================== FUNCTIONAL WRAPPER ====================

interface RAGFeatureErrorBoundaryWrapperProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
  className?: string;
}

export const RAGFeatureErrorBoundaryWrapper: React.FC<RAGFeatureErrorBoundaryWrapperProps> = (props) => {
  return <RAGFeatureErrorBoundary {...props} />;
};

// ==================== HOOK FOR ERROR HANDLING ====================

export const useRAGFeatureErrorHandler = () => {
  const handleError = (error: Error, context?: string) => {
    console.error(`RAG Feature Error${context ? ` in ${context}` : ''}:`, error);
    
    // You could integrate with error reporting services here
    // Example: Sentry.captureException(error, { tags: { context } });
  };

  const handleAsyncError = (error: unknown, context?: string) => {
    if (error instanceof Error) {
      handleError(error, context);
    } else {
      console.error(`RAG Feature Async Error${context ? ` in ${context}` : ''}:`, error);
    }
  };

  return {
    handleError,
    handleAsyncError
  };
};

// ==================== EXPORTS ====================

export default RAGFeatureErrorBoundary;
