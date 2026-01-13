/**
 * Loading UI for Trend Detail Page
 * Displayed during SSR while fetching trend data
 */

export default function TrendDetailLoading() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Skeleton */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="h-6 w-40 bg-gray-200 rounded animate-pulse"></div>
        </div>
      </header>

      {/* Main Content Skeleton */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Title and Badge Skeleton */}
        <div className="flex items-center gap-4 mb-8">
          <div className="h-8 w-96 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-8 w-20 bg-gray-200 rounded-full animate-pulse"></div>
        </div>

        {/* Platform Breakdown Section */}
        <section className="mb-8">
          <div className="h-7 w-48 bg-gray-200 rounded mb-4 animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 4 Platform Card Skeletons */}
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm animate-pulse"
              >
                <div className="h-6 w-32 bg-gray-200 rounded mb-3"></div>
                <div className="h-8 w-24 bg-gray-200 rounded mb-3"></div>
                <div className="h-2.5 w-full bg-gray-200 rounded-full mb-3"></div>
                <div className="space-y-2">
                  <div className="h-4 w-full bg-gray-200 rounded"></div>
                  <div className="h-4 w-3/4 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Score Breakdown Section */}
        <section>
          <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm animate-pulse">
            <div className="h-6 w-64 bg-gray-200 rounded mb-4"></div>
            <div className="space-y-3">
              <div className="h-4 w-full bg-gray-200 rounded"></div>
              <div className="h-4 w-5/6 bg-gray-200 rounded"></div>
              <div className="h-4 w-4/6 bg-gray-200 rounded"></div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
