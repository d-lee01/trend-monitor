import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToastProvider } from '@/components/Toast';
import { useToast } from '@/lib/toast';

// Test component that uses toast
function TestComponent() {
  const { showToast } = useToast();

  return (
    <div>
      <button
        onClick={() => showToast({ type: 'success', message: 'Success message' })}
        data-testid="success-button"
      >
        Show Success
      </button>
      <button
        onClick={() => showToast({ type: 'error', message: 'Error message' })}
        data-testid="error-button"
      >
        Show Error
      </button>
      <button
        onClick={() => showToast({ type: 'warning', message: 'Warning message' })}
        data-testid="warning-button"
      >
        Show Warning
      </button>
    </div>
  );
}

describe('Toast Component', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    jest.useFakeTimers();
    user = userEvent.setup({ delay: null });
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('renders toast with success type and message', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const successButton = screen.getByTestId('success-button');
    await user.click(successButton);

    expect(screen.getByText('Success message')).toBeInTheDocument();
    expect(screen.getByText('✓')).toBeInTheDocument();
  });

  it('renders toast with error type and message', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const errorButton = screen.getByTestId('error-button');
    await user.click(errorButton);

    expect(screen.getByText('Error message')).toBeInTheDocument();
    expect(screen.getByText('⚠')).toBeInTheDocument();
  });

  it('renders toast with warning type and message', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const warningButton = screen.getByTestId('warning-button');
    await user.click(warningButton);

    expect(screen.getByText('Warning message')).toBeInTheDocument();
    expect(screen.getByText('⚠')).toBeInTheDocument();
  });

  it('auto-dismisses toast after 5 seconds', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const successButton = screen.getByTestId('success-button');
    await user.click(successButton);

    expect(screen.getByText('Success message')).toBeInTheDocument();

    // Fast-forward 5 seconds
    act(() => {
      jest.advanceTimersByTime(5000);
    });

    await waitFor(() => {
      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
    });
  });

  it('allows manual close via close button', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const successButton = screen.getByTestId('success-button');
    await user.click(successButton);

    expect(screen.getByText('Success message')).toBeInTheDocument();

    // Click close button
    const closeButton = screen.getByLabelText('Close notification');
    await user.click(closeButton);

    // Wait for exit animation (300ms)
    act(() => {
      jest.advanceTimersByTime(300);
    });

    await waitFor(() => {
      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
    });
  });

  it('displays multiple toasts stacked correctly', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    // Show multiple toasts
    const successButton = screen.getByTestId('success-button');
    const errorButton = screen.getByTestId('error-button');
    const warningButton = screen.getByTestId('warning-button');

    await user.click(successButton);
    await user.click(errorButton);
    await user.click(warningButton);

    // All three should be visible
    expect(screen.getByText('Success message')).toBeInTheDocument();
    expect(screen.getByText('Error message')).toBeInTheDocument();
    expect(screen.getByText('Warning message')).toBeInTheDocument();
  });

  it('has proper ARIA attributes for accessibility', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const successButton = screen.getByTestId('success-button');
    await user.click(successButton);

    const toastContainer = screen.getByRole('alert');
    expect(toastContainer).toHaveAttribute('role', 'alert');

    // Container should have aria-live
    const liveRegion = toastContainer.parentElement;
    expect(liveRegion).toHaveAttribute('aria-live', 'polite');
  });
});
