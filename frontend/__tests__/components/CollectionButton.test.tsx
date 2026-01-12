import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CollectionButton } from '@/components/CollectionButton';
import { ToastProvider } from '@/components/Toast';
import { api, APIError } from '@/lib/api';
import { useRouter } from 'next/navigation';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock API client
jest.mock('@/lib/api', () => ({
  api: {
    triggerCollection: jest.fn(),
    getCollectionStatus: jest.fn(),
  },
  APIError: class APIError extends Error {
    constructor(public status: number, message: string) {
      super(message);
      this.name = 'APIError';
    }
  },
}));

const mockRouter = {
  refresh: jest.fn(),
  push: jest.fn(),
  back: jest.fn(),
  forward: jest.fn(),
  prefetch: jest.fn(),
  replace: jest.fn(),
};

describe('CollectionButton Component', () => {
  const mockToken = 'test-jwt-token';
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup({ delay: null });
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    jest.clearAllMocks();
  });

  const renderButton = () => {
    return render(
      <ToastProvider>
        <CollectionButton token={mockToken} />
      </ToastProvider>
    );
  };

  it('renders idle state with "Collect Latest Trends" text', () => {
    renderButton();
    expect(screen.getByText('Collect Latest Trends')).toBeInTheDocument();
  });

  it('triggers POST /collect API call when clicked', async () => {
    (api.triggerCollection as jest.Mock).mockResolvedValue({
      collection_id: 'test-collection-id',
      status: 'in_progress',
      started_at: '2026-01-12T10:00:00Z',
      message: 'Collection started',
    });

    renderButton();

    const button = screen.getByText('Collect Latest Trends');
    await user.click(button);

    await waitFor(() => {
      expect(api.triggerCollection).toHaveBeenCalledWith(mockToken);
    });
  });

  it('shows loading state with "Collecting..." and spinner', async () => {
    (api.triggerCollection as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({
        collection_id: 'test-collection-id',
        status: 'in_progress',
        started_at: '2026-01-12T10:00:00Z',
        message: 'Collection started',
      }), 100))
    );

    renderButton();

    const button = screen.getByText('Collect Latest Trends');
    await user.click(button);

    // Check loading state appears
    await waitFor(() => {
      expect(screen.getByText('Collecting...')).toBeInTheDocument();
    });

    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('disables button during collection', async () => {
    (api.triggerCollection as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({
        collection_id: 'test-collection-id',
        status: 'in_progress',
        started_at: '2026-01-12T10:00:00Z',
        message: 'Collection started',
      }), 100))
    );

    renderButton();

    const button = screen.getByText('Collect Latest Trends');
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByText('Collecting...')).toBeDisabled();
    });
  });

  it('handles 409 Conflict error', async () => {
    (api.triggerCollection as jest.Mock).mockRejectedValue(
      new APIError(409, 'Collection already in progress. Please wait.')
    );

    renderButton();

    const button = screen.getByText('Collect Latest Trends');
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Collection already in progress/)).toBeInTheDocument();
    });
  });

  it('has proper ARIA attributes for accessibility', () => {
    renderButton();

    const button = screen.getByLabelText('Collect latest trends');
    expect(button).toHaveAttribute('aria-busy', 'false');
  });

  it('sets aria-busy to true during collection', async () => {
    (api.triggerCollection as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({
        collection_id: 'test-collection-id',
        status: 'in_progress',
        started_at: '2026-01-12T10:00:00Z',
        message: 'Collection started',
      }), 100))
    );

    renderButton();

    const button = screen.getByText('Collect Latest Trends');
    await user.click(button);

    await waitFor(() => {
      expect(screen.getByLabelText('Collection in progress')).toHaveAttribute('aria-busy', 'true');
    });
  });
});
