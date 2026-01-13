import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExplainButton } from '@/components/ExplainButton';
import { api, APIError } from '@/lib/api';
import { BriefResponse } from '@/lib/types';
import { useRouter } from 'next/navigation';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock API client
jest.mock('@/lib/api', () => ({
  api: {
    generateTrendBrief: jest.fn(),
  },
  APIError: class APIError extends Error {
    constructor(public status: number, message: string) {
      super(message);
      this.name = 'APIError';
    }
  },
}));

const mockRouter = {
  push: jest.fn(),
  refresh: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  prefetch: jest.fn(),
  replace: jest.fn(),
};

describe('ExplainButton Component', () => {
  const mockToken = 'test-jwt-token';
  const mockTrendId = '123e4567-e89b-12d3-a456-426614174000';
  const mockBrief: BriefResponse = {
    ai_brief: 'Test brief. This is trending. Popular on Reddit.',
    generated_at: '2026-01-13T10:00:00Z',
    cached: false,
  };

  const mockOnBriefGenerated = jest.fn();
  const mockOnError = jest.fn();
  const mockOnToggleHide = jest.fn();

  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup({ delay: null });
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    jest.clearAllMocks();
  });

  const renderButton = (isExpanded = false) => {
    return render(
      <ExplainButton
        trendId={mockTrendId}
        token={mockToken}
        isExpanded={isExpanded}
        onBriefGenerated={mockOnBriefGenerated}
        onError={mockOnError}
        onToggleHide={mockOnToggleHide}
      />
    );
  };

  it('should render "Explain This Trend" button initially', () => {
    renderButton();

    const button = screen.getByRole('button', { name: /explain this trend/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Explain This Trend');
  });

  it('should have sparkles icon when not expanded', () => {
    renderButton();

    const button = screen.getByRole('button');
    // Check for SVG sparkles icon path
    const svgPath = button.querySelector('svg path[d*="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16"]');
    expect(svgPath).toBeInTheDocument();
  });

  it('should have hover effect styles', () => {
    renderButton();

    const button = screen.getByRole('button');
    expect(button).toHaveClass('hover:bg-blue-100');
    expect(button).toHaveClass('bg-blue-50');
  });

  it('should call API and onBriefGenerated on click', async () => {
    (api.generateTrendBrief as jest.Mock).mockResolvedValueOnce(mockBrief);

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    expect(api.generateTrendBrief).toHaveBeenCalledWith(mockToken, mockTrendId);

    await waitFor(() => {
      expect(mockOnBriefGenerated).toHaveBeenCalledWith(mockBrief);
    });
  });

  it('should show loading state while generating', async () => {
    (api.generateTrendBrief as jest.Mock).mockImplementationOnce(
      () => new Promise(resolve => setTimeout(() => resolve(mockBrief), 100))
    );

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    // Check loading state
    expect(screen.getByText(/generating explanation/i)).toBeInTheDocument();
    expect(button).toBeDisabled();

    // Check for spinner span with aria-busy
    const loadingSpan = screen.getByText(/generating explanation/i).closest('span');
    expect(loadingSpan).toHaveAttribute('aria-busy', 'true');
    expect(loadingSpan).toHaveAttribute('aria-live', 'polite');

    await waitFor(() => {
      expect(mockOnBriefGenerated).toHaveBeenCalled();
    });
  });

  it('should disable button during loading', async () => {
    (api.generateTrendBrief as jest.Mock).mockImplementationOnce(
      () => new Promise(resolve => setTimeout(() => resolve(mockBrief), 100))
    );

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    expect(button).toBeDisabled();
    expect(button).toHaveClass('cursor-not-allowed');
  });

  it('should toggle text to "Hide Explanation" when expanded', () => {
    renderButton(true);

    const button = screen.getByRole('button', { name: /hide explanation/i });
    expect(button).toHaveTextContent('Hide Explanation');
  });

  it('should call onToggleHide when clicking expanded button', async () => {
    renderButton(true);

    const button = screen.getByRole('button');
    await user.click(button);

    expect(mockOnToggleHide).toHaveBeenCalled();
    expect(api.generateTrendBrief).not.toHaveBeenCalled();
  });

  it('should handle 503 error and call onError', async () => {
    const error = new APIError(503, 'Unable to generate explanation. Please try again later.');
    (api.generateTrendBrief as jest.Mock).mockRejectedValueOnce(error);

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('Unable to generate explanation. Please try again later.');
    });
  });

  it('should handle 404 error and call onError', async () => {
    const error = new APIError(404, 'Trend not found.');
    (api.generateTrendBrief as jest.Mock).mockRejectedValueOnce(error);

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('Trend not found.');
    });
  });

  it('should redirect to login on 401 error', async () => {
    const error = new APIError(401, 'Authentication failed. Please log in again.');
    (api.generateTrendBrief as jest.Mock).mockRejectedValueOnce(error);

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/?message=Session expired. Please log in again.');
    });

    // onError should only be called once to clear errors (with empty string)
    expect(mockOnError).toHaveBeenCalledTimes(1);
    expect(mockOnError).toHaveBeenCalledWith('');
  });

  it('should handle unexpected errors gracefully', async () => {
    const error = new Error('Network error');
    (api.generateTrendBrief as jest.Mock).mockRejectedValueOnce(error);

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith('An unexpected error occurred. Please try again.');
    });
  });

  it('should clear errors before new request', async () => {
    (api.generateTrendBrief as jest.Mock).mockResolvedValueOnce(mockBrief);

    renderButton();

    const button = screen.getByRole('button');
    await user.click(button);

    expect(mockOnError).toHaveBeenCalledWith(''); // Clear errors
    await waitFor(() => {
      expect(mockOnBriefGenerated).toHaveBeenCalled();
    });
  });

  it('should have proper aria-label and aria-expanded attributes', () => {
    const { rerender } = renderButton(false);

    let button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Explain this trend');
    expect(button).toHaveAttribute('aria-expanded', 'false');

    rerender(
      <ExplainButton
        trendId={mockTrendId}
        token={mockToken}
        isExpanded={true}
        onBriefGenerated={mockOnBriefGenerated}
        onError={mockOnError}
        onToggleHide={mockOnToggleHide}
      />
    );

    button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', 'Hide explanation');
    expect(button).toHaveAttribute('aria-expanded', 'true');
  });

  it('should have focus ring styles for accessibility', () => {
    renderButton();

    const button = screen.getByRole('button');
    expect(button).toHaveClass('focus:ring-2');
    expect(button).toHaveClass('focus:ring-blue-500');
  });
});
