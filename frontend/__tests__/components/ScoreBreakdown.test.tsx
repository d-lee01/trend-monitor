import React from 'react';
import { render, screen } from '@testing-library/react';
import { ScoreBreakdown } from '@/components/ScoreBreakdown';

describe('ScoreBreakdown Component', () => {
  it('renders component with all scores', () => {
    render(
      <ScoreBreakdown
        redditVelocity={78}
        youtubeTraction={82}
        googleTrendsSpike={85}
        similarwebBonus={true}
        finalScore={87.5}
      />
    );

    expect(screen.getByText('Momentum Score Calculation')).toBeInTheDocument();
    expect(screen.getByText('78.0')).toBeInTheDocument();
    expect(screen.getByText('82.0')).toBeInTheDocument();
    expect(screen.getByText('85.0')).toBeInTheDocument();
    expect(screen.getByText('87.5')).toBeInTheDocument();
  });

  it('displays component scores with correct platform labels', () => {
    render(
      <ScoreBreakdown
        redditVelocity={70}
        youtubeTraction={80}
        googleTrendsSpike={90}
        similarwebBonus={false}
        finalScore={80}
      />
    );

    expect(screen.getByText(/Reddit:/i)).toBeInTheDocument();
    expect(screen.getByText(/YouTube:/i)).toBeInTheDocument();
    expect(screen.getByText(/Google:/i)).toBeInTheDocument();
  });

  it('displays base score calculation formula', () => {
    render(
      <ScoreBreakdown
        redditVelocity={60}
        youtubeTraction={70}
        googleTrendsSpike={80}
        similarwebBonus={false}
        finalScore={70}
      />
    );

    expect(screen.getByText(/Base Score Formula:/i)).toBeInTheDocument();
    expect(screen.getByText(/× 0.33/)).toBeInTheDocument();
    expect(screen.getByText(/× 0.34/)).toBeInTheDocument();
  });

  it('displays SimilarWeb bonus when applied', () => {
    render(
      <ScoreBreakdown
        redditVelocity={60}
        youtubeTraction={70}
        googleTrendsSpike={80}
        similarwebBonus={true}
        finalScore={105}
      />
    );

    expect(screen.getByText(/SimilarWeb Bonus Applied!/i)).toBeInTheDocument();
    expect(screen.getByText(/× 1.5 \(bonus multiplier\)/i)).toBeInTheDocument();
  });

  it('does not display SimilarWeb bonus when not applied', () => {
    render(
      <ScoreBreakdown
        redditVelocity={60}
        youtubeTraction={70}
        googleTrendsSpike={80}
        similarwebBonus={false}
        finalScore={70}
      />
    );

    expect(screen.queryByText(/SimilarWeb Bonus Applied!/i)).not.toBeInTheDocument();
    expect(screen.getByText(/No SimilarWeb bonus - traffic spike not detected/i)).toBeInTheDocument();
  });

  it('handles null values by displaying N/A', () => {
    render(
      <ScoreBreakdown
        redditVelocity={null}
        youtubeTraction={80}
        googleTrendsSpike={null}
        similarwebBonus={false}
        finalScore={80}
      />
    );

    const naElements = screen.getAllByText('N/A');
    expect(naElements.length).toBeGreaterThan(0);
  });

  it('calculates base score correctly', () => {
    render(
      <ScoreBreakdown
        redditVelocity={60}
        youtubeTraction={70}
        googleTrendsSpike={80}
        similarwebBonus={false}
        finalScore={70}
      />
    );

    // Base score = (60 * 0.33 + 70 * 0.33 + 80 * 0.34) = 70.1
    expect(screen.getByText('70.1')).toBeInTheDocument();
  });

  it('formats scores to 1 decimal place', () => {
    render(
      <ScoreBreakdown
        redditVelocity={78.456}
        youtubeTraction={82.123}
        googleTrendsSpike={85.789}
        similarwebBonus={false}
        finalScore={82.123}
      />
    );

    // Check that formatted scores appear in the document (may appear multiple times)
    expect(screen.getAllByText('78.5').length).toBeGreaterThan(0);
    expect(screen.getAllByText('82.1').length).toBeGreaterThan(0);
    expect(screen.getAllByText('85.8').length).toBeGreaterThan(0);
  });

  it('displays final score prominently', () => {
    render(
      <ScoreBreakdown
        redditVelocity={80}
        youtubeTraction={85}
        googleTrendsSpike={90}
        similarwebBonus={true}
        finalScore={128.5}
      />
    );

    expect(screen.getByText('Final Momentum Score:')).toBeInTheDocument();
    expect(screen.getByText('128.5')).toBeInTheDocument();
  });

  it('includes explanatory note', () => {
    render(
      <ScoreBreakdown
        redditVelocity={70}
        youtubeTraction={75}
        googleTrendsSpike={80}
        similarwebBonus={false}
        finalScore={75}
      />
    );

    expect(screen.getByText(/weighted average of platform-specific scores/i)).toBeInTheDocument();
  });
});
