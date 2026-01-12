import React from 'react';
import { render, screen } from '@testing-library/react';
import { ConfidenceBadge } from '@/components/ConfidenceBadge';

describe('ConfidenceBadge Component', () => {
  describe('High confidence badge', () => {
    it('renders with fire emoji and HIGH text', () => {
      render(<ConfidenceBadge level="high" />);

      const badge = screen.getByText(/HIGH/i);
      expect(badge).toBeInTheDocument();

      // Check for fire emoji
      expect(badge.textContent).toContain('🔥');
    });

    it('applies correct CSS classes for high confidence', () => {
      const { container } = render(<ConfidenceBadge level="high" />);
      const span = container.querySelector('span');

      expect(span).toHaveClass('bg-red-100');
      expect(span).toHaveClass('text-red-800');
      expect(span).toHaveClass('border-red-300');
    });

    it('displays correct tooltip for high confidence', () => {
      const { container } = render(<ConfidenceBadge level="high" />);
      const span = container.querySelector('span');

      expect(span).toHaveAttribute('title', 'High confidence - All 4 signals aligned');
    });
  });

  describe('Medium confidence badge', () => {
    it('renders with lightning emoji and MEDIUM text', () => {
      render(<ConfidenceBadge level="medium" />);

      const badge = screen.getByText(/MEDIUM/i);
      expect(badge).toBeInTheDocument();

      // Check for lightning emoji
      expect(badge.textContent).toContain('⚡');
    });

    it('applies correct CSS classes for medium confidence', () => {
      const { container } = render(<ConfidenceBadge level="medium" />);
      const span = container.querySelector('span');

      expect(span).toHaveClass('bg-yellow-100');
      expect(span).toHaveClass('text-yellow-800');
      expect(span).toHaveClass('border-yellow-300');
    });

    it('displays correct tooltip for medium confidence', () => {
      const { container } = render(<ConfidenceBadge level="medium" />);
      const span = container.querySelector('span');

      expect(span).toHaveAttribute('title', 'Medium confidence - 2-3 signals present');
    });
  });

  describe('Low confidence badge', () => {
    it('renders with eyes emoji and LOW text', () => {
      render(<ConfidenceBadge level="low" />);

      const badge = screen.getByText(/LOW/i);
      expect(badge).toBeInTheDocument();

      // Check for eyes emoji
      expect(badge.textContent).toContain('👀');
    });

    it('applies correct CSS classes for low confidence', () => {
      const { container } = render(<ConfidenceBadge level="low" />);
      const span = container.querySelector('span');

      expect(span).toHaveClass('bg-blue-100');
      expect(span).toHaveClass('text-blue-800');
      expect(span).toHaveClass('border-blue-300');
    });

    it('displays correct tooltip for low confidence', () => {
      const { container } = render(<ConfidenceBadge level="low" />);
      const span = container.querySelector('span');

      expect(span).toHaveAttribute('title', 'Low confidence - 1 signal present');
    });
  });
});
