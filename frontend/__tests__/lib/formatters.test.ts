import { formatNumber, formatPercent, timeAgo } from '@/lib/formatters';

describe('Formatter Utilities', () => {
  describe('formatNumber', () => {
    it('formats numbers in thousands with K notation', () => {
      expect(formatNumber(15234)).toBe('15.2K');
      expect(formatNumber(1000)).toBe('1.0K');
      expect(formatNumber(9999)).toBe('10.0K');
    });

    it('formats numbers in millions with M notation', () => {
      expect(formatNumber(2534000)).toBe('2.5M');
      expect(formatNumber(1000000)).toBe('1.0M');
      expect(formatNumber(15000000)).toBe('15.0M');
    });

    it('returns number as string for values under 1000', () => {
      expect(formatNumber(999)).toBe('999');
      expect(formatNumber(100)).toBe('100');
      expect(formatNumber(0)).toBe('0');
    });

    it('returns "N/A" for null values', () => {
      expect(formatNumber(null)).toBe('N/A');
    });
  });

  describe('formatPercent', () => {
    it('formats positive percentages with + sign', () => {
      expect(formatPercent(150.5)).toBe('+151%'); // Rounds 150.5 to 151
      expect(formatPercent(25.9)).toBe('+26%'); // Rounds 25.9 to 26
      expect(formatPercent(0)).toBe('+0%');
    });

    it('formats negative percentages with - sign', () => {
      expect(formatPercent(-25.3)).toBe('-25%');
      expect(formatPercent(-150)).toBe('-150%');
    });

    it('rounds to nearest integer', () => {
      expect(formatPercent(150.7)).toBe('+151%');
      expect(formatPercent(150.3)).toBe('+150%');
    });

    it('returns "N/A" for null values', () => {
      expect(formatPercent(null)).toBe('N/A');
    });
  });

  describe('timeAgo', () => {
    beforeEach(() => {
      // Mock current time to 2026-01-12T12:00:00Z for consistent testing
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2026-01-12T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('formats minutes ago correctly', () => {
      const thirtyMinsAgo = '2026-01-12T11:30:00Z';
      expect(timeAgo(thirtyMinsAgo)).toBe('30m ago');

      const fiveMinsAgo = '2026-01-12T11:55:00Z';
      expect(timeAgo(fiveMinsAgo)).toBe('5m ago');
    });

    it('formats hours ago correctly', () => {
      const twoHoursAgo = '2026-01-12T10:00:00Z';
      expect(timeAgo(twoHoursAgo)).toBe('2h ago');

      const fiveHoursAgo = '2026-01-12T07:00:00Z';
      expect(timeAgo(fiveHoursAgo)).toBe('5h ago');
    });

    it('formats days ago correctly', () => {
      const threeDaysAgo = '2026-01-09T12:00:00Z';
      expect(timeAgo(threeDaysAgo)).toBe('3d ago');

      const oneDayAgo = '2026-01-11T12:00:00Z';
      expect(timeAgo(oneDayAgo)).toBe('1d ago');
    });

    it('handles edge case at 60 minutes boundary', () => {
      const sixtyMinsAgo = '2026-01-12T11:00:00Z';
      expect(timeAgo(sixtyMinsAgo)).toBe('1h ago');
    });

    it('handles edge case at 24 hours boundary', () => {
      const twentyFourHoursAgo = '2026-01-11T12:00:00Z';
      expect(timeAgo(twentyFourHoursAgo)).toBe('1d ago');
    });
  });
});
