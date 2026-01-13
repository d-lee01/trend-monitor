/**
 * Score Breakdown Component
 * Displays the momentum score calculation formula in a clear, readable format
 */

interface ScoreBreakdownProps {
  redditVelocity: number | null;
  youtubeTraction: number | null;
  googleTrendsSpike: number | null;
  similarwebBonus: boolean;
  finalScore: number;
}

export function ScoreBreakdown({
  redditVelocity,
  youtubeTraction,
  googleTrendsSpike,
  similarwebBonus,
  finalScore,
}: ScoreBreakdownProps) {
  // Calculate base score (weighted average before bonus)
  const calculateBaseScore = () => {
    const reddit = redditVelocity ?? 0;
    const youtube = youtubeTraction ?? 0;
    const google = googleTrendsSpike ?? 0;

    return (reddit * 0.33 + youtube * 0.33 + google * 0.34);
  };

  const baseScore = calculateBaseScore();

  // Format number to 1 decimal place
  const formatScore = (score: number | null): string => {
    if (score === null) return 'N/A';
    return score.toFixed(1);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Momentum Score Calculation</h3>

      {/* Formula Breakdown */}
      <div className="space-y-4">
        {/* Component Scores */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600 mb-2 font-medium">Component Scores (0-100 scale):</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="flex items-center gap-2">
              <span className="text-orange-600 font-semibold">🔴 Reddit:</span>
              <span className="font-mono text-lg font-bold text-gray-900">
                {formatScore(redditVelocity)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-red-600 font-semibold">▶️ YouTube:</span>
              <span className="font-mono text-lg font-bold text-gray-900">
                {formatScore(youtubeTraction)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-600 font-semibold">📈 Google:</span>
              <span className="font-mono text-lg font-bold text-gray-900">
                {formatScore(googleTrendsSpike)}
              </span>
            </div>
          </div>
        </div>

        {/* Base Score Calculation */}
        <div className="border-l-4 border-blue-500 pl-4">
          <p className="text-sm text-gray-600 mb-1">Base Score Formula:</p>
          <p className="text-gray-800 leading-relaxed">
            <span className="text-orange-600 font-semibold">Reddit</span>{' '}
            <span className="font-mono font-bold">({formatScore(redditVelocity)})</span> × 0.33 +{' '}
            <span className="text-red-600 font-semibold">YouTube</span>{' '}
            <span className="font-mono font-bold">({formatScore(youtubeTraction)})</span> × 0.33 +{' '}
            <span className="text-blue-600 font-semibold">Google</span>{' '}
            <span className="font-mono font-bold">({formatScore(googleTrendsSpike)})</span> × 0.34
          </p>
          <p className="text-sm text-gray-600 mt-2">
            = Base Score: <span className="font-mono font-bold text-gray-900">{formatScore(baseScore)}</span>
          </p>
        </div>

        {/* SimilarWeb Bonus */}
        {similarwebBonus && (
          <div className="border-l-4 border-purple-500 pl-4 bg-purple-50 p-3 rounded-r-lg">
            <p className="text-sm text-purple-700 font-medium mb-1">
              📊 SimilarWeb Bonus Applied!
            </p>
            <p className="text-gray-800">
              Base Score <span className="font-mono font-bold">({formatScore(baseScore)})</span> × 1.5 (bonus multiplier)
            </p>
          </div>
        )}

        {/* Final Score */}
        <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-4">
          <p className="text-sm opacity-90 mb-1">Final Momentum Score:</p>
          <p className="text-4xl font-mono font-bold">
            {formatScore(finalScore)}
          </p>
          {!similarwebBonus && (
            <p className="text-sm opacity-75 mt-2">
              (No SimilarWeb bonus - traffic spike not detected)
            </p>
          )}
        </div>
      </div>

      {/* Explanation */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 leading-relaxed">
          <strong>Note:</strong> The momentum score is calculated as a weighted average of platform-specific
          scores (Reddit velocity, YouTube traction, Google Trends spike). When SimilarWeb detects a traffic
          spike, a 1.5× bonus multiplier is applied to amplify trending signals.
        </p>
      </div>
    </div>
  );
}
