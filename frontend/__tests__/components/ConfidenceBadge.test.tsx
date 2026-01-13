import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConfidenceBadge } from '@/components/ConfidenceBadge';

describe('ConfidenceBadge Component', () => {
  it('renders high confidence badge with fire emoji', () => {
    render(<ConfidenceBadge confidenceLevel="high" />);

    expect(screen.getByRole('img', { name: /confidence level: high/i })).toBeInTheDocument();
    expect(screen.getByText('🔥')).toBeInTheDocument();
  });

  it('renders medium confidence badge with lightning emoji', () => {
    render(<ConfidenceBadge confidenceLevel="medium" />);

    expect(screen.getByRole('img', { name: /confidence level: medium/i })).toBeInTheDocument();
    expect(screen.getByText('⚡')).toBeInTheDocument();
  });

  it('renders low confidence badge with eyes emoji', () => {
    render(<ConfidenceBadge confidenceLevel="low" />);

    expect(screen.getByRole('img', { name: /confidence level: low/i })).toBeInTheDocument();
    expect(screen.getByText('👀')).toBeInTheDocument();
  });

  it('displays tooltip on hover - high confidence', async () => {
    const user = userEvent.setup({ delay: null });
    render(<ConfidenceBadge confidenceLevel="high" />);

    const badge = screen.getByText('🔥');

    // Tooltip should not be visible initially
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();

    // Hover over badge
    await user.hover(badge);

    // Tooltip should be visible with correct text
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText('High Confidence: All 4 platform signals aligned')).toBeInTheDocument();
  });

  it('displays tooltip on hover - medium confidence', async () => {
    const user = userEvent.setup({ delay: null });
    render(<ConfidenceBadge confidenceLevel="medium" />);

    const badge = screen.getByText('⚡');
    await user.hover(badge);

    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText('Medium: 2-3 signals')).toBeInTheDocument();
  });

  it('displays tooltip on hover - low confidence', async () => {
    const user = userEvent.setup({ delay: null });
    render(<ConfidenceBadge confidenceLevel="low" />);

    const badge = screen.getByText('👀');
    await user.hover(badge);

    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText('Low: 1 signal')).toBeInTheDocument();
  });

  it('hides tooltip on unhover', async () => {
    const user = userEvent.setup({ delay: null });
    render(<ConfidenceBadge confidenceLevel="high" />);

    const badge = screen.getByText('🔥');

    await user.hover(badge);
    expect(screen.getByRole('tooltip')).toBeInTheDocument();

    await user.unhover(badge);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('renders small size by default', () => {
    render(<ConfidenceBadge confidenceLevel="high" />);

    const badge = screen.getByText('🔥');
    expect(badge).toHaveClass('text-2xl');
  });

  it('renders large size when specified', () => {
    render(<ConfidenceBadge confidenceLevel="high" size="large" />);

    const badge = screen.getByText('🔥');
    expect(badge).toHaveClass('text-4xl');
  });

  it('applies correct color class for high confidence', () => {
    render(<ConfidenceBadge confidenceLevel="high" />);

    const badge = screen.getByText('🔥');
    expect(badge).toHaveClass('text-orange-500');
  });

  it('applies correct color class for medium confidence', () => {
    render(<ConfidenceBadge confidenceLevel="medium" />);

    const badge = screen.getByText('⚡');
    expect(badge).toHaveClass('text-amber-500');
  });

  it('applies correct color class for low confidence', () => {
    render(<ConfidenceBadge confidenceLevel="low" />);

    const badge = screen.getByText('👀');
    expect(badge).toHaveClass('text-gray-500');
  });

  it('has cursor-help class for accessibility', () => {
    render(<ConfidenceBadge confidenceLevel="high" />);

    const badge = screen.getByText('🔥');
    expect(badge).toHaveClass('cursor-help');
  });
});
